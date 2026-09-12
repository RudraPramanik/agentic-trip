"""TripService + GuidebookExport proofs (P4.7 / P5.1–P5.2)."""

from __future__ import annotations

import pytest

from src.modules.chat import InMemorySessionRepository
from src.modules.media import StubMediaProvider
from src.modules.planner import Day, Itinerary, Stop, ValidateResult
from src.modules.trips import (
    TripAccessError,
    TripPersistError,
    TripService,
    to_guidebook_export,
)
from src.modules.trips.repository import InMemoryTripRepository


def _sample_itin() -> Itinerary:
    return Itinerary(
        days=[
            Day(
                day_index=1,
                title="Day one",
                story="Walk the hills.",
                stops=[
                    Stop(
                        place_id="p1",
                        name="Living Root Bridge",
                        lon=91.0,
                        lat=25.0,
                        country_code="in",
                    )
                ],
            )
        ],
        status="draft",
        place_ids=["p1"],
    )


@pytest.mark.asyncio
async def test_persist_draft_success_assigns_trip_id() -> None:
    sessions = InMemorySessionRepository()
    trip_repo = InMemoryTripRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions, trip_repo)
    saved = await trips.persist_draft(
        created.session_id, _sample_itin(), ValidateResult(ok=True)
    )
    assert saved.itinerary is not None
    assert saved.itinerary["status"] == "draft"
    assert saved.itinerary.get("saved") is False
    assert saved.itinerary.get("unlocks_last_trip") is False
    assert TripService.LAST_TRIP_UNLOCKED_BY_DRAFT is False
    assert saved.trip_id is not None
    artifact = await trip_repo.get(saved.trip_id)
    assert artifact is not None
    assert artifact.guest_id == "g1"


@pytest.mark.asyncio
async def test_persist_draft_refuses_validation_fail() -> None:
    sessions = InMemorySessionRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions)
    with pytest.raises(TripPersistError):
        await trips.persist_draft(
            created.session_id,
            Itinerary(days=[]),
            ValidateResult(ok=False, errors=["unknown_venue:x"]),
        )
    state = await sessions.get(created.session_id)
    assert state is not None
    assert state.itinerary is None
    assert state.trip_id is None


@pytest.mark.asyncio
async def test_persist_draft_refuses_abort() -> None:
    sessions = InMemorySessionRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions)
    with pytest.raises(TripPersistError):
        await trips.persist_draft(
            created.session_id,
            Itinerary(days=[]),
            ValidateResult(ok=True),
            aborted=True,
        )


@pytest.mark.asyncio
async def test_get_trip_owner_and_foreign() -> None:
    sessions = InMemorySessionRepository()
    trip_repo = InMemoryTripRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions, trip_repo)
    saved = await trips.persist_draft(
        created.session_id, _sample_itin(), ValidateResult(ok=True)
    )
    assert saved.trip_id
    got = await trips.get_trip(saved.trip_id, "g1")
    assert got["trip_id"] == saved.trip_id
    assert got["itinerary"]["days"][0]["stops"][0]["place_id"] == "p1"
    with pytest.raises(TripAccessError):
        await trips.get_trip(saved.trip_id, "other-guest")


@pytest.mark.asyncio
async def test_export_guidebook_schema_no_invented_ids() -> None:
    sessions = InMemorySessionRepository()
    trip_repo = InMemoryTripRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions, trip_repo)
    saved = await trips.persist_draft(
        created.session_id, _sample_itin(), ValidateResult(ok=True)
    )
    assert saved.trip_id
    export = await trips.export_guidebook(saved.trip_id, "g1")
    data = export.to_dict()
    assert data["trip_id"] == saved.trip_id
    assert "cover" in data and "days" in data and "map_points" in data
    assert "narratives" in data and "hubs" in data
    assert data["cover"]["day_count"] == 1
    assert data["days"][0]["stops"][0]["place_id"] == "p1"
    assert data["map_points"][0]["place_id"] == "p1"
    assert "route_geometry" not in data  # v1 points-only


def test_to_guidebook_export_does_not_invent_coords() -> None:
    trip = {
        "trip_id": "t1",
        "itinerary": {
            "status": "draft",
            "days": [
                {
                    "day_index": 1,
                    "stops": [{"place_id": "p1", "name": "A"}],  # no lon/lat
                }
            ],
        },
    }
    export = to_guidebook_export(trip)
    assert export.days[0].stops[0].place_id == "p1"
    assert export.map_points == []
    assert export.route_geometry is None


@pytest.mark.asyncio
async def test_media_stub_empty_and_unused_by_contract() -> None:
    media = StubMediaProvider()
    assert await media.get_place_media("p1") == []
