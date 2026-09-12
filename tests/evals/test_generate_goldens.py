"""Generate goldens — Meghalaya/Japan-shaped, hub sequence, border, abort, traces (P4.10)."""

from __future__ import annotations

from typing import Any

import pytest

from src.modules.agents.generate import GenerateDeps, run_generate
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.modules.monitor import NoOpObs
from src.modules.planner import (
    Day,
    GreedyTravelEngine,
    Itinerary,
    Stop,
    pack_days,
    validate_itinerary,
)
from src.modules.trips import TripService
from tests.fakes import FakeDialogueLlm, RecordingObs, meghalaya_region


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        return FetchResult(places=[])


def _meghalaya_places() -> list[PlaceRecord]:
    # Rough Meghalaya bbox cluster (IN)
    base = [
        ("Living Root Bridge", 91.75, 25.25),
        ("Cherrapunji", 91.72, 25.28),
        ("Shillong Peak", 91.88, 25.54),
        ("Umiam Lake", 91.90, 25.65),
        ("Dawki", 92.02, 25.18),
        ("Mawlynnong", 91.92, 25.20),
    ]
    return [
        PlaceRecord(
            name=name,
            lon=lon,
            lat=lat,
            provider="golden",
            provider_id=str(i),
            country_code="in",
            category="nature",
        )
        for i, (name, lon, lat) in enumerate(base)
    ]


def _japan_places() -> list[PlaceRecord]:
    # Tokyo + Kyoto style hubs
    spots = [
        ("Sensoji", 139.80, 35.71, "tokyo"),
        ("Meiji Shrine", 139.70, 35.68, "tokyo"),
        ("Tokyo Skytree", 139.81, 35.71, "tokyo"),
        ("Fushimi Inari", 135.77, 34.97, "kyoto"),
        ("Kiyomizu", 135.78, 34.99, "kyoto"),
        ("Arashiyama", 135.67, 35.01, "kyoto"),
        ("Osaka Castle", 135.53, 34.69, "osaka"),
        ("Dotonbori", 135.50, 34.67, "osaka"),
    ]
    return [
        PlaceRecord(
            name=name,
            lon=lon,
            lat=lat,
            provider="golden",
            provider_id=str(i),
            country_code="jp",
            category="sight",
            tags=[hub],
        )
        for i, (name, lon, lat, hub) in enumerate(spots)
    ]


@pytest.mark.asyncio
async def test_golden_meghalaya_catalog_only_days() -> None:
    places_repo = InMemoryPlaceRepository()
    await places_repo.upsert_many(_meghalaya_places())
    records = await places_repo.retrieve(
        {
            "bbox": list(meghalaya_region().bbox),
            "country_code": "in",
        },
        None,
    )
    place_dicts = [r.to_dict() for r in records]
    scope = {
        "kind": "region",
        "name": "Meghalaya",
        "country_code": "in",
        "bbox": list(meghalaya_region().bbox),
        "day_budget": 4,
    }
    itin = pack_days(scope, place_dicts, {"day_budget": 4})
    assert len(itin.days) == 4
    catalog_ids = {str(p["id"]) for p in place_dicts}
    assert itin.stop_place_ids().issubset(catalog_ids)
    result = validate_itinerary(
        itin,
        catalog_ids,
        scope,
        day_budget=4,
        place_countries={str(p["id"]): p.get("country_code") for p in place_dicts},
    )
    assert result.ok


@pytest.mark.asyncio
async def test_golden_japan_shaped_and_ten_day_hubs() -> None:
    places_repo = InMemoryPlaceRepository()
    await places_repo.upsert_many(_japan_places())
    # Tag places with hub_id via retrieve + manual annotation for packer
    records = await places_repo.retrieve(
        {"bbox": [129.0, 30.0, 146.0, 46.0], "country_code": "jp"},
        None,
    )
    place_dicts = []
    for r in records:
        d = r.to_dict()
        tags = d.get("tags") or []
        if tags:
            d["hub_id"] = f"hub:{tags[0]}"
        place_dicts.append(d)

    hubs = [
        {
            "geo_id": "hub:tokyo",
            "name": "Tokyo",
            "bbox": [139.5, 35.5, 140.0, 35.9],
        },
        {
            "geo_id": "hub:kyoto",
            "name": "Kyoto",
            "bbox": [135.5, 34.8, 136.0, 35.2],
        },
        {
            "geo_id": "hub:osaka",
            "name": "Osaka",
            "bbox": [135.3, 34.5, 135.7, 34.8],
        },
    ]
    scope = {
        "kind": "country",
        "name": "Japan",
        "country_code": "jp",
        "day_budget": 10,
        "hubs": hubs,
        "bbox": [129.0, 30.0, 146.0, 46.0],
    }
    itin = pack_days(scope, place_dicts, {"day_budget": 10})
    assert len(itin.days) == 10
    # Hub sequence: days should reference hubs (Japan-10-days-or-HITL path = hubs present)
    hub_ids = {d.hub_id for d in itin.days if d.hub_id}
    assert len(hub_ids) >= 2
    catalog_ids = {str(p["id"]) for p in place_dicts}
    assert itin.stop_place_ids().issubset(catalog_ids)


def test_golden_border_country_filter() -> None:
    itin = Itinerary(
        days=[
            Day(
                day_index=1,
                stops=[
                    Stop(place_id="in-1", country_code="in"),
                    Stop(place_id="bd-1", country_code="bd"),  # Bangladesh near Meghalaya
                ],
            )
        ]
    )
    result = validate_itinerary(
        itin,
        {"in-1", "bd-1"},
        {"country_code": "in"},
        place_countries={"in-1": "in", "bd-1": "bd"},
    )
    assert not result.ok
    assert any("foreign_poi" in e for e in result.errors)


@pytest.mark.asyncio
async def test_golden_abandoned_generate_and_failed_traced() -> None:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(_japan_places()[:3])
    obs = RecordingObs()
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 140.0, 36.0],
        "country_code": "jp",
        "day_budget": 2,
    }
    await sessions.save(state)

    catalog = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=InlineAcquireQueue(),
        obs=obs,
    )
    deps = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=TripService(sessions),
        llm=FakeDialogueLlm(),
        obs=obs,
        sessions_get=sessions.get,
    )

    # Abandoned via abort_check
    result = await run_generate(
        state.session_id, deps, abort_check=lambda: True
    )
    assert result.status == "aborted"
    final = await sessions.get(state.session_id)
    assert final is not None
    assert final.itinerary is None

    # Failed empty retrieve still traced
    state.trip_scope = {
        "kind": "city",
        "bbox": [0.0, 0.0, 0.1, 0.1],
        "country_code": "jp",
    }
    await sessions.save(state)
    failed = await run_generate(state.session_id, deps)
    assert failed.status == "error"
    assert "generate.outcome" in obs.spans or "generate.run" in obs.traces
