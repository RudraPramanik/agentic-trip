"""ASGI catalog HTTP proofs (P3.6)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from src.core.settings import get_settings
from src.main import create_app
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import InMemorySessionRepository
from src.api.catalog import get_catalog_service
from src.api.sessions import get_chat_service
from src.modules.chat import ChatService
from src.modules.monitor import NoOpObs
from tests.fakes import make_chat_service


class FakeFacade:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        self.calls.append(scope)
        return FetchResult(
            places=[
                PlaceRecord(
                    name="API Spot",
                    lon=135.5,
                    lat=34.5,
                    provider="t",
                    provider_id="api1",
                    country_code="jp",
                )
            ]
        )


def _build_client() -> tuple[TestClient, InMemorySessionRepository, CatalogService]:
    get_settings.cache_clear()
    application = create_app()
    chat, sessions, _, _, _ = make_chat_service()
    places = InMemoryPlaceRepository()
    facade = FakeFacade()
    queue = InlineAcquireQueue()
    catalog = CatalogService(
        auth=application.state.auth_port,
        sessions=sessions,
        places=places,
        facade=facade,
        queue=queue,
        obs=NoOpObs(),
    )
    queue.acquire_fn = catalog.acquire
    application.state.acquire_queue = queue
    application.state.places_facade = facade

    def _chat() -> ChatService:
        return chat

    def _catalog() -> CatalogService:
        return CatalogService(
            auth=application.state.auth_port,
            sessions=sessions,
            places=places,
            facade=facade,
            queue=queue,
            obs=NoOpObs(),
        )

    application.dependency_overrides[get_chat_service] = _chat
    application.dependency_overrides[get_catalog_service] = _catalog
    client = TestClient(application)
    return client, sessions, catalog


def test_catalog_enqueue_and_readiness() -> None:
    client, sessions, _ = _build_client()
    create = client.post("/api/v1/sessions")
    assert create.status_code == 200
    session_id = create.json()["session_id"]
    cookie = create.cookies.get("at_guest")
    assert cookie

    # Seed trip_scope directly (dialogue not under test here).
    import asyncio

    async def _seed() -> None:
        state = await sessions.get(session_id)
        assert state is not None
        state.trip_scope = {
            "kind": "city",
            "name": "Kyoto",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
        }
        await sessions.save(state)

    asyncio.run(_seed())

    enq = client.post(
        "/api/v1/catalog/acquire",
        json={"session_id": session_id},
        cookies={"at_guest": cookie},
    )
    assert enq.status_code == 200
    body = enq.json()
    assert body["status"] in {"pending", "ready", "partial"}

    ready = client.get(
        f"/api/v1/sessions/{session_id}/catalog",
        cookies={"at_guest": cookie},
    )
    assert ready.status_code == 200
    payload = ready.json()
    assert payload["status"] == "ready"
    assert payload["ready"] is True
    assert payload["place_count"] == 1

    # Session projection may include catalog.
    proj = client.get(
        f"/api/v1/sessions/{session_id}",
        cookies={"at_guest": cookie},
    )
    assert proj.status_code == 200
    assert proj.json().get("catalog", {}).get("status") == "ready"


def test_foreign_catalog_denied() -> None:
    client, sessions, _ = _build_client()
    owner = client.post("/api/v1/sessions")
    session_id = owner.json()["session_id"]

    # New guest identity (clear jar so create_session issues a different cookie).
    client.cookies.clear()
    other = client.post("/api/v1/sessions")
    other_cookie = other.cookies.get("at_guest")
    assert other_cookie
    assert other_cookie != owner.cookies.get("at_guest")

    denied = client.get(
        f"/api/v1/sessions/{session_id}/catalog",
        cookies={"at_guest": other_cookie},
    )
    assert denied.status_code == 404

    enq = client.post(
        "/api/v1/catalog/acquire",
        json={"session_id": session_id},
        cookies={"at_guest": other_cookie},
    )
    assert enq.status_code == 404


def test_health_without_redis() -> None:
    """API liveness does not require Redis (P3.4 / api-foundation)."""
    get_settings.cache_clear()
    application = create_app()
    client = TestClient(application)
    res = client.get("/health")
    assert res.status_code == 200
