# board.build_board의 출력(공개 필드만, 정렬, 유효 JSON)을 검증하는 테스트
# Tests for board.build_board output (public fields only, sorting, valid JSON)
import json
from datetime import date

from jobhunter.board import build_board
from jobhunter.models import Job, Source, Track

PUBLIC_KEYS = {
    "company", "title", "location", "track", "posted", "source", "url", "remote", "category",
}


def _job(title, posted, **kw):
    base = dict(
        job_id="SECRET-JOB-ID",
        title=title,
        company="Acme",
        url="https://example.com/apply",
        track=Track.INTERN,
        source=Source.SIMPLIFY,
        country="zz",
        location="Toronto, ON",
        posted=posted,
        collected=date(1999, 1, 2),
    )
    base.update(kw)
    return Job(**base)


def test_writes_only_public_fields_and_creates_dir(tmp_path):
    out = tmp_path / "nested" / "jobs.json"
    build_board([_job("Dev", date(2026, 11, 1))], out)
    raw = out.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "generated_at" in data
    assert set(data["jobs"][0]) == PUBLIC_KEYS
    for leaked in ("SECRET-JOB-ID", "1999-01-02", '"zz"'):
        assert leaked not in raw


def test_labels_and_iso_dates(tmp_path):
    out = tmp_path / "jobs.json"
    build_board(
        [
            _job("A", date(2026, 11, 1), track=Track.NEW_GRAD, source=Source.CANADA_INTERNSHIP),
            _job("B", None, source=Source.SIMPLIFY),
        ],
        out,
    )
    jobs = {j["title"]: j for j in json.loads(out.read_text())["jobs"]}
    assert jobs["A"]["track"] == "New Grad"
    assert jobs["A"]["source"] == "CanadaInternship"
    assert jobs["A"]["posted"] == "2026-11-01"
    assert jobs["B"]["track"] == "Intern"
    assert jobs["B"]["source"] == "Simplify"
    assert jobs["B"]["posted"] is None


def test_sorted_newest_first_undated_last(tmp_path):
    out = tmp_path / "jobs.json"
    build_board(
        [_job("old", date(2026, 1, 1)), _job("none", None), _job("new", date(2026, 11, 1))],
        out,
    )
    titles = [j["title"] for j in json.loads(out.read_text())["jobs"]]
    assert titles == ["new", "old", "none"]


def test_empty_list(tmp_path):
    out = tmp_path / "jobs.json"
    build_board([], out)
    assert json.loads(out.read_text())["jobs"] == []


def test_jsearch_postings_are_published(tmp_path):
    out = tmp_path / "jobs.json"
    build_board([_job("JS", date(2026, 1, 2), source=Source.JSEARCH)], out)
    assert json.loads(out.read_text())["jobs"][0]["source"] == "JSearch"


def _prev(title, posted, source="JSearch", url=None, company="Acme"):
    return {
        "company": company, "title": title, "location": "", "track": "Intern",
        "posted": posted, "source": source, "url": url or "https://example.com/" + title,
        "remote": False, "category": "",
    }


def test_carries_recent_jsearch_from_previous_board(tmp_path):
    out = tmp_path / "jobs.json"
    previous = [
        _prev("recent", "2026-11-01"),
        _prev("expired", "2026-10-27"),          # older than 14 days on 2026-11-11
        _prev("undated", None),
        _prev("free", "2026-11-05", source="Simplify"),  # the current run owns free sources
        _prev("same-url", "2026-11-05", url="https://www.example.com/apply/"),
        _prev("Dev", "2026-11-05", company="ACME"),  # same company + title as current
    ]
    build_board(
        [_job("Dev", date(2026, 11, 10))], out, previous=previous, today=date(2026, 11, 11)
    )
    titles = [j["title"] for j in json.loads(out.read_text())["jobs"]]
    assert titles == ["Dev", "recent"]


def test_carried_entries_keep_only_public_fields(tmp_path):
    out = tmp_path / "jobs.json"
    build_board([], out, previous=[_prev("js", "2026-11-10")], today=date(2026, 11, 11))
    assert set(json.loads(out.read_text())["jobs"][0]) == PUBLIC_KEYS
