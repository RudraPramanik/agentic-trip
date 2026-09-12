"""ASGI trip get/export ownership proofs (P5.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.sessions import get_chat_service
from src.core.settings import get_settings
from src.main import create_app
from src.modules.chat import ChatService, InMemorySessionRepository
from src.modules.planner import Day, Itinerary, Stop, ValidateResult
from src.modules.trips import TripService
from src.modules.trips.repository import InMemoryTripRepository
from tests.fakes import make_chat_service


def _build_trips_client() -> tuple[
    TestClient,
    InMemorySessionRepository,
    InMemoryTripRepository,
    TripService,
]:
    get_settings.cache_clear()
    application = create_app()
    chat, sessions, _, _, _ = make_chat_service()
    trip_repo = InMemoryTripRepository()
    trips = TripService(sessions, trip_repo)

    def _chat() -> ChatService:
        return ChatService(
            auth=chat._auth,
            sessions=sessions,
            obs=chat._obs,
            dialogue=chat._dialogue,
            trips=trips,
        )

    application.dependency_overrides[get_chat_service] = _chat
    application.state.trip_service_factory = lambda _db=None: trips

    from src.api import trips as trips_api

    class _SessionRepoAdapter:
        def __init__(self, _db=None) -> None:
            self._inner = sessions

        async def get(self, session_id: str):
            return await self._inner.get(session_id)

        async def create(self, guest_id: str):
            return await self._inner.create(guest_id)

        async def save(self, state):
            return await self._inner.save(state)

    trips_api.SqlSessionRepository = _SessionRepoAdapter  # type: ignore[misc,assignment]
    trips_api.SqlTripRepository = lambda _db=None: trip_repo  # type: ignore[misc,assignment]

    client = TestClient(application)
    return client, sessions, trip_repo, trips


def test_asgi_trip_get_and_export_owner() -> None:
    client, sessions, _repo, trips = _build_trips_client()
    created = client.post("/api/v1/sessions")
    assert created.status_code == 200
    sid = created.json()["session_id"]

    # Seed draft as the same guest via cookie-bound session
    import asyncio

    async def _seed() -> str:
        state = await sessions.get(sid)
        assert state is not None
        saved = await trips.persist_draft(
            sid,
            Itinerary(
                days=[
                    Day(
                        day_index=1,
                        story="Hello",
                        stops=[
                            Stop(
                                place_id="p1",
                                name="Bridge",
                                lon=91.1,
                                lat=25.2,
                            )
                        ],
                    )
                ],
                place_ids=["p1"],
            ),
            ValidateResult(ok=True),
        )
        assert saved.trip_id
        return saved.trip_id

    trip_id = asyncio.run(_seed())

    get_res = client.get(f"/api/v1/trips/{trip_id}")
    assert get_res.status_code == 200
    body = get_res.json()
    assert body["trip_id"] == trip_id
    assert body["itinerary"]["days"][0]["stops"][0]["place_id"] == "p1"

    export_res = client.get(f"/api/v1/trips/{trip_id}/export")
    assert export_res.status_code == 200
    export = export_res.json()
    assert export["trip_id"] == trip_id
    assert export["cover"]["day_count"] == 1
    assert export["map_points"][0]["place_id"] == "p1"
    assert "route_geometry" not in export

    # Session projection exposes trip_id
    sess = client.get(f"/api/v1/sessions/{sid}")
    assert sess.status_code == 200
    assert sess.json().get("trip_id") == trip_id


def test_asgi_foreign_trip_denied() -> None:
    client, sessions, _repo, trips = _build_trips_client()
    owner = client.post("/api/v1/sessions")
    sid = owner.json()["session_id"]

    import asyncio

    async def _seed() -> str:
        saved = await trips.persist_draft(
            sid,
            Itinerary(
                days=[Day(day_index=1, stops=[Stop(place_id="p1", name="A")])],
                place_ids=["p1"],
            ),
            ValidateResult(ok=True),
        )
        assert saved.trip_id
        return saved.trip_id

    trip_id = asyncio.run(_seed())

    # New client = no owner cookie
    get_settings.cache_clear()
    other_app = create_app()
    other_app.state.trip_service_factory = lambda _db=None: trips
    from src.api import trips as trips_api

    trips_api.SqlTripRepository = lambda _db=None: _repo  # type: ignore[misc,assignment]
    other = TestClient(other_app)
    denied = other.get(f"/api/v1/trips/{trip_id}")
    assert denied.status_code == 404
    export_denied = other.get(f"/api/v1/trips/{trip_id}/export")
    assert export_denied.status_code == 404
