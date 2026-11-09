# config.yaml을 타입이 있는 객체로 읽어오는 로더
# Loader that parses config.yaml into typed objects
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

import yaml

from jobhunter.models import Track


@dataclass(frozen=True)
class SimplifyConfig:
    enabled: bool
    new_grad_repo: str
    intern_repo: str
    categories: List[str]


@dataclass(frozen=True)
class CanadaInternshipConfig:
    enabled: bool


@dataclass(frozen=True)
class JSearchConfig:
    enabled: bool
    run_hour: int


@dataclass(frozen=True)
class SourcesConfig:
    simplify: SimplifyConfig
    canada_internship: CanadaInternshipConfig
    jsearch: JSearchConfig


@dataclass(frozen=True)
class TrackConfig:
    queries: List[str]


@dataclass(frozen=True)
class RegionConfig:
    name: str
    country: str
    enabled: bool
    notify: bool
    publish: bool
    notion_db_env: str  # env var name, never the secret itself
    discord_webhook_env: str  # env var name, never the secret itself


@dataclass(frozen=True)
class Config:
    sources: SourcesConfig
    tracks: Dict[Track, TrackConfig]
    exclude_title_keywords: List[str]
    include_title_keywords: List[str]
    regions: Dict[str, RegionConfig]

    def enabled_regions(self) -> List[RegionConfig]:
        return [r for r in self.regions.values() if r.enabled]


def load_config(path: Union[str, Path] = "config.yaml") -> Config:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    src = raw["sources"]
    sim = src["simplify"]
    return Config(
        sources=SourcesConfig(
            simplify=SimplifyConfig(
                enabled=bool(sim["enabled"]),
                new_grad_repo=sim["new_grad_repo"],
                intern_repo=sim["intern_repo"],
                categories=list(sim["categories"]),
            ),
            canada_internship=CanadaInternshipConfig(
                enabled=bool(src["canada_internship"]["enabled"])
            ),
            jsearch=JSearchConfig(
                enabled=bool(src["jsearch"]["enabled"]),
                run_hour=int(src["jsearch"]["run_hour"]),
            ),
        ),
        tracks={
            Track(name): TrackConfig(queries=list(t["queries"]))
            for name, t in raw["tracks"].items()
        },
        exclude_title_keywords=list(raw["exclude_title_keywords"]),
        include_title_keywords=list(raw["include_title_keywords"]),
        regions={
            name: RegionConfig(
                name=name,
                country=r["country"],
                enabled=bool(r["enabled"]),
                notify=bool(r["notify"]),
                publish=bool(r["publish"]),
                notion_db_env=r["notion_db_env"],
                discord_webhook_env=r["discord_webhook_env"],
            )
            for name, r in raw["regions"].items()
        },
    )
