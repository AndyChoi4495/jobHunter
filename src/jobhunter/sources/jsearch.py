# JSearch(RapidAPI) 검색 결과를 Job으로 바꾸는 선택 수집기
# Optional collector that turns JSearch (RapidAPI) search results into Jobs
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from zoneinfo import ZoneInfo

import requests

from jobhunter.config import TrackConfig
from jobhunter.dedupe import normalize_url
from jobhunter.models import Job, Source, Track

HOST = "jsearch.p.rapidapi.com"
URL = "https://%s/search-v2" % HOST  # the old /search endpoint returns 404
DATE_POSTED = "3days"  # runs once per weekday, so Monday also covers the weekend
TIMEZONE = ZoneInfo("America/Toronto")


def should_run(now: datetime, run_hour: int) -> bool:
    """True on weekdays during run_hour, Toronto time (free quota is 200 requests/month)."""
    local = now.astimezone(TIMEZONE)
    return local.weekday() < 5 and local.hour == run_hour


def parse_results(data: dict, track: Track) -> List[Job]:
    jobs: List[Job] = []
    for r in data.get("data", {}).get("jobs", []):
        link, title = r.get("job_apply_link"), r.get("job_title")
        if not link or not title:
            continue
        ts = r.get("job_posted_at_timestamp")
        jobs.append(
            Job(
                job_id=normalize_url(link),
                title=title,
                company=r.get("employer_name") or "",
                url=link,
                track=track,
                source=Source.JSEARCH,
                country=(r.get("job_country") or "").lower(),
                location=r.get("job_location") or "",
                remote=bool(r.get("job_is_remote")),
                posted=datetime.fromtimestamp(ts, timezone.utc).date() if ts else None,
            )
        )
    return jobs


def fetch(tracks: Dict[Track, TrackConfig], country: str, api_key: str) -> List[Job]:
    """One request per query (one page each). Errors, including 429 quota, propagate."""
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": HOST}
    jobs: List[Job] = []
    for track, tc in tracks.items():
        for query in tc.queries:
            params = {"query": query, "country": country, "date_posted": DATE_POSTED}
            resp = requests.get(URL, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            jobs.extend(parse_results(resp.json(), track))
    return jobs
