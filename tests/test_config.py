# 실제 config.yaml이 기대한 형태로 파싱되는지 검증하는 테스트
# Tests that the real config.yaml parses into the expected shape
from pathlib import Path

import pytest
import yaml

from jobhunter.config import load_config
from jobhunter.models import Track

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def test_sources():
    cfg = load_config(CONFIG_PATH)
    assert cfg.sources.simplify.enabled
    assert cfg.sources.simplify.new_grad_repo == "SimplifyJobs/New-Grad-Positions"
    assert "Software" in cfg.sources.simplify.categories
    assert cfg.sources.canada_internship.enabled
    assert not cfg.sources.jsearch.enabled


def test_tracks_and_exclusions():
    cfg = load_config(CONFIG_PATH)
    assert set(cfg.tracks) == {Track.INTERN, Track.NEW_GRAD}
    assert cfg.tracks[Track.INTERN].queries
    assert "senior" in cfg.exclude_title_keywords


def test_regions():
    cfg = load_config(CONFIG_PATH)
    canada = cfg.regions["canada"]
    assert canada.country == "ca"
    assert canada.enabled and canada.notify and canada.publish
    assert canada.notion_db_env == "NOTION_DB_CANADA"
    assert canada.discord_webhook_env == "DISCORD_WEBHOOK_CANADA"
    assert not cfg.regions["usa"].enabled
    assert cfg.enabled_regions() == [canada]


def test_missing_key_raises(tmp_path):
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    del raw["regions"]["canada"]["country"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(KeyError):
        load_config(bad)
