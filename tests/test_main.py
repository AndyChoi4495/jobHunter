# main 파이프라인의 흐름을 외부 호출을 모두 대체해 검증하는 테스트
# Tests for the main pipeline flow with all external calls monkeypatched
from __future__ import annotations

import pytest

from jobhunter import main as m
from jobhunter.models import Job, Source, Track


def job(i, country="ca"):
    return Job(
        job_id="id%d" % i, title="Dev", company="C%d" % i, url="id%d" % i,
        track=Track.INTERN, source=Source.SIMPLIFY, country=country,
    )


@pytest.fixture
def env(monkeypatch):
    calls = {"added": [], "summary": [], "warn": [], "board": []}
    monkeypatch.setenv("NOTION_TOKEN", "tok")
    monkeypatch.setenv("NOTION_DB_CANADA", "dbca")
    monkeypatch.setenv("DISCORD_WEBHOOK_CANADA", "hookca")
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.setattr(m.simplify, "fetch", lambda cfg: [job(1), job(2), job(3, "us")])
    monkeypatch.setattr(m.canada_internship, "fetch", lambda: [job(4)])
    monkeypatch.setattr(
        m, "filter_jobs", lambda jobs, r, kw, inc: [j for j in jobs if j.country == r.country]
    )
    monkeypatch.setattr(m, "dedupe", lambda jobs: list(jobs))
    monkeypatch.setattr(m.notion_store, "existing_job_ids", lambda t, d: {"id1"})
    monkeypatch.setattr(
        m.notion_store, "add_jobs",
        lambda t, d, js: calls["added"].append((d, [j.job_id for j in js])),
    )
    monkeypatch.setattr(
        m.notify_discord, "send_summary",
        lambda h, r, js: calls["summary"].append((h, r, len(js))),
    )
    monkeypatch.setattr(
        m.notify_discord, "send_warning", lambda h, msg: calls["warn"].append(msg)
    )
    monkeypatch.setattr(
        m.board, "build_board",
        lambda js, *a, **k: calls["board"].append([j.job_id for j in js]),
    )
    return calls


def test_happy_path(env):
    assert m.main() == 0
    assert env["added"] == [("dbca", ["id2", "id4"])]
    assert env["summary"] == [("hookca", "canada", 2)]
    assert env["board"] == [["id1", "id2", "id4"]]  # canada only (usa disabled)
    assert env["warn"] == []


def test_missing_secret_fails_before_work(env, monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_CANADA")
    assert m.main() == 1
    assert env["added"] == [] and env["board"] == []


def test_zero_rows_warns(env, monkeypatch):
    monkeypatch.setattr(m.canada_internship, "fetch", lambda: [])
    assert m.main() == 0
    assert len(env["warn"]) == 1 and "canada_internship" in env["warn"][0]


def test_fetch_failure_returns_nonzero(env, monkeypatch):
    def boom():
        raise RuntimeError("net")

    monkeypatch.setattr(m.canada_internship, "fetch", boom)
    assert m.main() == 1
    assert env["warn"]


def test_dry_run_skips_io(env, monkeypatch, capsys):
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.delenv("NOTION_TOKEN")
    monkeypatch.delenv("NOTION_DB_CANADA")
    assert m.main() == 0
    assert env["added"] == [] and env["summary"] == []
    assert len(env["board"]) == 1
    assert "[dry-run] canada: 3 postings" in capsys.readouterr().out
