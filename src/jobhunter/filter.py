# 지역(국가)과 제외 키워드로 공고를 거르는 필터
# Filter that keeps jobs matching a region's country and drops excluded title keywords
from __future__ import annotations

import re
from typing import List, Optional

from jobhunter.config import RegionConfig
from jobhunter.models import Job


def _patterns(keywords: List[str]) -> List[re.Pattern]:
    return [re.compile(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", re.IGNORECASE) for kw in keywords]


def filter_jobs(
    jobs: List[Job],
    region: RegionConfig,
    exclude_title_keywords: List[str],
    include_title_keywords: Optional[List[str]] = None,
) -> List[Job]:
    """Keep jobs in the region's country whose title has an include keyword (if any are
    given) and no exclude keyword. Exclusion wins."""
    exclude = _patterns(exclude_title_keywords)
    include = _patterns(include_title_keywords or [])
    country = region.country.lower()
    return [
        j
        for j in jobs
        if j.country.lower() == country
        and (not include or any(p.search(j.title) for p in include))
        and not any(p.search(j.title) for p in exclude)
    ]
