# 수집된 공고를 표현하는 Job 데이터클래스와 Track/Source 열거형
# Job dataclass and Track/Source enums representing collected postings
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Track(str, Enum):
    INTERN = "intern"
    NEW_GRAD = "new_grad"


class Source(str, Enum):
    SIMPLIFY = "simplify"
    CANADA_INTERNSHIP = "canada_internship"
    JSEARCH = "jsearch"


@dataclass(frozen=True)
class Job:
    job_id: str  # normalized application URL (normalization is done by sources/dedupe)
    title: str
    company: str
    url: str  # application link
    track: Track
    source: Source
    country: str  # lowercase ISO code, e.g. "ca" or "us"; matches RegionConfig.country
    location: str = ""  # display text
    remote: bool = False
    category: str = ""  # Simplify's category; empty for other sources
    posted: Optional[date] = None
    collected: date = field(default_factory=date.today)
