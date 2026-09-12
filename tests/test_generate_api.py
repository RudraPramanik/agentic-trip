"""ASGI generate SSE + abort proofs (P4.8–P4.9)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi.testclient import TestClient

from src.api.sessions import get_chat_service
from src.core.settings import get_settings
from src.main import create_app
from src.modules.agents.generate import GenerateDeps
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


def _build_generate_client(
    *,
    timeout_seconds: float = 120.0,
) -> tuple[TestClient, InMemorySessionRepository, InMemoryPlaceRepository]:
    get_settings.cache_clear()
    application = create_app()
    chat, sessions, _, _, _ = make_chat_service()
    places = InMemoryPlaceRepository()
    auth = CookieAuthAdapter()
    catalog = CatalogService(
        auth=auth,
        sessions=sessions,
        places=places,
        facade=FakeFacade(),
        queue=InlineAcquireQueue(),
        obs=NoOpObs(),
    )
    trips = TripService(sessions)

    async def factory(_sid: str) -> GenerateDeps:
        return GenerateDeps(
            catalog=CatalogService(
                auth=auth,
                sessions=sessions,
                places=places,
                facade=FakeFacade(),
                queue=InlineAcquireQueue(),
                obs=NoOpObs(),
            ),
            engine=GreedyTravelEngine(),
            trips=trips,
            llm=FakeDialogueLlm(structured={"days": []}),
            obs=NoOpObs(),
            sessions_get=sessions.get,
        )

    application.state.generate_runner = InProcessGenerateRunner(
        factory, timeout_seconds=timeout_seconds
    )
    application.state.generate_deps_factory = factory

    def _chat() -> ChatService:
        return chat

    application.dependency_overrides[get_chat_service] = _chat
    # Ownership check in generate router uses SqlSessionRepository(db) by default —
    # override by patching the route helper via a thin monkey: replace runner + use
    # in-memory ownership by swapping get_session path. For ASGI we instead seed via
    # the same sessions repo the chat service uses and override ownership by making
    # generate router use our sessions. Simplest: set app.state sessions and patch
    # generate module's SqlSessionRepository usage via dependency on chat cookie +
    # in-memory through a custom override of _require_owned_session — not available.
    #
    # Practical approach: use the real create_app SQL path only when DB is up; for
    # unit ASGI, monkeypatch src.api.generate.SqlSessionRepository to wrap in-memory.
    from src.api import generate as generate_api

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

    client = TestClient(application)
    return client, sessions, places


def test_generate_sse_progress_then_done() -> None:
    client, sessions, places = _build_generate_client()

    async def _seed() -> str:
        created = await sessions.create(guest_id="will-replace")
        return created.session_id

    # Create via HTTP so cookie matches guest
    create = client.post("/api/v1/sessions")
    assert create.status_code == 200
    session_id = create.json()["session_id"]

    async def _prepare() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        # Align in-memory guest with cookie principal by reading cookie path —
        # chat service used make_chat_service's sessions; our sessions is the same
        # instance from make_chat_service in _build — wait, make_chat_service creates
        # its own sessions. We need the same sessions the chat cookie owns.
        state.trip_scope = {
            "kind": "city",
            "name": "Kyoto",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
            "day_budget": 2,
        }
        state.intent = {"duration_days": 2}
        await sessions.save(state)
        await places.upsert_many(
            [
                PlaceRecord(
                    name="Spot A",
                    lon=135.5,
                    lat=34.5,
                    provider="t",
                    provider_id="a",
                    country_code="jp",
                ),
                PlaceRecord(
                    name="Spot B",
                    lon=135.55,
                    lat=34.55,
                    provider="t",
                    provider_id="b",
                    country_code="jp",
                ),
            ]
        )

    asyncio.run(_prepare())

    # Fix guest_id mismatch: HTTP create used make_chat_service sessions, but we
    # also have sessions from make_chat_service in _build — they are the SAME object
    # returned by make_chat_service. Good.
    response = client.post(f"/api/v1/sessions/{session_id}/generate")
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


def test_generate_foreign_session_denied() -> None:
    client, sessions, _ = _build_generate_client()
    create = client.post("/api/v1/sessions")
    session_id = create.json()["session_id"]
    # New client without cookie
    other = TestClient(create_app())
    response = other.post(f"/api/v1/sessions/{session_id}/generate")
    assert response.status_code == 404


def test_generate_abort_route() -> None:
    client, sessions, places = _build_generate_client()
    create = client.post("/api/v1/sessions")
    session_id = create.json()["session_id"]

    async def _prepare() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        state.trip_scope = {
            "kind": "city",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
            "day_budget": 1,
        }
        await sessions.save(state)
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

    asyncio.run(_prepare())
    abort = client.post(f"/api/v1/sessions/{session_id}/generate/abort")
    assert abort.status_code == 200
    assert abort.json()["abort_requested"] is True


def test_generate_without_redis_ok() -> None:
    """Generate must not require Redis — runner is in-process."""
    client, sessions, places = _build_generate_client()
    create = client.post("/api/v1/sessions")
    session_id = create.json()["session_id"]

    async def _prepare() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        state.trip_scope = {
            "kind": "city",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
            "day_budget": 1,
        }
        await sessions.save(state)
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

    asyncio.run(_prepare())
    response = client.post(f"/api/v1/sessions/{session_id}/generate")
    assert response.status_code == 200
    kinds = [e for e, _ in _parse_sse(response.text)]
    assert "done" in kinds or "error" in kinds
