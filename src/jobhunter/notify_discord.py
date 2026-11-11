# Discord 웹훅으로 새 공고 요약과 경고를 보내는 알림 모듈
# Notification module that sends new-posting summaries and warnings to a Discord webhook
from __future__ import annotations

import time
from typing import List

import requests

from jobhunter.models import Job

MAX_LEN = 2000
PAUSE = 2  # seconds between messages; stays under Discord's 30 messages/minute per channel
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
    # Newest posted first (undated last), split across as many messages as needed.
    ordered = sorted(jobs, key=lambda j: j.posted.toordinal() if j.posted else 0, reverse=True)
    messages = []
    current = "**%d new postings (%s)**" % (len(jobs), region_name)
    for job in ordered:
        line = _line(job)
        if len(current) + 1 + len(line) > MAX_LEN:
            messages.append(current)
            current = line
        else:
            current += "\n" + line
    messages.append(current)
    for i, content in enumerate(messages):
        if i:
            time.sleep(PAUSE)
        _send(webhook_url, content)


def send_warning(webhook_url: str, message: str) -> None:
    _send(webhook_url, "⚠️ " + message)
