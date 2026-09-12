"""Planner domain types for itinerary packing and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Stop:
    place_id: str
    name: str = ""
    lon: float | None = None
    lat: float | None = None
    country_code: str | None = None
    hub_id: str | None = None
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "lon": self.lon,
            "lat": self.lat,
            "country_code": self.country_code,
            "hub_id": self.hub_id,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stop:
        return cls(
            place_id=str(data["place_id"]),
            name=str(data.get("name") or ""),
            lon=data.get("lon"),
            lat=data.get("lat"),
            country_code=data.get("country_code"),
            hub_id=data.get("hub_id"),
            title=data.get("title"),
        )


@dataclass
class Day:
    day_index: int
    stops: list[Stop] = field(default_factory=list)
    hub_id: str | None = None
    story: str | None = None
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "stops": [s.to_dict() for s in self.stops],
            "hub_id": self.hub_id,
            "story": self.story,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Day:
        return cls(
            day_index=int(data["day_index"]),
            stops=[Stop.from_dict(s) for s in (data.get("stops") or [])],
            hub_id=data.get("hub_id"),
            story=data.get("story"),
            title=data.get("title"),
        )


@dataclass
class Itinerary:
    days: list[Day] = field(default_factory=list)
    status: str = "draft"
    place_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        ids = list(self.place_ids) or [
            s.place_id for d in self.days for s in d.stops
        ]
        return {
            "status": self.status,
            "days": [d.to_dict() for d in self.days],
            "place_ids": ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Itinerary:
        days = [Day.from_dict(d) for d in (data.get("days") or [])]
        ids = [str(x) for x in (data.get("place_ids") or [])]
        if not ids:
            ids = [s.place_id for d in days for s in d.stops]
        return cls(days=days, status=str(data.get("status") or "draft"), place_ids=ids)

    def stop_place_ids(self) -> set[str]:
        return {s.place_id for d in self.days for s in d.stops}


@dataclass
class ValidateResult:
    ok: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors)}
