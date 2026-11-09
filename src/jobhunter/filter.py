# 지역(국가)과 제외 키워드로 공고를 거르는 필터
# Filter that keeps jobs matching a region's country and drops excluded title keywords
from __future__ import annotations

import re
from typing import List

from jobhunter.config import RegionConfig
from jobhunter.models import Job


def filter_jobs(
    jobs: List[Job], region: RegionConfig, exclude_title_keywords: List[str]
) -> List[Job]:
    patterns = [
        re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE)
        for kw in exclude_title_keywords
    ]
    country = region.country.lower()
    return [
        j
        for j in jobs
        if j.country.lower() == country and not any(p.search(j.title) for p in patterns)
    ]
