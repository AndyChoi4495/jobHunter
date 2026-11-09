# canada-internship Markdown 파서와 fetch 테스트
# Tests for the canada-internship Markdown parser and fetch
from datetime import date
from pathlib import Path

from jobhunter.models import Source, Track
from jobhunter.sources import canada_internship as ci

FIX = Path(__file__).parent / "fixtures"
INTERN_MD = (FIX / "canada_internships_sample.md").read_text()
GRAD_MD = (FIX / "canada_new_grad_sample.md").read_text()


def test_intern_parses_only_tech_section():
    jobs = ci.parse_markdown(INTERN_MD, Track.INTERN)
    assert len(jobs) == 4  # 4 tech rows; summary table and "Other" section excluded
    j = jobs[0]
    assert j.country == "ca" and j.source == Source.CANADA_INTERNSHIP
    assert j.track == Track.INTERN and j.category == ""
    assert j.posted == date(2026, 11, 9)
    assert j.job_id == ci.normalize_url(j.url)


def test_cleans_new_prefix_and_html():
    jobs = ci.parse_markdown(GRAD_MD, Track.NEW_GRAD)
    assert jobs[0].title == "Junior Software Engineer (Remote)"
    assert jobs[0].remote and jobs[0].company == "Joblet-AI"
    assert all("<" not in j.title + j.location + j.company for j in jobs)
    assert all("&amp;" not in j.title for j in jobs)


def test_wrong_track_heading_yields_nothing():
    assert ci.parse_markdown(GRAD_MD, Track.INTERN) == []


def test_format_change_yields_empty():
    assert ci.parse_markdown("# nothing here\n| a | b |\n", Track.INTERN) == []


def test_fetch(monkeypatch):
    urls = []

    class Resp:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        urls.append(url)
        return Resp(INTERN_MD if "INTERNSHIPS" in url else GRAD_MD)

    monkeypatch.setattr(ci.requests, "get", fake_get)
    jobs = ci.fetch()
    assert [u.rsplit("/", 1)[1] for u in urls] == ["INTERNSHIPS.md", "NEW_GRAD.md"]
    assert {j.track for j in jobs} == {Track.INTERN, Track.NEW_GRAD}
