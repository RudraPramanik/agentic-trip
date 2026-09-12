# Local terminal smoke — P5 trip get/export (fixture draft, no live LLM required)

"""Seed an in-process app with a draft trip and exercise get/export over HTTP.

Usage (from repo root, with DATABASE_URL set or using TestClient path):

  uv run python scripts/smoke_p5_trips.py

This uses FastAPI TestClient + in-memory repos (same pattern as ASGI tests).
For live Compose API: create session → generate → curl GET /api/v1/trips/{id}/export.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `uv run python scripts/smoke_p5_trips.py` from repo root.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient

from src.api.sessions import get_chat_service
from src.core.settings import get_settings
from src.main import create_app
from src.modules.chat import ChatService
from src.modules.planner import Day, Itinerary, Stop, ValidateResult
from src.modules.trips import TripService
from src.modules.trips.repository import InMemoryTripRepository
from tests.fakes import make_chat_service


def main() -> int:
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
    created = client.post("/api/v1/sessions")
    assert created.status_code == 200, created.text
    sid = created.json()["session_id"]

    async def seed() -> str:
        saved = await trips.persist_draft(
            sid,
            Itinerary(
                days=[
                    Day(
                        day_index=1,
                        story="Smoke day",
                        stops=[
                            Stop(
                                place_id="p1",
                                name="Viewpoint",
                                lon=91.0,
                                lat=25.0,
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

    trip_id = asyncio.run(seed())
    get_res = client.get(f"/api/v1/trips/{trip_id}")
    export_res = client.get(f"/api/v1/trips/{trip_id}/export")
    assert get_res.status_code == 200, get_res.text
    assert export_res.status_code == 200, export_res.text
    export = export_res.json()
    assert export["map_points"][0]["place_id"] == "p1"
    assert "route_geometry" not in export
    sess = client.get(f"/api/v1/sessions/{sid}")
    assert sess.json().get("trip_id") == trip_id

    # Foreign cookie denied
    other = TestClient(create_app())
    other.app.state.trip_service_factory = lambda _db=None: trips
    trips_api.SqlTripRepository = lambda _db=None: trip_repo  # type: ignore[misc,assignment]
    assert other.get(f"/api/v1/trips/{trip_id}").status_code == 404

    print("P5 smoke OK:", trip_id, "days=", export["cover"]["day_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
