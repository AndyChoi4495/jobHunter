# SimplifyJobs 저장소의 listings.json을 Job 목록으로 변환하는 소스
# Source that turns SimplifyJobs repos' listings.json into Job objects
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from jobhunter.config import SimplifyConfig
from jobhunter.dedupe import normalize_url
from jobhunter.models import Job, Source, Track

BRANCH = "dev"  # both SimplifyJobs repos use `dev` as the default branch
_URL = "https://raw.githubusercontent.com/{repo}/" + BRANCH + "/.github/scripts/listings.json"

_CA_RE = re.compile(
    r"\bcanada\b|\bCAN$|,\s*(AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT)\b", re.IGNORECASE
)
_US_CODES = (
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT "
    "NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY"
).split()
_US_NAMES = {
    n.lower()
    for n in (
        "Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida "
        "Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine "
        "Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska "
        "Nevada Ohio Oklahoma Oregon Pennsylvania Tennessee Texas Utah Vermont Virginia "
        "Washington Wisconsin Wyoming"
    ).split()
} | {"new hampshire", "new jersey", "new mexico", "new york", "north carolina",
     "north dakota", "rhode island", "south carolina", "south dakota", "west virginia",
     "district of columbia"}
_US_CODE_RE = re.compile(r",\s*(" + "|".join(_US_CODES) + r")$", re.IGNORECASE)
_US_WORD_RE = re.compile(r"\bunited states\b|\busa\b|\bUS\b", re.IGNORECASE)
_US_ALIASES = {"sf", "south sf", "nyc", "la"}


def _country(location: str) -> Optional[str]:
    # Canada is checked first: "CA" alone is ambiguous (California), province codes are not.
    loc = location.strip()
    if _CA_RE.search(loc):
        return "ca"
    if (
        _US_CODE_RE.search(loc)
        or _US_WORD_RE.search(loc)
        or loc.lower() in _US_ALIASES
        or loc.lower() in _US_NAMES
    ):
        return "us"
    return None


def parse_listings(data: list, track: Track, categories: List[str]) -> List[Job]:
    jobs: List[Job] = []
    for item in data:
        if not (item.get("active") and item.get("is_visible")):
            continue
        if item.get("category") not in categories:
            continue
        by_country: Dict[str, List[str]] = {}
        for loc in item.get("locations") or []:
            country = _country(loc)
            if country:
                by_country.setdefault(country, []).append(loc)
        posted = item.get("date_posted")
        for country, locs in by_country.items():
            jobs.append(
                Job(
                    job_id=normalize_url(item["url"]),
                    title=item["title"],
                    company=item["company_name"],
                    url=item["url"],
                    track=track,
                    source=Source.SIMPLIFY,
                    country=country,
                    location=", ".join(locs),
                    remote=any("remote" in loc.lower() for loc in locs),
                    category=item["category"],
                    posted=(
                        datetime.fromtimestamp(posted, tz=timezone.utc).date()
                        if posted
                        else None
                    ),
                )
            )
    return jobs


def _fetch_repo(repo: str, track: Track, categories: List[str]) -> List[Job]:
    resp = requests.get(_URL.format(repo=repo), timeout=60)
    resp.raise_for_status()
    return parse_listings(resp.json(), track, categories)


def fetch(cfg: SimplifyConfig) -> List[Job]:
    return _fetch_repo(cfg.new_grad_repo, Track.NEW_GRAD, cfg.categories) + _fetch_repo(
        cfg.intern_repo, Track.INTERN, cfg.categories
    )
