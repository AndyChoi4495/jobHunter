# 공개 채용 보드용 site/jobs.json을 공개 필드만으로 생성하는 모듈
# Module that builds site/jobs.json for the public job board from public fields only
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Sequence, Union

import requests

from jobhunter.dedupe import normalize_url
from jobhunter.models import Job, Source, Track

# JSearch only runs at weekday noon, so the board carries its postings over from the
# live board between runs until they are this old (by posted date).
JSEARCH_KEEP_DAYS = 14

TRACK_LABELS = {Track.INTERN: "Intern", Track.NEW_GRAD: "New Grad"}
SOURCE_LABELS = {
    Source.SIMPLIFY: "Simplify",
    Source.CANADA_INTERNSHIP: "CanadaInternship",
    Source.JSEARCH: "JSearch",
}


def _public(job: Job) -> Dict[str, object]:
    return {
        "company": job.company,
        "title": job.title,
        "location": job.location,
        "track": TRACK_LABELS[job.track],
        "posted": job.posted.isoformat() if job.posted else None,
        "source": SOURCE_LABELS[job.source],
        "url": job.url,
        "remote": job.remote,
        "category": job.category,
    }


def fetch_previous(board_url: str) -> List[Dict[str, object]]:
    """The live board's postings; raises if it can't be read."""
    resp = requests.get(board_url.rstrip("/") + "/jobs.json", timeout=30)
    resp.raise_for_status()
    return list(resp.json()["jobs"])


def _carried_jsearch(
    previous: List[Dict[str, object]], current: List[Dict[str, object]], today: date
) -> List[Dict[str, object]]:
    """Previous JSearch entries still within the window and not already on the new board."""
    cutoff = (today - timedelta(days=JSEARCH_KEEP_DAYS)).isoformat()
    urls = {normalize_url(str(e["url"])) for e in current}
    names = {(str(e["company"]).lower(), str(e["title"]).lower()) for e in current}
    kept = []
    for e in previous:
        if e.get("source") != SOURCE_LABELS[Source.JSEARCH] or not e.get("posted"):
            continue
        if str(e["posted"]) < cutoff:
            continue
        name = (str(e["company"]).lower(), str(e["title"]).lower())
        if normalize_url(str(e["url"])) in urls or name in names:
            continue
        urls.add(normalize_url(str(e["url"])))
        names.add(name)
        kept.append(e)
    return kept


def build_board(
    jobs: List[Job],
    out_path: Union[str, Path] = "site/jobs.json",
    previous: Sequence[Dict[str, object]] = (),
    today: Union[date, None] = None,
) -> None:
    entries = [_public(j) for j in jobs]
    entries += _carried_jsearch(list(previous), entries, today or date.today())
    # Newest posted first; undated postings go last (ISO dates sort as strings).
    entries.sort(key=lambda e: e["posted"] or "", reverse=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jobs": entries,
    }
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
