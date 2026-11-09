# notion_store의 페이지네이션, 속성 형태, 429 재시도를 검증하는 테스트
# Tests for notion_store pagination, property shape, and 429 retry
from __future__ import annotations

from datetime import date

import pytest

from jobhunter import notion_store
from jobhunter.models import Job, Source, Track


class FakeResp:
    def __init__(self, data=None, status=200, headers=None):
        self._data = data or {}
        self.status_code = status
        self.headers = headers or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http %d" % self.status_code)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(notion_store.time, "sleep", lambda s: None)


def page(job_id):
    return {"properties": {"Job ID": {"rich_text": [{"plain_text": job_id}]}}}


def test_existing_job_ids_paginates(monkeypatch):
    responses = [
        FakeResp({"results": [page("a"), page("b")], "has_more": True, "next_cursor": "c1"}),
        FakeResp({"results": [page("c"), {"properties": {}}], "has_more": False}),
    ]
    bodies = []

    def fake_post(url, headers, json, timeout):
        bodies.append(json)
        assert headers["Notion-Version"] == "2022-06-28"
        return responses.pop(0)

    monkeypatch.setattr(notion_store.requests, "post", fake_post)
    assert notion_store.existing_job_ids("t", "db") == {"a", "b", "c"}
    assert "start_cursor" not in bodies[0]
    assert bodies[1]["start_cursor"] == "c1"


def test_add_jobs_payload(monkeypatch):
    sent = []
    monkeypatch.setattr(
        notion_store.requests,
        "post",
        lambda url, headers, json, timeout: sent.append((url, json)) or FakeResp(),
    )
    job = Job(
        job_id="https://x.com/1",
        title="Dev",
        company="Acme",
        url="https://x.com/1",
        track=Track.NEW_GRAD,
        source=Source.CANADA_INTERNSHIP,
        country="ca",
        category="Software",
        posted=date(2026, 1, 2),
    )
    bare = Job(
        job_id="u2", title="T", company="C", url="u2",
        track=Track.INTERN, source=Source.SIMPLIFY, country="ca",
    )
    notion_store.add_jobs("t", "db1", [job, bare])
    url, body = sent[0]
    assert url.endswith("/pages")
    assert body["parent"] == {"database_id": "db1"}
    p = body["properties"]
    assert p["Track"]["select"]["name"] == "New Grad"
    assert p["Source"]["select"]["name"] == "CanadaInternship"
    assert p["Posted"]["date"]["start"] == "2026-01-02"
    assert p["Link"]["url"] == "https://x.com/1"
    assert "Status" not in p
    p2 = sent[1][1]["properties"]
    assert "Category" not in p2 and "Posted" not in p2
    assert p2["Track"]["select"]["name"] == "Intern"


def test_retry_on_429(monkeypatch):
    responses = [FakeResp(status=429, headers={"Retry-After": "0"}), FakeResp({"ok": 1})]
    monkeypatch.setattr(
        notion_store.requests, "post", lambda *a, **k: responses.pop(0)
    )
    assert notion_store._post("t", "/x", {}) == {"ok": 1}


def test_http_error_raises(monkeypatch):
    monkeypatch.setattr(
        notion_store.requests, "post", lambda *a, **k: FakeResp(status=400)
    )
    with pytest.raises(RuntimeError):
        notion_store._post("t", "/x", {})
