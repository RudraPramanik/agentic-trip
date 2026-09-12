from __future__ import annotations

from typing import Any

from src.modules.geo.types import GeoCandidate, NeedsHitl, TripIntent, TripScope

SHORT_COUNTRY_DAYS = 3

# Coarse default hubs when country metadata is thin (not catalog quality — P3 deepens).
_DEFAULT_COUNTRY_HUBS: dict[str, list[dict[str, Any]]] = {
    "jp": [
        {"name": "Tokyo", "geo_id": "hub:tokyo"},
        {"name": "Kyoto", "geo_id": "hub:kyoto"},
        {"name": "Osaka", "geo_id": "hub:osaka"},
    ],
    "japan": [
        {"name": "Tokyo", "geo_id": "hub:tokyo"},
        {"name": "Kyoto", "geo_id": "hub:kyoto"},
        {"name": "Osaka", "geo_id": "hub:osaka"},
    ],
}

_DEFAULT_BEST_REGION: dict[str, dict[str, Any]] = {
    "jp": {"name": "Kansai", "geo_id": "region:kansai"},
    "japan": {"name": "Kansai", "geo_id": "region:kansai"},
}


def classify_scope(
    intent: TripIntent, candidate: GeoCandidate
) -> TripScope | NeedsHitl:
    """Deterministic city/region/country from geo metadata first."""
    days = intent.duration_days
    place_class = _effective_place_class(candidate)
    named_cityish = place_class == "city"
    named_region = place_class == "region"

    # Named city or region always wins over best-region override.
    if named_cityish:
        return TripScope(
            kind="city",
            geo_id=candidate.geo_id,
            name=candidate.name,
            bbox=candidate.bbox,
            hubs=[],
            day_budget=days,
            explain=f"Planning around {candidate.name} as a city base.",
        )

    if named_region:
        return TripScope(
            kind="region",
            geo_id=candidate.geo_id,
            name=candidate.name,
            bbox=candidate.bbox,
            hubs=[],
            day_budget=days,
            explain=f"Planning within the {candidate.name} region.",
        )

    if place_class != "country":
        # Ambiguous metadata — HITL rather than silent centroid.
        return NeedsHitl(
            kind="place",
            candidates=[candidate.to_dict()],
            prompt=f"Is {candidate.display_name} the place you meant?",
        )

    # Country-scale
    key = (candidate.country_code or candidate.name or "").lower()
    if days is not None and days <= SHORT_COUNTRY_DAYS:
        best = _DEFAULT_BEST_REGION.get(key) or {
            "name": f"best region in {candidate.name}",
            "geo_id": f"region:best:{candidate.geo_id}",
        }
        return TripScope(
            kind="region",
            geo_id=str(best["geo_id"]),
            name=str(best["name"]),
            bbox=candidate.bbox,
            hubs=[best],
            day_budget=days,
            explain=(
                f"For a short {days}-day stay in {candidate.name}, "
                f"focusing on {best['name']} rather than a nationwide hop."
            ),
        )

    hubs = list(_DEFAULT_COUNTRY_HUBS.get(key) or [])
    if not hubs:
        # Thin country metadata — HITL for hub set (LLM hubs only later if thin).
        return NeedsHitl(
            kind="hubs",
            candidates=[
                {
                    "choice_id": "hubs_default",
                    "label": f"Suggest hubs for {candidate.name}",
                    "geo_id": candidate.geo_id,
                }
            ],
            prompt=(
                f"{candidate.name} is country-scale. "
                "Pick a hub set or tell me which cities to include."
            ),
        )

    return TripScope(
        kind="country",
        geo_id=candidate.geo_id,
        name=candidate.name,
        bbox=candidate.bbox,
        hubs=hubs,
        day_budget=days,
        explain=(
            f"Country stay in {candidate.name} with hubs: "
            + ", ".join(h["name"] for h in hubs)
        ),
    )


def _effective_place_class(candidate: GeoCandidate) -> str:
    if candidate.place_class in {"city", "region", "country"}:
        return candidate.place_class
    bbox = candidate.bbox
    if bbox and len(bbox) == 4:
        span = max(abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1]))
        if span > 8:
            return "country"
        if span > 1.5:
            return "region"
        return "city"
    if candidate.admin_level is not None:
        if candidate.admin_level <= 2:
            return "country"
        if candidate.admin_level <= 5:
            return "region"
        return "city"
    return "other"
