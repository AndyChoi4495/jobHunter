# Notion REST API로 Job ID를 조회하고 새 공고 페이지를 추가하는 저장소
# Store that reads Job IDs and adds new posting pages via the Notion REST API
from __future__ import annotations

import time
from typing import Any, Dict, List, Set

import requests

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MIN_INTERVAL = 0.35  # seconds between requests, ~3 req/s
TIMEOUT = 30
TEXT_LIMIT = 2000  # Notion rich_text content limit

TRACK_LABELS = {"intern": "Intern", "new_grad": "New Grad"}
SOURCE_LABELS = {
    "simplify": "Simplify",
    "canada_internship": "CanadaInternship",
    "jsearch": "JSearch",
}


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": "Bearer " + token,
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _post(token: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST with throttling and a single retry on HTTP 429."""
    for attempt in range(2):
        time.sleep(MIN_INTERVAL)
        resp = requests.post(
            API + path, headers=_headers(token), json=body, timeout=TIMEOUT
        )
        if resp.status_code == 429 and attempt == 0:
            time.sleep(float(resp.headers.get("Retry-After", "1")))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("unreachable")


def _text(value: str) -> List[Dict[str, Any]]:
    return [{"text": {"content": value[:TEXT_LIMIT]}}]


def existing_job_ids(token: str, db_id: str) -> Set[str]:
    ids: Set[str] = set()
    cursor = None
    while True:
        body: Dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = _post(token, "/databases/%s/query" % db_id, body)
        for page in data.get("results", []):
            rich = page.get("properties", {}).get("Job ID", {}).get("rich_text", [])
            if rich:
                ids.add(rich[0].get("plain_text", ""))
        if not data.get("has_more"):
            return ids
        cursor = data.get("next_cursor")


def _properties(job: Any) -> Dict[str, Any]:
    props: Dict[str, Any] = {
        "Title": {"title": _text(job.title)},
        "Company": {"rich_text": _text(job.company)},
        "Location": {"rich_text": _text(job.location)},
        "Remote": {"checkbox": job.remote},
        "Track": {"select": {"name": TRACK_LABELS[job.track.value]}},
        "Source": {"select": {"name": SOURCE_LABELS[job.source.value]}},
        "Link": {"url": job.url},
        "Job ID": {"rich_text": _text(job.job_id)},
        "Collected": {"date": {"start": job.collected.isoformat()}},
    }
    if job.category:
        props["Category"] = {"select": {"name": job.category.replace(",", " ")}}
    if job.posted:
        props["Posted"] = {"date": {"start": job.posted.isoformat()}}
    return props


def add_jobs(token: str, db_id: str, jobs: List[Any]) -> None:
    for job in jobs:
        _post(
            token,
            "/pages",
            {"parent": {"database_id": db_id}, "properties": _properties(job)},
        )
