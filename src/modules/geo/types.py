from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TripIntent:
    """Structured trip intent from user text (dialogue budget)."""

    place_query: str
    duration_days: int | None = None
    vibe: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_query": self.place_query,
            "duration_days": self.duration_days,
            "vibe": list(self.vibe),
            "constraints": list(self.constraints),
            "raw_text": self.raw_text,
        }


@dataclass(frozen=True)
class AskClarification:
    """Missing fields — ask in chat; do not persist trip_scope."""

    question: str
    missing: tuple[str, ...] = ("duration",)


INTENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "place_query": {"type": "string"},
        "duration_days": {"type": ["integer", "null"]},
        "vibe": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["place_query", "duration_days", "vibe", "constraints"],
    "additionalProperties": False,
}


ScopeKind = Literal["city", "region", "country"]


@dataclass
class TripScope:
    kind: ScopeKind
    geo_id: str
    name: str
    bbox: list[float] | None = None  # [min_lon, min_lat, max_lon, max_lat]
    hubs: list[dict[str, Any]] = field(default_factory=list)
    day_budget: int | None = None
    explain: str | None = None
    country_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "geo_id": self.geo_id,
            "name": self.name,
            "bbox": self.bbox,
            "hubs": list(self.hubs),
            "day_budget": self.day_budget,
            "explain": self.explain,
            "country_code": self.country_code,
        }


@dataclass
class NeedsHitl:
    kind: str  # place | hubs | region
    candidates: list[dict[str, Any]]
    prompt: str = "Please pick one option to continue."

    def to_hitl_projection(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "candidates": list(self.candidates),
            "prompt": self.prompt,
            "status": "pending",
        }


@dataclass(frozen=True)
class GeoCandidate:
    geo_id: str
    name: str
    display_name: str
    lat: float
    lon: float
    place_class: str  # city | region | country | other
    admin_level: int | None = None
    bbox: list[float] | None = None
    country_code: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "geo_id": self.geo_id,
            "name": self.name,
            "display_name": self.display_name,
            "lat": self.lat,
            "lon": self.lon,
            "place_class": self.place_class,
            "admin_level": self.admin_level,
            "bbox": self.bbox,
            "country_code": self.country_code,
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeoCandidate:
        return cls(
            geo_id=str(data["geo_id"]),
            name=str(data["name"]),
            display_name=str(data.get("display_name") or data["name"]),
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            place_class=str(data.get("place_class") or "other"),
            admin_level=data.get("admin_level"),
            bbox=data.get("bbox"),
            country_code=data.get("country_code"),
            extra=dict(data.get("extra") or {}),
        )


@dataclass
class GeoSearchResult:
    candidates: list[GeoCandidate]
    query: str = ""

    @property
    def count(self) -> int:
        return len(self.candidates)

    @property
    def needs_hitl(self) -> bool:
        return self.count != 1
