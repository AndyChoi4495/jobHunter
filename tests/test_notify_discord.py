# Discord 메시지의 길이 제한과 형식을 검증하는 테스트
# Tests for Discord message length limits and formatting
from __future__ import annotations

from dataclasses import replace
from datetime import date

from jobhunter import notify_discord
from jobhunter.models import Job, Source, Track


def make(i):
    return Job(
        job_id=str(i), title="Software Developer Intern %d" % i, company="Company",
        url="https://example.com/jobs/%d" % i, track=Track.INTERN,
        source=Source.SIMPLIFY, country="ca", location="Toronto, ON",
    )


class Resp:
    def raise_for_status(self):
        pass


def capture(monkeypatch):
    sent = []
    monkeypatch.setattr(
        notify_discord.requests,
        "post",
        lambda url, json, timeout: sent.append(json["content"]) or Resp(),
    )
    return sent


def test_summary_small(monkeypatch):
    sent = capture(monkeypatch)
    notify_discord.send_summary("hook", "canada", [make(1), make(2)])
    assert len(sent) == 1
    assert "2 new postings (canada)" in sent[0]
    expected = "[Intern] Company — Software Developer Intern 1 (Toronto, ON)"
    assert expected + " <https://example.com/jobs/1>" in sent[0]
    assert "more" not in sent[0]


def test_summary_truncates(monkeypatch):
    sent = capture(monkeypatch)
    notify_discord.send_summary("hook", "canada", [make(i) for i in range(100)])
    assert len(sent[0]) <= 2000
    last = sent[0].splitlines()[-1]
    assert last.startswith("+") and last.endswith("more")


def test_warning(monkeypatch):
    sent = capture(monkeypatch)
    notify_discord.send_warning("hook", "x" * 5000)
    assert sent[0].startswith("⚠️ ") and len(sent[0]) == 2000


def test_summary_newest_first(monkeypatch):
    sent = capture(monkeypatch)
    old = replace(make(1), posted=date(2026, 11, 1))
    undated = make(2)
    new = replace(make(3), posted=date(2026, 11, 9))
    notify_discord.send_summary("hook", "canada", [old, undated, new])
    lines = sent[0].splitlines()[1:]
    assert ["Intern 3" in lines[0], "Intern 1" in lines[1], "Intern 2" in lines[2]] == [True] * 3


def test_truncation_keeps_newest(monkeypatch):
    sent = capture(monkeypatch)
    jobs = [replace(make(i), posted=date(2026, 1, 1)) for i in range(100)]
    jobs.append(replace(make(999), posted=date(2026, 11, 9)))
    notify_discord.send_summary("hook", "canada", jobs)
    assert "Intern 999" in sent[0].splitlines()[1]
