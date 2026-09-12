"""Unit proofs for planner matrix, pack, validate (P4.1–P4.4)."""

from __future__ import annotations

from src.modules.planner import (
    Day,
    GreedyTravelEngine,
    Itinerary,
    Stop,
    haversine_meters,
    pack_days,
    travel_matrix,
    validate_itinerary,
)


def _places_jp() -> list[dict]:
    return [
        {
            "id": "jp-1",
            "name": "Fushimi Inari",
            "lon": 135.77,
            "lat": 34.97,
            "country_code": "jp",
            "category": "shrine",
            "tags": ["temple"],
        },
        {
            "id": "jp-2",
            "name": "Kiyomizu",
            "lon": 135.78,
            "lat": 34.99,
            "country_code": "jp",
            "category": "temple",
            "tags": ["temple"],
        },
        {
            "id": "jp-3",
            "name": "Arashiyama",
            "lon": 135.67,
            "lat": 35.01,
            "country_code": "jp",
            "category": "nature",
            "tags": ["park"],
        },
        {
            "id": "jp-4",
            "name": "Nara Park",
            "lon": 135.84,
            "lat": 34.68,
            "country_code": "jp",
            "category": "park",
            "tags": ["park"],
        },
    ]


def test_haversine_finite() -> None:
    d = haversine_meters((135.0, 35.0), (135.1, 35.1))
    assert d > 0
    assert d < 50_000


def test_travel_matrix_no_osrm_finite_no_geometry() -> None:
    result = travel_matrix(_places_jp())
    assert result["source"] == "haversine"
    assert result["geometry"] is None
    matrix = result["durations_seconds"]
    assert len(matrix) == 4
    assert all(isinstance(v, float) and v == v for row in matrix for v in row)
    assert "LineString" not in str(result)
    assert "polyline" not in str(result).lower()


def test_pack_days_catalog_only_and_day_budget() -> None:
    scope = {"kind": "city", "country_code": "jp", "day_budget": 2}
    itin = pack_days(scope, _places_jp(), {"day_budget": 2})
    assert len(itin.days) == 2
    ids = {s.place_id for d in itin.days for s in d.stops}
    assert ids.issubset({"jp-1", "jp-2", "jp-3", "jp-4"})
    assert all(s.place_id.startswith("jp-") for d in itin.days for s in d.stops)


def test_greedy_engine_pack() -> None:
    engine = GreedyTravelEngine()
    itin = engine.pack(
        {"country_code": "jp", "day_budget": 3},
        _places_jp(),
        {"day_budget": 3},
    )
    assert isinstance(itin, Itinerary)
    assert len(itin.days) == 3


def test_validate_unknown_venue_fails() -> None:
    itin = Itinerary(
        days=[Day(day_index=1, stops=[Stop(place_id="ghost", country_code="jp")])],
        status="draft",
    )
    result = validate_itinerary(itin, {"jp-1"}, {"country_code": "jp"})
    assert not result.ok
    assert any("unknown_venue" in e for e in result.errors)


def test_validate_foreign_poi_fails() -> None:
    itin = Itinerary(
        days=[
            Day(
                day_index=1,
                stops=[Stop(place_id="jp-1", country_code="kr")],
            )
        ]
    )
    result = validate_itinerary(
        itin, {"jp-1"}, {"country_code": "jp"}, place_countries={"jp-1": "kr"}
    )
    assert not result.ok
    assert any("foreign_poi" in e for e in result.errors)


def test_validate_day_cap_fails() -> None:
    itin = Itinerary(
        days=[
            Day(day_index=1, stops=[Stop(place_id="jp-1", country_code="jp")]),
            Day(day_index=2, stops=[Stop(place_id="jp-2", country_code="jp")]),
            Day(day_index=3, stops=[Stop(place_id="jp-3", country_code="jp")]),
        ]
    )
    result = validate_itinerary(
        itin,
        {"jp-1", "jp-2", "jp-3"},
        {"country_code": "jp"},
        day_budget=2,
    )
    assert not result.ok
    assert "day_cap_exceeded" in result.errors
