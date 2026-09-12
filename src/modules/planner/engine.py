"""Constrained greedy day packer — catalog ids only; no LLM stop-order."""

from __future__ import annotations

from typing import Any

from src.modules.planner.matrix import travel_matrix
from src.modules.planner.types import Day, Itinerary, Stop
from src.ports import TravelEngine

# Soft caps per day (seconds of travel between stops + visit slots).
_DEFAULT_DAY_TRAVEL_BUDGET_S = 4 * 3600.0
_DEFAULT_MAX_STOPS_PER_DAY = 4
_DEFAULT_VISIT_SECONDS = 45 * 60


def _day_budget(scope: dict[str, Any], prefs: dict[str, Any] | None) -> int:
    prefs = prefs or {}
    for key in ("day_budget", "days", "duration_days"):
        if key in prefs and prefs[key] is not None:
            return max(1, int(prefs[key]))
    for key in ("day_budget", "days", "duration_days"):
        if key in scope and scope[key] is not None:
            return max(1, int(scope[key]))
    intent = scope.get("intent") or {}
    if isinstance(intent, dict) and intent.get("duration_days") is not None:
        return max(1, int(intent["duration_days"]))
    return 3


def _hubs(scope: dict[str, Any]) -> list[dict[str, Any]]:
    raw = scope.get("hubs") or []
    if not isinstance(raw, list):
        return []
    return [h for h in raw if isinstance(h, dict)]


def _place_near_hub(place: dict[str, Any], hub: dict[str, Any]) -> bool:
    """Cheap membership: hub geo_id/name match or bbox containment when present."""
    hub_id = str(hub.get("geo_id") or hub.get("id") or hub.get("name") or "")
    place_hub = place.get("hub_id")
    if place_hub and hub_id and str(place_hub) == hub_id:
        return True
    bbox = hub.get("bbox")
    lon, lat = place.get("lon"), place.get("lat")
    if (
        isinstance(bbox, (list, tuple))
        and len(bbox) == 4
        and lon is not None
        and lat is not None
    ):
        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox)
        return min_lon <= float(lon) <= max_lon and min_lat <= float(lat) <= max_lat
    return False


def pack_days(
    scope: dict[str, Any],
    places: list[dict[str, Any]],
    prefs: dict[str, Any] | None = None,
) -> Itinerary:
    """Greedy assign catalog stops to days under travel/stop caps.

    Complexity: O(n log n) sort + linear assign.
    """
    prefs = prefs or {}
    n_days = _day_budget(scope, prefs)
    if not places:
        return Itinerary(
            days=[Day(day_index=i + 1) for i in range(n_days)],
            status="draft",
            place_ids=[],
        )

    # Deterministic sort: category preference then name (never LLM order).
    preferred = set(str(t).lower() for t in (prefs.get("tags") or []))
    preferred_cat = str(prefs.get("category") or "").lower()

    def sort_key(p: dict[str, Any]) -> tuple:
        tags = [str(t).lower() for t in (p.get("tags") or [])]
        tag_hit = 0 if preferred.intersection(tags) else 1
        cat_hit = 0 if preferred_cat and str(p.get("category") or "").lower() == preferred_cat else 1
        return (tag_hit, cat_hit, str(p.get("name") or ""), str(p.get("id") or ""))

    ordered = sorted(places, key=sort_key)
    matrix = travel_matrix(ordered)
    durations = matrix["durations_seconds"]
    index_by_id = {str(p["id"]): i for i, p in enumerate(ordered) if p.get("id")}

    hubs = _hubs(scope)
    days: list[Day] = []
    used: set[str] = set()

    # Allocate day slots per hub when hubs exist; else one pool.
    if hubs:
        base = n_days // len(hubs)
        rem = n_days % len(hubs)
        hub_day_counts = [base + (1 if i < rem else 0) for i in range(len(hubs))]
        # Ensure at least one day per hub when n_days >= len(hubs)
        if n_days >= len(hubs):
            hub_day_counts = [max(1, c) for c in hub_day_counts]
            while sum(hub_day_counts) > n_days:
                for i in range(len(hub_day_counts)):
                    if hub_day_counts[i] > 1 and sum(hub_day_counts) > n_days:
                        hub_day_counts[i] -= 1
        day_hubs: list[dict[str, Any] | None] = []
        for hub, count in zip(hubs, hub_day_counts, strict=False):
            day_hubs.extend([hub] * count)
        while len(day_hubs) < n_days:
            day_hubs.append(hubs[-1])
        day_hubs = day_hubs[:n_days]
    else:
        day_hubs = [None] * n_days

    max_stops = int(prefs.get("max_stops_per_day") or _DEFAULT_MAX_STOPS_PER_DAY)
    travel_budget = float(prefs.get("day_travel_budget_s") or _DEFAULT_DAY_TRAVEL_BUDGET_S)

    for day_i, hub in enumerate(day_hubs):
        day = Day(
            day_index=day_i + 1,
            hub_id=str(hub.get("geo_id") or hub.get("id") or hub.get("name"))
            if hub
            else None,
        )
        candidates = [
            p
            for p in ordered
            if p.get("id")
            and str(p["id"]) not in used
            and (hub is None or _place_near_hub(p, hub) or not hubs)
        ]
        # If hub filter emptied the pool, fall back to remaining unused places.
        if not candidates:
            candidates = [
                p for p in ordered if p.get("id") and str(p["id"]) not in used
            ]

        travel_used = 0.0
        last_idx: int | None = None
        for place in candidates:
            if len(day.stops) >= max_stops:
                break
            pid = str(place["id"])
            idx = index_by_id[pid]
            transfer = 0.0 if last_idx is None else float(durations[last_idx][idx])
            if (
                last_idx is not None
                and travel_used + transfer + _DEFAULT_VISIT_SECONDS > travel_budget
                and day.stops
            ):
                continue
            day.stops.append(
                Stop(
                    place_id=pid,
                    name=str(place.get("name") or ""),
                    lon=place.get("lon"),
                    lat=place.get("lat"),
                    country_code=place.get("country_code"),
                    hub_id=day.hub_id,
                )
            )
            used.add(pid)
            travel_used += transfer + _DEFAULT_VISIT_SECONDS
            last_idx = idx
        days.append(day)

    return Itinerary(
        days=days,
        status="draft",
        place_ids=[s.place_id for d in days for s in d.stops],
    )


class GreedyTravelEngine(TravelEngine):
    def pack(self, scope: Any, places: Any, prefs: Any) -> Itinerary:
        return pack_days(
            dict(scope or {}),
            list(places or []),
            dict(prefs or {}) if prefs else None,
        )
