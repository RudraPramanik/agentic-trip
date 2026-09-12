"""CatalogService acquire / retrieve / queue proofs (P3.3–P3.7)."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request

from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.facade import FetchResult
from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import InMemoryPlaceRepository
from src.modules.catalog.service import CatalogService, scope_allows_acquire
from src.modules.chat import InMemorySessionRepository
from src.modules.monitor import NoOpObs
from tests.fakes import RecordingObs


class FakeFacade:
    def __init__(self, result: FetchResult | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.result = result or FetchResult(places=[])

    def fetch_for_scope(self, scope: dict[str, Any]) -> FetchResult:
        self.calls.append(scope)
        return self.result


def _request_with_cookie(guest_id: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", f"at_guest={guest_id}".encode())],
    }
    return Request(scope)


def _make_service(
    *,
    facade: FakeFacade | None = None,
    queue: InlineAcquireQueue | None = None,
    obs: object | None = None,
) -> tuple[CatalogService, InMemorySessionRepository, FakeFacade, InlineAcquireQueue]:
    sessions = InMemorySessionRepository()
    places = InMemoryPlaceRepository()
    fake = facade or FakeFacade()
    q = queue or InlineAcquireQueue()
    service = CatalogService(
        auth=CookieAuthAdapter(),
        sessions=sessions,
        places=places,
        facade=fake,
        queue=q,
        obs=obs or NoOpObs(),  # type: ignore[arg-type]
    )
    # Wire inline queue to real acquire for success-path tests.
    if q.acquire_fn is None and not q.fail:
        q.acquire_fn = service.acquire
    return service, sessions, fake, q


def test_scope_allows_acquire_rules() -> None:
    assert scope_allows_acquire(None)[0] is False
    assert scope_allows_acquire({"kind": "country", "hubs": []})[1] == "country_without_hubs"
    ok, _ = scope_allows_acquire(
        {
            "kind": "city",
            "bbox": [135.0, 34.0, 136.0, 35.0],
            "country_code": "jp",
        }
    )
    assert ok is True
    ok2, _ = scope_allows_acquire(
        {
            "kind": "country",
            "hubs": [{"name": "Tokyo", "bbox": [139.0, 35.0, 140.0, 36.0]}],
            "country_code": "jp",
        }
    )
    assert ok2 is True


@pytest.mark.asyncio
async def test_acquire_uses_region_bbox_and_country_filter() -> None:
    facade = FakeFacade(
        FetchResult(
            places=[
                PlaceRecord(
                    name="In",
                    lon=135.7,
                    lat=34.9,
                    provider="t",
                    provider_id="1",
                    country_code="jp",
                ),
                PlaceRecord(
                    name="Out",
                    lon=135.7,
                    lat=34.9,
                    provider="t",
                    provider_id="2",
                    country_code="kr",
                ),
            ]
        )
    )
    service, sessions, fake, _ = _make_service(facade=facade)
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "region",
        "name": "Kansai",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
        "hubs": [],
    }
    await sessions.save(state)

    result = await service.acquire(state.session_id)
    assert result.status == "ready"
    assert result.place_count == 1
    assert fake.calls and fake.calls[0]["bbox"] == [135.0, 34.0, 136.0, 35.0]
    loaded = await sessions.get(state.session_id)
    assert loaded is not None
    assert loaded.catalog is not None
    assert loaded.catalog["status"] == "ready"


@pytest.mark.asyncio
async def test_acquire_refuses_country_without_hubs() -> None:
    service, sessions, fake, _ = _make_service()
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "country",
        "name": "Japan",
        "hubs": [],
        "country_code": "jp",
        "bbox": [129.0, 30.0, 146.0, 46.0],
    }
    await sessions.save(state)
    result = await service.acquire(state.session_id)
    assert result.status == "failed"
    assert result.error == "country_without_hubs"
    assert fake.calls == []


@pytest.mark.asyncio
async def test_enqueue_queue_down_marks_failed() -> None:
    service, sessions, _, q = _make_service(queue=InlineAcquireQueue(fail=True))
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
    }
    await sessions.save(state)
    req = _request_with_cookie("g1")
    out = await service.enqueue_acquire(req, state.session_id)
    assert out["status"] == "failed"
    loaded = await sessions.get(state.session_id)
    assert loaded is not None
    assert loaded.catalog is not None
    assert loaded.catalog["status"] == "failed"


@pytest.mark.asyncio
async def test_enqueue_success_runs_inline_acquire() -> None:
    facade = FakeFacade(
        FetchResult(
            places=[
                PlaceRecord(
                    name="Spot",
                    lon=135.5,
                    lat=34.5,
                    provider="t",
                    provider_id="9",
                    country_code="jp",
                )
            ]
        )
    )
    service, sessions, _, _ = _make_service(facade=facade)
    state = await sessions.create(guest_id="g1")
    state.trip_scope = {
        "kind": "city",
        "bbox": [135.0, 34.0, 136.0, 35.0],
        "country_code": "jp",
    }
    await sessions.save(state)
    out = await service.enqueue_acquire(_request_with_cookie("g1"), state.session_id)
    assert out["status"] in {"pending", "ready"}
    loaded = await sessions.get(state.session_id)
    assert loaded is not None
    assert loaded.catalog is not None
    assert loaded.catalog["status"] == "ready"


@pytest.mark.asyncio
async def test_retrieve_ids_or_empty_and_obs_span() -> None:
    obs = RecordingObs()
    service, sessions, _, _ = _make_service(obs=obs)
    places = service._places  # noqa: SLF001 — test double
    await places.upsert_many(
        [
            PlaceRecord(
                name="A",
                lon=135.5,
                lat=34.5,
                provider="t",
                provider_id="a",
                country_code="jp",
            )
        ]
    )
    got = await service.retrieve(
        {"bbox": [135.0, 34.0, 136.0, 35.0], "country_code": "jp"},
        prefs=None,
    )
    assert got.empty is False
    assert got.place_ids
    assert "catalog.retrieve" in obs.spans
    assert obs.span_kwargs[-1].get("empty") is False

    empty = await service.retrieve(
        {"bbox": [0.0, 0.0, 1.0, 1.0], "country_code": "jp"},
        prefs=None,
    )
    assert empty.empty is True
    assert empty.places == []
    assert obs.span_kwargs[-1].get("empty") is True


@pytest.mark.asyncio
async def test_retrieve_noop_obs_still_succeeds() -> None:
    service, _, _, _ = _make_service(obs=NoOpObs())
    result = await service.retrieve(
        {"bbox": [135.0, 34.0, 136.0, 35.0], "country_code": "jp"},
        prefs={},
    )
    assert result.empty is True
