"""TripService.persist_draft proofs (P4.7)."""

from __future__ import annotations

import pytest

from src.modules.chat import InMemorySessionRepository
from src.modules.planner import Day, Itinerary, Stop, ValidateResult
from src.modules.trips import TripPersistError, TripService


@pytest.mark.asyncio
async def test_persist_draft_success() -> None:
    sessions = InMemorySessionRepository()
    created = await sessions.create(guest_id="g1")
    trips = TripService(sessions)
    itin = Itinerary(
        days=[Day(day_index=1, stops=[Stop(place_id="p1", name="A", country_code="jp")])],
        status="draft",
        place_ids=["p1"],
    )
    saved = await trips.persist_draft(
        created.session_id, itin, ValidateResult(ok=True)
    )
    assert saved.itinerary is not None
    assert saved.itinerary["status"] == "draft"
    assert saved.itinerary.get("saved") is False
    assert saved.itinerary.get("unlocks_last_trip") is False
    assert TripService.LAST_TRIP_UNLOCKED_BY_DRAFT is False


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
