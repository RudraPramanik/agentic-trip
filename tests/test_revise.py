"""P6.3 revise_graph integration + runner proofs."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.modules.agents.generate import GenerateDeps, run_generate
from src.modules.agents.revise import ReviseDeps, run_revise
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine, Itinerary, pack_days
from src.modules.planner.types import Day, Stop
from src.modules.trips import TripService
from src.modules.trips.export import to_guidebook_export
from tests.fakes import FakeDialogueLlm, RecordingObs


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        return FetchResult(places=[])


class _InlineQueue:
    async def enqueue(self, session_id: str) -> str:
        return "job"


def _place(name: str, provider_id: str, lon: float, lat: float) -> PlaceRecord:
    return PlaceRecord(
        name=name,
        lon=lon,
        lat=lat,
        provider="t",
        provider_id=provider_id,
        country_code="jp",
        category="sight",
    )


def _many_places() -> list[PlaceRecord]:
    spots = [
        ("A", "a", 135.50, 34.50),
        ("B", "b", 135.51, 34.51),
        ("C", "c", 135.52, 34.52),
        ("D", "d", 135.53, 34.53),
        ("E", "e", 135.54, 34.54),
        ("F", "f", 135.55, 34.55),
        ("G", "g", 135.56, 34.56),
        ("H", "h", 135.57, 34.57),
    ]
    return [_place(n, i, lon, lat) for n, i, lon, lat in spots]


@pytest.fixture
async def revise_env():
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(_many_places())
    obs = RecordingObs()
    catalog = CatalogService(
        auth=CookieAuthAdapter(),
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

    generate = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=trips,
        llm=FakeDialogueLlm(structured={"days": []}),
        obs=obs,
        sessions_get=sessions.get,
    )
    deps = ReviseDeps(
        generate=generate,
        sessions_save=sessions.save,
        max_loops=3,
    )
    first = await run_generate(state.session_id, generate)
    assert first.status == "done"
    return sessions, deps, state.session_id, obs, trips


@pytest.mark.asyncio
async def test_run_revise_changes_day_2_structure(revise_env) -> None:
    sessions, deps, session_id, obs, trips = revise_env
    before = await sessions.get(session_id)
    assert before is not None and before.itinerary is not None
    before_day2 = [s["place_id"] for s in before.itinerary["days"][1]["stops"]]
    trip_id = before.trip_id

    result = await run_revise(session_id, "less walking day 2", deps)
    assert result.status == "done"
    after = await sessions.get(session_id)
    assert after is not None and after.itinerary is not None
    assert after.itinerary["status"] == "draft"
    assert after.trip_id == trip_id
    after_day2 = [s["place_id"] for s in after.itinerary["days"][1]["stops"]]
    assert len(after_day2) < len(before_day2) or after_day2 != before_day2
    ids = {s["place_id"] for d in after.itinerary["days"] for s in d["stops"]}
    assert all(isinstance(i, str) and i for i in ids)

    trip = await trips.get_trip(trip_id, after.guest_id)
    export = to_guidebook_export(trip)
    export_ids = {s.place_id for d in export.days for s in d.stops}
    assert export_ids == ids
    map_ids = {p.place_id for p in export.map_points}
    assert map_ids == ids
    assert "revise.caps" in obs.spans or "revise.parse" in obs.spans


@pytest.mark.asyncio
async def test_run_revise_validation_fail_keeps_last_valid(revise_env) -> None:
    sessions, deps, session_id, obs, _trips = revise_env
    before = await sessions.get(session_id)
    assert before is not None
    last = dict(before.itinerary or {})

    class BadEngine(GreedyTravelEngine):
        def pack(self, scope: Any, places: Any, prefs: Any) -> Itinerary:
            return Itinerary(
                days=[
                    Day(
                        day_index=1,
                        stops=[Stop(place_id="ghost-venue", name="Ghost")],
                    )
                ],
                status="draft",
            )

    deps.generate.engine = BadEngine()
    result = await run_revise(session_id, "less walking day 2", deps)
    assert result.status == "error"
    after = await sessions.get(session_id)
    assert after is not None
    assert after.itinerary == last


@pytest.mark.asyncio
async def test_run_revise_missing_draft() -> None:
    sessions = InMemorySessionRepository()
    state = await sessions.create(guest_id="g1")
    generate = GenerateDeps(
        catalog=CatalogService(
            auth=CookieAuthAdapter(),
            sessions=sessions,
            places=InMemoryPlaceRepository(),
            facade=FakeFacade(),
            queue=_InlineQueue(),  # type: ignore[arg-type]
            obs=NoOpObs(),
        ),
        engine=GreedyTravelEngine(),
        trips=TripService(sessions),
        llm=FakeDialogueLlm(),
        obs=RecordingObs(),
        sessions_get=sessions.get,
    )
    deps = ReviseDeps(generate=generate, sessions_save=sessions.save)
    result = await run_revise(state.session_id, "less walking day 2", deps)
    assert result.status == "error"
    assert result.error == "missing_draft"


@pytest.mark.asyncio
async def test_run_revise_loop_cap_traced(revise_env) -> None:
    sessions, deps, session_id, obs, _trips = revise_env
    deps.max_loops = 1
    first = await run_revise(session_id, "less walking day 2", deps)
    assert first.status in {"done", "error"}
    before = await sessions.get(session_id)
    assert before is not None
    last = dict(before.itinerary or {})
    second = await run_revise(session_id, "less walking day 2", deps)
    assert second.status == "error"
    assert second.error == "loop_cap"
    after = await sessions.get(session_id)
    assert after is not None
    assert after.itinerary == last
    assert any("revise.outcome" in s for s in obs.spans)


@pytest.mark.asyncio
async def test_runner_start_revise_progress_and_abort() -> None:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    await places.upsert_many(_many_places())
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "day_budget": 2,
    }
    state.intent = {"duration_days": 2}
    await sessions.save(state)

    catalog = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=_InlineQueue(),  # type: ignore[arg-type]
        obs=NoOpObs(),
    )
    generate = GenerateDeps(
        catalog=catalog,
        engine=GreedyTravelEngine(),
        trips=TripService(sessions),
        llm=FakeDialogueLlm(structured={"days": []}),
        obs=NoOpObs(),
        sessions_get=sessions.get,
    )
    first = await run_generate(state.session_id, generate)
    assert first.status == "done"

    gate = asyncio.Event()

    class SlowCatalog(CatalogService):
        async def retrieve(self, scope, prefs=None):
            await gate.wait()
            return await super().retrieve(scope, prefs)

    slow = SlowCatalog(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=_InlineQueue(),  # type: ignore[arg-type]
        obs=NoOpObs(),
    )
    last = dict((await sessions.get(state.session_id)).itinerary)  # type: ignore[arg-type]

    async def factory(_sid: str) -> ReviseDeps:
        gen = GenerateDeps(
            catalog=slow,
            engine=GreedyTravelEngine(),
            trips=TripService(sessions),
            llm=FakeDialogueLlm(),
            obs=NoOpObs(),
            sessions_get=sessions.get,
        )
        return ReviseDeps(generate=gen, sessions_save=sessions.save)

    runner = InProcessGenerateRunner(factory, timeout_seconds=30)

    async def consume() -> list[str]:
        events = []
        async for ev in runner.start_revise(state.session_id, "less walking day 2"):
            events.append(ev.event)
            if ev.event == "progress" and ev.data.get("stage") in {"retrieve", "parse", "caps"}:
                await runner.abort(state.session_id)
                gate.set()
        return events

    events = await consume()
    assert "progress" in events
    assert "aborted" in events or "error" in events
    final = await sessions.get(state.session_id)
    assert final is not None
    assert final.itinerary == last


def test_pack_day_overrides_used_by_engine() -> None:
    places = [
        {
            "id": f"p{i}",
            "name": f"P{i}",
            "lon": 135.5 + i * 0.01,
            "lat": 34.5 + i * 0.01,
            "country_code": "jp",
        }
        for i in range(8)
    ]
    base = pack_days({"day_budget": 2}, places, {"day_budget": 2})
    tight = pack_days(
        {"day_budget": 2},
        places,
        {"day_budget": 2, "day_overrides": {2: {"max_stops_per_day": 1}}},
    )
    assert len(tight.days[1].stops) <= 1
    assert len(tight.days[1].stops) <= len(base.days[1].stops)
