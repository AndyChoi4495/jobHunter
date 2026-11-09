# 공개 채용 보드용 site/jobs.json을 공개 필드만으로 생성하는 모듈
# Module that builds site/jobs.json for the public job board from public fields only
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Union

from jobhunter.models import Job, Source, Track

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


def build_board(jobs: List[Job], out_path: Union[str, Path] = "site/jobs.json") -> None:
    # JSearch is paid third-party data, so it is never republished.
    jobs = [j for j in jobs if j.source is not Source.JSEARCH]
    # Newest posted first; undated postings go last.
    ordered = sorted(jobs, key=lambda j: j.posted.toordinal() if j.posted else 0, reverse=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "jobs": [_public(j) for j in ordered],
    }
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
