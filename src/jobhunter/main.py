# 수집 → 필터 → 중복 제거 → Notion → Discord → 공개 보드를 잇는 진입점
# Entry point wiring collect → filter → dedupe → Notion → Discord → public board
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List

from jobhunter import board, notify_discord, notion_store
from jobhunter.config import load_config
from jobhunter.dedupe import dedupe
from jobhunter.filter import filter_jobs
from jobhunter.models import Job
from jobhunter.sources import canada_internship, jsearch, simplify

log = logging.getLogger("jobhunter")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    dry_run = os.environ.get("DRY_RUN") == "1"
    cfg = load_config()
    regions = cfg.enabled_regions()

    # Fail loudly on missing secrets before doing any work.
    secrets: Dict[str, Dict[str, str]] = {}
    token = os.environ.get("NOTION_TOKEN", "")
    if not dry_run:
        missing = [] if token else ["NOTION_TOKEN"]
        for r in regions:
            for env in (r.notion_db_env, r.discord_webhook_env):
                if not os.environ.get(env):
                    missing.append(env)
        if missing:
            log.error("Missing required env vars: %s", ", ".join(missing))
            return 1
    for r in regions:
        secrets[r.name] = {
            "db": os.environ.get(r.notion_db_env, ""),
            "hook": os.environ.get(r.discord_webhook_env, ""),
        }

    failed = False
    warn_hook = next((s["hook"] for s in secrets.values() if s["hook"]), "")

    def warn(message: str) -> None:
        log.warning(message)
        if warn_hook and not dry_run:
            try:
                notify_discord.send_warning(warn_hook, message)
            except Exception:
                log.exception("Could not send Discord warning")

    # Fetch each source once; regions share the results.
    raw: Dict[str, List[Job]] = {}
    fetchers = []
    if cfg.sources.simplify.enabled:
        fetchers.append(("simplify", lambda: simplify.fetch(cfg.sources.simplify)))
    if cfg.sources.canada_internship.enabled and any(
        r.country == "ca" for r in regions
    ):
        fetchers.append(("canada_internship", canada_internship.fetch))
    for name, fetch in fetchers:
        try:
            raw[name] = fetch()
        except Exception:
            log.exception("Fetching %s failed", name)
            raw[name] = []
            failed = True
            warn("Source %s failed to fetch (see Actions log)." % name)
            continue
        log.info("%s: %d rows", name, len(raw[name]))
        if not raw[name]:
            warn("Source %s returned 0 rows; the format may have changed." % name)

    # JSearch is optional and quota-limited: run only at its scheduled hour, never in a
    # dry run, and treat failures as warnings (its postings never reach the board anyway).
    js = cfg.sources.jsearch
    if js.enabled and not dry_run and jsearch.should_run(datetime.now(timezone.utc), js.run_hour):
        key = os.environ.get("JSEARCH_API_KEY", "")
        rows: List[Job] = []
        try:
            if not key:
                raise RuntimeError("JSEARCH_API_KEY is not set")
            for country in sorted({r.country for r in regions}):
                rows.extend(jsearch.fetch(cfg.tracks, country, key))
            log.info("jsearch: %d rows", len(rows))
        except Exception:
            log.exception("Fetching jsearch failed")
            warn("Source jsearch failed (quota or API change?); continuing without it.")
        raw["jsearch"] = rows  # last, so dedupe keeps the other sources' copies

    all_jobs = [j for rows in raw.values() for j in rows]
    published: List[Job] = []
    for r in regions:
        jobs = dedupe(filter_jobs(
            all_jobs, r, cfg.exclude_title_keywords, cfg.include_title_keywords
        ))
        if r.publish:
            published.extend(jobs)
        if dry_run:
            print("[dry-run] %s: %d postings after filter/dedupe" % (r.name, len(jobs)))
            continue
        s = secrets[r.name]
        try:
            known = notion_store.existing_job_ids(token, s["db"])
            new = [j for j in jobs if j.job_id not in known]
            notion_store.add_jobs(token, s["db"], new)
            log.info("%s: %d new of %d", r.name, len(new), len(jobs))
            if r.notify and new:
                notify_discord.send_summary(s["hook"], r.name, new)
        except Exception:
            log.exception("Region %s failed", r.name)
            failed = True

    previous: List[dict] = []
    try:
        previous = board.fetch_previous(cfg.board_url)
    except Exception:
        log.exception("Reading the live board failed")
        warn("Could not read the live board; JSearch postings from earlier runs drop off "
             "until the next JSearch run.")
    board.build_board(dedupe(published), previous=previous)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
