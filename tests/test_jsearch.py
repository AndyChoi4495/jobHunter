# JSearch 응답 파싱, 요청 파라미터, 실행 시각 판정 테스트
# Tests for JSearch response parsing, request parameters, and run-time check
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from jobhunter.config import TrackConfig
from jobhunter.models import Source, Track
from jobhunter.sources import jsearch

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "jsearch_sample.json").read_text(encoding="utf-8")
)


def test_parse_results():
    jobs = jsearch.parse_results(FIXTURE, Track.NEW_GRAD)
    assert len(jobs) == 4  # the posting without an apply link is skipped
    j = jobs[0]
    assert (j.company, j.title) == ("Konrad", "Software Developer (Entry Level)")
    assert j.source is Source.JSEARCH and j.track is Track.NEW_GRAD
    assert j.country == "ca"
    assert j.job_id.startswith("https://bebee.com/ca/jobs/")
    assert j.posted == date(2026, 11, 8)


class Resp:
    def raise_for_status(self):
        pass

    def json(self):
        return FIXTURE


def test_fetch_runs_every_query(monkeypatch):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append((url, params, headers))
        return Resp()

    monkeypatch.setattr(jsearch.requests, "get", fake_get)
    tracks = {
        Track.INTERN: TrackConfig(queries=["a", "b"]),
        Track.NEW_GRAD: TrackConfig(queries=["c"]),
    }
    jobs = jsearch.fetch(tracks, "ca", "KEY")
    assert [c[1]["query"] for c in calls] == ["a", "b", "c"]
    url, params, headers = calls[0]
    assert url.endswith("/search-v2")
    assert params == {"query": "a", "country": "ca", "date_posted": "3days"}
    assert headers["X-RapidAPI-Key"] == "KEY"
    assert len(jobs) == 12 and jobs[0].track is Track.INTERN and jobs[-1].track is Track.NEW_GRAD


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_should_run_noon_toronto_weekdays_across_dst():
    # Monday 2026-11-09, EST (UTC-5): 17:05 UTC is 12:05 Toronto.
    assert jsearch.should_run(utc(2026, 11, 9, 17, 5), 12)
    assert not jsearch.should_run(utc(2026, 11, 9, 16, 5), 12)
    # Monday 2026-06-08, EDT (UTC-4): 16:05 UTC is 12:05 Toronto.
    assert jsearch.should_run(utc(2026, 6, 8, 16, 5), 12)
    assert not jsearch.should_run(utc(2026, 6, 8, 17, 5), 12)


def test_should_run_skips_weekends():
    assert not jsearch.should_run(utc(2026, 11, 7, 17, 5), 12)  # Saturday
    assert not jsearch.should_run(utc(2026, 11, 8, 17, 5), 12)  # Sunday
