"""P6.5 less-walking-day-2 golden + failed/capped revise still traced."""

from __future__ import annotations

from typing import Any

import pytest

from src.modules.agents.generate import GenerateDeps, run_generate
from src.modules.agents.revise import ReviseDeps, run_revise
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine, Itinerary
from src.modules.planner.types import Day, Stop
from src.modules.trips import TripService
from tests.fakes import FakeDialogueLlm, RecordingObs


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        return FetchResult(places=[])


def _kyoto_cluster() -> list[PlaceRecord]:
    spots = [
        ("Fushimi Inari", 135.77, 34.97),
        ("Kiyomizu", 135.78, 34.99),
        ("Gion", 135.77, 35.00),
        ("Nijo", 135.75, 35.01),
        ("Arashiyama", 135.67, 35.01),
        ("Bamboo Grove", 135.67, 35.02),
        ("Kinkakuji", 135.73, 35.04),
        ("Philosopher Path", 135.80, 35.03),
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
        )
        for i, (name, lon, lat) in enumerate(spots)
    ]


async def _seed() -> tuple[InMemorySessionRepository, ReviseDeps, str, RecordingObs]:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(_kyoto_cluster())
    obs = RecordingObs()
    catalog = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=InlineAcquireQueue(),
        obs=obs,
    )
    state = await sessions.create(guest_id="golden")
    state.trip_scope = {
        "kind": "city",
        "name": "Kyoto",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 2,
    }
    state.intent = {"duration_days": 2}
    await sessions.save(state)
    generate = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=TripService(sessions),
        llm=FakeDialogueLlm(structured={"days": []}),
        obs=obs,
        sessions_get=sessions.get,
    )
    first = await run_generate(state.session_id, generate)
    assert first.status == "done"
    deps = ReviseDeps(generate=generate, sessions_save=sessions.save, max_loops=3)
    return sessions, deps, state.session_id, obs


@pytest.mark.asyncio
async def test_golden_less_walking_day_2_updates_structure() -> None:
    sessions, deps, session_id, _obs = await _seed()
    before = await sessions.get(session_id)
    assert before is not None and before.itinerary is not None
    before_d2 = before.itinerary["days"][1]["stops"]
    result = await run_revise(session_id, "less walking day 2", deps)
    assert result.status == "done"
    after = await sessions.get(session_id)
    assert after is not None and after.itinerary is not None
    after_d2 = after.itinerary["days"][1]["stops"]
    assert len(after_d2) <= len(before_d2)
    assert len(after_d2) <= 2
    ids = {s["place_id"] for d in after.itinerary["days"] for s in d["stops"]}
    assert all(i.startswith("golden:") for i in ids)
    assert after.itinerary["status"] == "draft"


@pytest.mark.asyncio
async def test_golden_validation_required_to_persist() -> None:
    sessions, deps, session_id, obs = await _seed()
    before = await sessions.get(session_id)
    assert before is not None
    last = dict(before.itinerary or {})

    class BadEngine(GreedyTravelEngine):
        def pack(self, scope: Any, places: Any, prefs: Any) -> Itinerary:
            return Itinerary(
                days=[Day(day_index=1, stops=[Stop(place_id="ghost", name="Ghost")])],
                status="draft",
            )

    deps.generate.engine = BadEngine()
    result = await run_revise(session_id, "less walking day 2", deps)
    assert result.status == "error"
    after = await sessions.get(session_id)
    assert after is not None
    assert after.itinerary == last
    assert any("outcome" in s for s in obs.spans)


@pytest.mark.asyncio
async def test_golden_capped_revise_still_traced() -> None:
    sessions, deps, session_id, obs = await _seed()
    deps.max_loops = 0
    # loop already 0; bump makes attempt 1 > 0
    before = await sessions.get(session_id)
    last = dict(before.itinerary or {})  # type: ignore[union-attr]
    result = await run_revise(session_id, "less walking day 2", deps)
    assert result.status == "error"
    assert result.error == "loop_cap"
    after = await sessions.get(session_id)
    assert after is not None
    assert after.itinerary == last
    assert "revise.outcome" in obs.spans


@pytest.mark.asyncio
async def test_golden_unconfigured_obs_noops() -> None:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(_kyoto_cluster())
    catalog = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=InlineAcquireQueue(),
        obs=NoOpObs(),
    )
    state = await sessions.create(guest_id="golden")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 2,
    }
    state.intent = {"duration_days": 2}
    await sessions.save(state)
    generate = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=TripService(sessions),
        llm=FakeDialogueLlm(structured={"days": []}),
        obs=NoOpObs(),
        sessions_get=sessions.get,
    )
    assert (await run_generate(state.session_id, generate)).status == "done"
    deps = ReviseDeps(generate=generate, sessions_save=sessions.save)
    result = await run_revise(state.session_id, "less walking day 2", deps)
    assert result.status in {"done", "error"}
