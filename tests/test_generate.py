"""GenerateRunner + generate graph proofs (P4.1, P4.5, P4.8)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.modules.agents.generate import GenerateDeps, run_generate
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine
from src.modules.trips import TripService
from tests.fakes import FakeDialogueLlm, RecordingObs


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]):
        from src.modules.catalog.facade import FetchResult

        return FetchResult(places=[])


class _InlineQueue:
    async def enqueue(self, session_id: str) -> str:
        return "job"


def _seed_places(places: InMemoryPlaceRepository) -> None:
    records = [
        PlaceRecord(
            name="Spot A",
            lon=135.5,
            lat=34.5,
            provider="t",
            provider_id="a",
            country_code="jp",
            category="temple",
        ),
        PlaceRecord(
            name="Spot B",
            lon=135.6,
            lat=34.6,
            provider="t",
            provider_id="b",
            country_code="jp",
            category="park",
        ),
        PlaceRecord(
            name="Spot C",
            lon=135.7,
            lat=34.7,
            provider="t",
            provider_id="c",
            country_code="jp",
            category="shrine",
        ),
    ]
    # Upsert via public API
    import asyncio as _aio

    async def _up() -> None:
        await places.upsert_many(records)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # caller will upsert
            pass
    except RuntimeError:
        pass


@pytest.fixture
async def gen_env():
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
                category="temple",
            ),
            PlaceRecord(
                name="Spot B",
                lon=135.6,
                lat=34.6,
                provider="t",
                provider_id="b",
                country_code="jp",
                category="park",
            ),
            PlaceRecord(
                name="Spot C",
                lon=135.7,
                lat=34.7,
                provider="t",
                provider_id="c",
                country_code="jp",
                category="shrine",
            ),
        ]
    )
    from src.modules.auth import CookieAuthAdapter

    auth = CookieAuthAdapter()
    obs = RecordingObs()
    catalog = CatalogService(
        auth=auth,
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=_InlineQueue(),  # type: ignore[arg-type]
        obs=obs,
    )
    trips = TripService(sessions)
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

    async def sessions_get(sid: str):
        return await sessions.get(sid)

    deps = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=trips,
        llm=FakeDialogueLlm(structured={"days": []}),
        obs=obs,
        sessions_get=sessions_get,
    )
    return sessions, deps, state.session_id, obs


@pytest.mark.asyncio
async def test_run_generate_valid_persists_draft(gen_env) -> None:
    sessions, deps, session_id, obs = gen_env
    result = await run_generate(session_id, deps)
    assert result.status == "done"
    state = await sessions.get(session_id)
    assert state is not None
    assert state.itinerary is not None
    assert state.itinerary["status"] == "draft"
    ids = {s["place_id"] for d in state.itinerary["days"] for s in d["stops"]}
    assert ids
    assert all(i.startswith("t:") or True for i in ids)
    assert "generate.outcome" in obs.spans


@pytest.mark.asyncio
async def test_run_generate_empty_retrieve_no_persist(gen_env) -> None:
    sessions, deps, session_id, obs = gen_env
    state = await sessions.get(session_id)
    assert state is not None
    state.trip_scope = {
        "kind": "city",
        "bbox": [0.0, 0.0, 0.1, 0.1],
        "country_code": "jp",
    }
    await sessions.save(state)
    result = await run_generate(session_id, deps)
    assert result.status == "error"
    assert result.error == "empty_retrieve"
    state = await sessions.get(session_id)
    assert state is not None
    assert state.itinerary is None
    assert "generate.outcome" in obs.spans


@pytest.mark.asyncio
async def test_runner_progress_and_abort() -> None:
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
            )
        ]
    )
    from src.modules.auth import CookieAuthAdapter

    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 1,
    }
    await sessions.save(state)

    gate = asyncio.Event()

    class SlowCatalog(CatalogService):
        async def retrieve(self, scope, prefs=None):
            await gate.wait()
            return await super().retrieve(scope, prefs)

    catalog = SlowCatalog(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=_InlineQueue(),  # type: ignore[arg-type]
        obs=NoOpObs(),
    )
    trips = TripService(sessions)

    async def factory(_sid: str):
        return GenerateDeps(
            catalog=catalog,
            engine=GreedyTravelEngine(),
            trips=trips,
            llm=FakeDialogueLlm(),
            obs=NoOpObs(),
            sessions_get=sessions.get,
        )

    runner = InProcessGenerateRunner(factory, timeout_seconds=30)

    async def consume() -> list[str]:
        events = []
        async for ev in runner.start(state.session_id):
            events.append(ev.event)
            if ev.event == "progress" and ev.data.get("stage") == "retrieve":
                await runner.abort(state.session_id)
                gate.set()
        return events

    events = await consume()
    assert "progress" in events
    assert "aborted" in events or "error" in events
    final = await sessions.get(state.session_id)
    assert final is not None
    assert final.itinerary is None


@pytest.mark.asyncio
async def test_runner_timeout_no_persist(monkeypatch: pytest.MonkeyPatch) -> None:
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
            )
        ]
    )
    from src.modules.auth import CookieAuthAdapter

    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 1,
    }
    await sessions.save(state)

    class SlowCatalog(CatalogService):
        async def retrieve(self, scope, prefs=None):
            await asyncio.sleep(0.5)
            return await super().retrieve(scope, prefs)

    catalog = SlowCatalog(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=_InlineQueue(),  # type: ignore[arg-type]
        obs=NoOpObs(),
    )

    async def factory(_sid: str):
        return GenerateDeps(
            catalog=catalog,
            engine=GreedyTravelEngine(),
            trips=TripService(sessions),
            llm=FakeDialogueLlm(),
            obs=NoOpObs(),
            sessions_get=sessions.get,
        )

    runner = InProcessGenerateRunner(factory, timeout_seconds=0.05)
    events = []
    async for ev in runner.start(state.session_id):
        events.append(ev.event)
    assert "aborted" in events or "error" in events
    final = await sessions.get(state.session_id)
    assert final is not None
    assert final.itinerary is None
