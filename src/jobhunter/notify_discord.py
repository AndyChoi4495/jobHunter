# Discord 웹훅으로 새 공고 요약과 경고를 보내는 알림 모듈
# Notification module that sends new-posting summaries and warnings to a Discord webhook
from __future__ import annotations

from typing import List

import requests

from jobhunter.models import Job

MAX_LEN = 2000
BUDGET = 1900  # leave room for the "+N more" line
TRACK_LABELS = {"intern": "Intern", "new_grad": "New Grad"}


def _send(webhook_url: str, content: str) -> None:
    resp = requests.post(webhook_url, json={"content": content[:MAX_LEN]}, timeout=30)
    resp.raise_for_status()


def _line(job: Job) -> str:
    where = " (%s)" % job.location if job.location else ""
    return "[%s] %s — %s%s <%s>" % (
        TRACK_LABELS[job.track.value],
        job.company,
        job.title,
        where,
        job.url,
    )


def send_summary(webhook_url: str, region_name: str, jobs: List[Job]) -> None:
    lines = ["**%d new postings (%s)**" % (len(jobs), region_name)]
    size = len(lines[0])
    shown = 0
    # Newest posted first (undated last), so truncation never hides the freshest postings.
    ordered = sorted(jobs, key=lambda j: j.posted.toordinal() if j.posted else 0, reverse=True)
    for job in ordered:
        line = _line(job)
        if size + len(line) + 1 > BUDGET:
            break
        lines.append(line)
        size += len(line) + 1
        shown += 1
    if shown < len(jobs):
        lines.append("+%d more" % (len(jobs) - shown))
    _send(webhook_url, "\n".join(lines))


def send_warning(webhook_url: str, message: str) -> None:
    _send(webhook_url, "⚠️ " + message)
