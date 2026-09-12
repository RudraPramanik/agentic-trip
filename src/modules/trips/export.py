"""GuidebookExport — pure mapping from structured trip (no LLM rewrite)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuidebookMapPoint:
    place_id: str
    name: str
    lon: float
    lat: float
    day_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "lon": self.lon,
            "lat": self.lat,
            "day_index": self.day_index,
        }


@dataclass
class GuidebookStop:
    place_id: str
    name: str
    lon: float | None = None
    lat: float | None = None
    title: str | None = None
    hub_id: str | None = None
    country_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "lon": self.lon,
            "lat": self.lat,
            "title": self.title,
            "hub_id": self.hub_id,
            "country_code": self.country_code,
        }


@dataclass
class GuidebookDay:
    day_index: int
    title: str | None = None
    story: str | None = None
    hub_id: str | None = None
    stops: list[GuidebookStop] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "title": self.title,
            "story": self.story,
            "hub_id": self.hub_id,
            "stops": [s.to_dict() for s in self.stops],
        }


@dataclass
class GuidebookCover:
    title: str
    status: str
    day_count: int
    stop_count: int
    hubs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "status": self.status,
            "day_count": self.day_count,
            "stop_count": self.stop_count,
            "hubs": list(self.hubs),
        }


@dataclass
class GuidebookExport:
    """Stable JSON view-model for guidebook UI and future PDF."""

    trip_id: str
    cover: GuidebookCover
    hubs: list[str]
    days: list[GuidebookDay]
    narratives: list[dict[str, Any]]
    map_points: list[GuidebookMapPoint]
    route_geometry: list[Any] | None = None  # only when stored on trip; v1 usually None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "trip_id": self.trip_id,
            "cover": self.cover.to_dict(),
            "hubs": list(self.hubs),
            "days": [d.to_dict() for d in self.days],
            "narratives": list(self.narratives),
            "map_points": [p.to_dict() for p in self.map_points],
        }
        if self.route_geometry:
            out["route_geometry"] = list(self.route_geometry)
        return out


def to_guidebook_export(trip: dict[str, Any]) -> GuidebookExport:
    """Map structured trip artifact → GuidebookExport. Does not invent coords/ids."""
    trip_id = str(trip.get("trip_id") or "")
    itinerary = trip.get("itinerary") if isinstance(trip.get("itinerary"), dict) else trip
    status = str(itinerary.get("status") or trip.get("status") or "draft")
    raw_days = itinerary.get("days") or []
    hubs: list[str] = []
    seen_hubs: set[str] = set()
    days: list[GuidebookDay] = []
    narratives: list[dict[str, Any]] = []
    map_points: list[GuidebookMapPoint] = []
    stop_count = 0

    for raw in raw_days:
        if not isinstance(raw, dict):
            continue
        day_index = int(raw.get("day_index") or 0)
        hub_id = raw.get("hub_id")
        if hub_id and str(hub_id) not in seen_hubs:
            seen_hubs.add(str(hub_id))
            hubs.append(str(hub_id))
        stops: list[GuidebookStop] = []
        for s in raw.get("stops") or []:
            if not isinstance(s, dict):
                continue
            place_id = str(s.get("place_id") or "")
            if not place_id:
                continue
            name = str(s.get("name") or "")
            lon = s.get("lon")
            lat = s.get("lat")
            stop = GuidebookStop(
                place_id=place_id,
                name=name,
                lon=lon,
                lat=lat,
                title=s.get("title"),
                hub_id=s.get("hub_id"),
                country_code=s.get("country_code"),
            )
            stops.append(stop)
            stop_count += 1
            if lon is not None and lat is not None:
                map_points.append(
                    GuidebookMapPoint(
                        place_id=place_id,
                        name=name,
                        lon=float(lon),
                        lat=float(lat),
                        day_index=day_index,
                    )
                )
            shub = s.get("hub_id")
            if shub and str(shub) not in seen_hubs:
                seen_hubs.add(str(shub))
                hubs.append(str(shub))

        title = raw.get("title")
        story = raw.get("story")
        days.append(
            GuidebookDay(
                day_index=day_index,
                title=title,
                story=story,
                hub_id=hub_id,
                stops=stops,
            )
        )
        if title or story:
            narratives.append(
                {
                    "day_index": day_index,
                    "title": title,
                    "story": story,
                }
            )

    # Optional geometry only if already on artifact — never invent.
    route_geometry = trip.get("route_geometry") or itinerary.get("route_geometry")
    if not route_geometry:
        route_geometry = None

    cover_title = str(trip.get("title") or itinerary.get("title") or "Trip draft")
    cover = GuidebookCover(
        title=cover_title,
        status=status,
        day_count=len(days),
        stop_count=stop_count,
        hubs=list(hubs),
    )
    return GuidebookExport(
        trip_id=trip_id,
        cover=cover,
        hubs=hubs,
        days=days,
        narratives=narratives,
        map_points=map_points,
        route_geometry=list(route_geometry) if route_geometry else None,
    )
