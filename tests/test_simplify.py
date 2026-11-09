# Simplify 소스 파서와 fetch 테스트
# Tests for the Simplify source parser and fetch
import json
from datetime import date
from pathlib import Path

from jobhunter.config import SimplifyConfig
from jobhunter.models import Source, Track
from jobhunter.sources import simplify
from jobhunter.sources.simplify import _country, parse_listings

CATS = ["Software", "Software Engineering", "AI/ML/Data"]
DATA = json.loads((Path(__file__).parent / "fixtures" / "simplify_sample.json").read_text())


def test_filters_inactive_invisible_category_and_foreign():
    jobs = parse_listings(DATA, Track.INTERN, CATS)
    titles = {j.title for j in jobs}
    assert "Student Intern - IT Construction Systems" not in titles  # inactive
    assert "Junior Software Engineer" not in titles  # invisible
    assert "Browser Software Engineer Intern" not in titles  # Hardware
    assert all("London" not in j.location for j in jobs)  # UK only -> dropped
    assert {j.country for j in jobs} == {"ca", "us"}


def test_multi_country_listing_yields_one_job_per_country():
    jobs = parse_listings(DATA, Track.INTERN, CATS)
    multi = [j for j in jobs if j.title.startswith("Artificial Intelligence Intern")]
    assert {j.country for j in multi} == {"ca", "us"}
    assert len({j.job_id for j in multi}) == 1
    by = {j.country: j for j in multi}
    assert by["ca"].location == "Toronto, ON, Canada"
    assert by["us"].location == "NYC"


def test_fields_and_remote():
    jobs = parse_listings(DATA, Track.NEW_GRAD, CATS)
    remote = next(j for j in jobs if j.location == "Remote in USA")
    assert remote.remote and remote.country == "us"
    assert remote.track == Track.NEW_GRAD and remote.source == Source.SIMPLIFY
    assert isinstance(remote.posted, date)
    toronto = next(j for j in jobs if j.location == "Toronto, ON, Canada")
    assert not toronto.remote and toronto.category == "Software"


def test_country_classification():
    cases = {
        "Toronto, ON, Canada": "ca", "Calgary, AB, CAN": "ca", "Remote in Canada": "ca",
        "Ontario, Canada": "ca", "Austin, TX": "us", "Carlsbad, Ca": "us", "SF": "us",
        "NYC": "us", "Washington": "us", "United States": "us", "Remote in US": "us",
        "London, UK": None, "Remote in Germany": None, "Munich, Germany": None,
    }
    for loc, want in cases.items():
        assert _country(loc) == want, loc


def test_fetch_uses_both_repos(monkeypatch):
    urls = []

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return DATA

    def fake_get(url, timeout):
        urls.append(url)
        return Resp()

    monkeypatch.setattr(simplify.requests, "get", fake_get)
    cfg = SimplifyConfig(True, "o/grad", "o/intern", CATS)
    jobs = simplify.fetch(cfg)
    assert urls == [
        "https://raw.githubusercontent.com/o/grad/dev/.github/scripts/listings.json",
        "https://raw.githubusercontent.com/o/intern/dev/.github/scripts/listings.json",
    ]
    assert {j.track for j in jobs} == {Track.NEW_GRAD, Track.INTERN}
