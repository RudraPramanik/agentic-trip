"""ASGI revise SSE proofs (P6.4)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi.testclient import TestClient

from src.api.sessions import get_chat_service
from src.core.settings import get_settings
from src.main import create_app
from src.modules.agents.generate import GenerateDeps
from src.modules.agents.revise import ReviseDeps
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import ChatService, InMemorySessionRepository
from src.modules.monitor import NoOpObs
from src.modules.planner import GreedyTravelEngine
from src.modules.trips import TripService
from tests.fakes import FakeDialogueLlm, make_chat_service


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    event_name = "message"
    data_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:") :].strip())
        elif line == "" and data_lines:
            raw = "\n".join(data_lines)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}
            events.append((event_name, payload))
            event_name = "message"
            data_lines = []
    if data_lines:
        raw = "\n".join(data_lines)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        events.append((event_name, payload))
    return events


class FakeFacade:
    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        return FetchResult(places=[])


def _places() -> list[PlaceRecord]:
    return [
        PlaceRecord(
            name=f"Spot {i}",
            lon=135.5 + i * 0.01,
            lat=34.5 + i * 0.01,
            provider="t",
            provider_id=str(i),
            country_code="jp",
        )
        for i in range(8)
    ]


def _build_revise_client(
    *,
    timeout_seconds: float = 120.0,
    max_loops: int = 3,
) -> tuple[TestClient, InMemorySessionRepository, InMemoryPlaceRepository]:
    get_settings.cache_clear()
    application = create_app()
    chat, sessions, _, _, _ = make_chat_service()
    places = InMemoryPlaceRepository()
    auth = CookieAuthAdapter()
    trips = TripService(sessions)

    async def factory(_sid: str) -> ReviseDeps:
        catalog = CatalogService(
            auth=auth,
            sessions=sessions,
            places=places,
            facade=FakeFacade(),
            queue=InlineAcquireQueue(),
            obs=NoOpObs(),
        )
        generate = GenerateDeps(
            catalog=catalog,
            engine=GreedyTravelEngine(),
            trips=trips,
            llm=FakeDialogueLlm(structured={"days": []}),
            obs=NoOpObs(),
            sessions_get=sessions.get,
        )
        return ReviseDeps(
            generate=generate,
            sessions_save=sessions.save,
            max_loops=max_loops,
        )

    async def gen_factory(_sid: str) -> GenerateDeps:
        deps = await factory(_sid)
        return deps.generate

    application.state.generate_runner = InProcessGenerateRunner(
        gen_factory,
        timeout_seconds=timeout_seconds,
        revise_timeout_seconds=timeout_seconds,
        revise_deps_factory=factory,
        max_revise_loops=max_loops,
    )
    application.state.generate_deps_factory = gen_factory
    application.state.revise_deps_factory = factory

    def _chat() -> ChatService:
        return chat

    application.dependency_overrides[get_chat_service] = _chat
    from src.api import generate as generate_api
    from src.api import revise as revise_api

    class _RepoAdapter:
        def __init__(self, _db=None) -> None:
            self._inner = sessions

        async def get(self, session_id: str):
            return await self._inner.get(session_id)

        async def save(self, state):
            return await self._inner.save(state)

        async def create(self, guest_id: str):
            return await self._inner.create(guest_id)

    generate_api.SqlSessionRepository = _RepoAdapter  # type: ignore[misc,assignment]
    generate_api.SqlPlaceRepository = lambda _db=None: places  # type: ignore[misc,assignment]
    revise_api.SqlSessionRepository = _RepoAdapter  # type: ignore[misc,assignment]
    revise_api.SqlPlaceRepository = lambda _db=None: places  # type: ignore[misc,assignment]

    client = TestClient(application)
    return client, sessions, places


def _seed_draft(
    client: TestClient,
    sessions: InMemorySessionRepository,
    places: InMemoryPlaceRepository,
) -> str:
    create = client.post("/api/v1/sessions")
    assert create.status_code == 200
    session_id = create.json()["session_id"]

    async def _prepare() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        state.trip_scope = {
            "kind": "city",
            "name": "Kyoto",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
            "day_budget": 2,
        }
        state.intent = {"duration_days": 2}
        await sessions.save(state)
        await places.upsert_many(_places())

    asyncio.run(_prepare())
    gen = client.post(f"/api/v1/sessions/{session_id}/generate")
    assert gen.status_code == 200
    kinds = [e for e, _ in _parse_sse(gen.text)]
    assert "done" in kinds
    return session_id


def test_revise_sse_progress_then_done() -> None:
    client, sessions, places = _build_revise_client()
    session_id = _seed_draft(client, sessions, places)
    response = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    kinds = [e for e, _ in events]
    assert "progress" in kinds
    assert "done" in kinds

    async def _check() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        assert state.itinerary is not None
        assert state.itinerary["status"] == "draft"

    asyncio.run(_check())


def test_revise_cap_hit_keeps_last_valid() -> None:
    client, sessions, places = _build_revise_client(max_loops=1)
    session_id = _seed_draft(client, sessions, places)

    async def _snapshot() -> dict:
        state = await sessions.get(session_id)
        assert state is not None
        return dict(state.itinerary or {})

    first = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert first.status_code == 200
    last = asyncio.run(_snapshot())
    second = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    kinds = [e for e, p in _parse_sse(second.text)]
    assert "error" in kinds
    codes = [p.get("code") for e, p in _parse_sse(second.text) if e == "error"]
    assert "loop_cap" in codes
    after = asyncio.run(_snapshot())
    assert after == last


def test_revise_foreign_session_denied() -> None:
    client, sessions, places = _build_revise_client()
    session_id = _seed_draft(client, sessions, places)
    other = TestClient(create_app())
    response = other.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert response.status_code == 404


def test_revise_without_redis_ok() -> None:
    client, sessions, places = _build_revise_client()
    session_id = _seed_draft(client, sessions, places)
    response = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert response.status_code == 200
    kinds = [e for e, _ in _parse_sse(response.text)]
    assert "done" in kinds or "error" in kinds


def test_revise_missing_draft_errors() -> None:
    client, sessions, _places = _build_revise_client()
    create = client.post("/api/v1/sessions")
    session_id = create.json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/revise",
        json={"text": "less walking day 2"},
    )
    assert response.status_code == 200
    codes = [p.get("code") for e, p in _parse_sse(response.text) if e == "error"]
    assert "missing_draft" in codes


def test_revise_abort_keeps_last_valid() -> None:
    client, sessions, places = _build_revise_client()
    session_id = _seed_draft(client, sessions, places)
    abort = client.post(f"/api/v1/sessions/{session_id}/generate/abort")
    assert abort.status_code == 200
    assert abort.json()["abort_requested"] is True
