"""Media stub stays off generate hot path (P5.6)."""

from __future__ import annotations

from typing import Any

import pytest

from src.modules.agents.generate import GenerateDeps, run_generate
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.modules.media import StubMediaProvider
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine
from src.modules.trips import TripService
from src.modules.trips.repository import InMemoryTripRepository
from tests.fakes import FakeDialogueLlm, RecordingObs
from src.modules.auth import CookieAuthAdapter


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        return FetchResult(places=[])


class SpyMedia(StubMediaProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def get_place_media(self, place_id: str) -> list[dict[str, Any]]:
        self.calls += 1
        return await super().get_place_media(place_id)


@pytest.mark.asyncio
async def test_media_stub_empty() -> None:
    assert await StubMediaProvider().get_place_media("any") == []


@pytest.mark.asyncio
async def test_generate_does_not_call_media() -> None:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(
        [
            PlaceRecord(
                name="Spot A",
                lon=135.5,
                lat=34.5,
                provider="t",
                provider_id="a",
                country_code="jp",
                category="park",
            ),
            PlaceRecord(
                name="Spot B",
                lon=135.6,
                lat=34.6,
                provider="t",
                provider_id="b",
                country_code="jp",
                category="cafe",
            ),
        ]
    )
    catalog = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=InlineAcquireQueue(),
        obs=NoOpObs(),
    )
    trips = TripService(sessions, InMemoryTripRepository())
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "name": "Kyoto",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 2,
    }
    state.intent = {"duration_days": 2}
    await sessions.save(state)

    media = SpyMedia()
    result = await run_generate(
        state.session_id,
        GenerateDeps(
            catalog=catalog,
            engine=GreedyTravelEngine(),
            trips=trips,
            llm=FakeDialogueLlm(structured={"days": []}),
            obs=RecordingObs(),
            sessions_get=sessions.get,
        ),
    )
    assert result.status == "done"
    assert result.trip_id is not None
    # Media is never a GenerateDeps field and was never invoked.
    assert media.calls == 0
    assert "media" not in GenerateDeps.__dataclass_fields__
