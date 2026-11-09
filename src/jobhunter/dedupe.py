# URL 정규화와 중복 공고 병합
# URL normalization and merging of duplicate postings
from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jobhunter.models import Job

_TRACKING_PARAMS = {"ref", "source", "embed", "gh_src", "lever-source", "src"}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(query), ""))


def _name_key(job: Job) -> Tuple[str, str, str]:
    return (job.company.strip().lower(), job.title.strip().lower(), job.country)


def dedupe(jobs: List[Job]) -> List[Job]:
    """Merge by job_id or (company, title, country). First occurrence wins and
    gets empty fields filled from later duplicates, so pass Simplify first."""
    result: List[Job] = []
    by_id: Dict[str, int] = {}
    by_name: Dict[Tuple[str, str, str], int] = {}
    for job in jobs:
        idx = by_id.get(job.job_id)
        if idx is None:
            idx = by_name.get(_name_key(job))
        if idx is None:
            by_id[job.job_id] = by_name[_name_key(job)] = len(result)
            result.append(job)
            continue
        kept = result[idx]
        fill = {}
        if kept.posted is None and job.posted is not None:
            fill["posted"] = job.posted
        if not kept.category and job.category:
            fill["category"] = job.category
        if not kept.location and job.location:
            fill["location"] = job.location
        if fill:
            result[idx] = replace(kept, **fill)
        by_id.setdefault(job.job_id, idx)
    return result
