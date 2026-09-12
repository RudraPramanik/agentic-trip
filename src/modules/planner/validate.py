"""Hard validation gate before draft persist."""

from __future__ import annotations

from typing import Any

from src.modules.planner.types import Itinerary, ValidateResult

_MAX_TRANSFER_S = 6 * 3600.0  # transfers longer than 6h are insane for day hops


def validate_itinerary(
    itinerary: Itinerary,
    catalog_ids: set[str] | list[str],
    scope: dict[str, Any],
    *,
    day_budget: int | None = None,
    place_countries: dict[str, str | None] | None = None,
) -> ValidateResult:
    """Pure gates: stop id ∈ catalog; country filter; day caps; transfer sanity."""
    errors: list[str] = []
    catalog = {str(x) for x in catalog_ids}
    country = (scope.get("country_code") or "").strip().lower() or None
    place_countries = place_countries or {}

    expected_days = day_budget
    if expected_days is None:
        for key in ("day_budget", "days", "duration_days"):
            if scope.get(key) is not None:
                expected_days = int(scope[key])
                break

    if expected_days is not None and len(itinerary.days) > expected_days:
        errors.append("day_cap_exceeded")

    seen: set[str] = set()
    for day in itinerary.days:
        prev: tuple[float, float] | None = None
        for stop in day.stops:
            pid = stop.place_id
            if pid not in catalog:
                errors.append(f"unknown_venue:{pid}")
                continue
            if pid in seen:
                errors.append(f"duplicate_stop:{pid}")
            seen.add(pid)

            cc = (stop.country_code or place_countries.get(pid) or "").strip().lower()
            if country and (not cc or cc != country):
                errors.append(f"foreign_poi:{pid}")

            if stop.lon is not None and stop.lat is not None:
                cur = (float(stop.lon), float(stop.lat))
                if prev is not None:
                    # crude transfer sanity via degree delta (avoid importing matrix cycle)
                    dlon = abs(cur[0] - prev[0])
                    dlat = abs(cur[1] - prev[1])
                    # ~111km per degree; > ~400km same-day is insane
                    approx_km = (dlon**2 + dlat**2) ** 0.5 * 111.0
                    if approx_km > 400:
                        errors.append(f"transfer_insanity:{pid}")
                prev = cur

    return ValidateResult(ok=not errors, errors=errors)
