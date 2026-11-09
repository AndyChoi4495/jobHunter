# 국가 및 제외 키워드 필터 테스트
# Tests for the country and excluded-keyword filter
from jobhunter.config import RegionConfig
from jobhunter.filter import filter_jobs
from jobhunter.models import Job, Source, Track

REGION = RegionConfig("canada", "ca", True, True, True, "N", "D")
KW = ["senior", "sr.", "lead", "manager"]


def job(title, country="ca"):
    return Job(job_id=title, title=title, company="C", url="http://x/" + title,
               track=Track.INTERN, source=Source.SIMPLIFY, country=country)


def test_country_match():
    out = filter_jobs([job("Dev"), job("Dev2", "us")], REGION, KW)
    assert [j.title for j in out] == ["Dev"]


def test_keywords_case_insensitive_and_literal():
    titles = ["SENIOR Developer", "Sr. Engineer", "Tech Lead", "Engineering Manager", "Developer"]
    assert [j.title for j in filter_jobs([job(t) for t in titles], REGION, KW)] == ["Developer"]


def test_word_boundaries():
    titles = ["Leading Edge Intern", "Seniority Analyst", "Srx Engineer"]
    assert len(filter_jobs([job(t) for t in titles], REGION, KW)) == 3


INCLUDE = ["software", "developer", "engineer", "data", "qa"]


def test_include_requires_a_role_word():
    titles = ["Software Intern", "Data Analyst", "QA Co-op", "Relevance Rater", "Coordinator"]
    out = filter_jobs([job(t) for t in titles], REGION, KW, INCLUDE)
    assert [j.title for j in out] == ["Software Intern", "Data Analyst", "QA Co-op"]


def test_exclude_wins_over_include():
    out = filter_jobs([job("Senior Software Engineer")], REGION, KW, INCLUDE)
    assert out == []


def test_empty_include_keeps_everything():
    assert len(filter_jobs([job("Relevance Rater")], REGION, KW, [])) == 1
