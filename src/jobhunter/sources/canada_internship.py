# Francklin9999/canada-internship의 Markdown 표(Tech 섹션)를 Job 목록으로 변환하는 소스
# Source that parses the Tech-section Markdown tables of Francklin9999/canada-internship
from __future__ import annotations

import html
import re
from datetime import date, datetime
from typing import List, Optional

import requests

from jobhunter.dedupe import normalize_url
from jobhunter.models import Job, Source, Track

BRANCH = "master"  # the repo's default branch
_BASE = "https://raw.githubusercontent.com/Francklin9999/canada-internship/" + BRANCH + "/"
_FILES = {Track.INTERN: "INTERNSHIPS.md", Track.NEW_GRAD: "NEW_GRAD.md"}
_HEADINGS = {Track.INTERN: "## Tech internships", Track.NEW_GRAD: "## Tech new-grad roles"}

_HREF_RE = re.compile(r'<a href="([^"]+)"')
_TAG_RE = re.compile(r"<[^>]+>")
_DATE_RE = re.compile(r"[A-Z][a-z]{2} \d{1,2}, \d{4}")


def _text(cell: str) -> str:
    return html.unescape(_TAG_RE.sub("", cell)).strip()


def _posted(cell: str) -> Optional[date]:
    m = _DATE_RE.search(cell)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(0), "%b %d, %Y").date()
    except ValueError:
        return None


def _section(text: str, heading: str) -> List[str]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == heading:
            out = []
            for nxt in lines[i + 1 :]:
                if nxt.startswith("## "):
                    break
                out.append(nxt)
            return out
    return []


def parse_markdown(text: str, track: Track) -> List[Job]:
    jobs: List[Job] = []
    for line in _section(text, _HEADINGS[track]):
        if not line.startswith("|") or '<a href="' not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) < 6:
            continue
        m = _HREF_RE.search(cells[5])
        if not m:
            continue
        url = html.unescape(m.group(1))
        title = re.sub(r"^NEW\s+", "", _text(cells[1]))
        location = _text(cells[2])
        jobs.append(
            Job(
                job_id=normalize_url(url),
                title=title,
                company=_text(cells[0]),
                url=url,
                track=track,
                source=Source.CANADA_INTERNSHIP,
                country="ca",
                location=location,
                remote="remote" in (title + " " + location).lower(),
                posted=_posted(cells[4]),
            )
        )
    return jobs


def fetch() -> List[Job]:
    jobs: List[Job] = []
    for track, name in _FILES.items():
        resp = requests.get(_BASE + name, timeout=60)
        resp.raise_for_status()
        jobs += parse_markdown(resp.text, track)
    return jobs
