# URL 정규화와 중복 병합 테스트
# Tests for URL normalization and duplicate merging
from datetime import date

from jobhunter.dedupe import dedupe, normalize_url
from jobhunter.models import Job, Source, Track


def mk(url, title="Dev", company="Acme", country="ca", source=Source.SIMPLIFY, **kw):
    return Job(job_id=normalize_url(url), title=title, company=company, url=url,
               track=Track.INTERN, source=source, country=country, **kw)


def test_normalize_url():
    assert normalize_url("HTTPS://www.Example.com/jobs/1/?utm_source=x&gh_jid=5#frag") == (
        "https://example.com/jobs/1?gh_jid=5"
    )
    assert normalize_url("https://x.com/a?embed=true") == "https://x.com/a"
    assert normalize_url("https://x.com/a/") == normalize_url("https://x.com/a")


def test_merge_by_url_fills_missing_fields():
    a = mk("https://x.com/1", category="Software")
    b = mk("https://www.x.com/1/?utm_medium=z", title="Other", posted=date(2026, 1, 2),
           source=Source.CANADA_INTERNSHIP)
    out = dedupe([a, b])
    assert len(out) == 1
    assert out[0].source == Source.SIMPLIFY and out[0].category == "Software"
    assert out[0].posted == date(2026, 1, 2)


def test_merge_by_company_title_country():
    out = dedupe([mk("https://x.com/1"), mk("https://y.com/2", title=" dev ", company="ACME")])
    assert len(out) == 1


def test_different_country_not_merged_and_order_kept():
    jobs = [
        mk("https://x.com/1"),
        mk("https://y.com/2", country="us"),
        mk("https://z.com/3", title="Q"),
    ]
    assert dedupe(jobs) == jobs
