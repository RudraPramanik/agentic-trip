from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette.requests import Request

from src.modules.auth import GuestPrincipal
from src.modules.catalog.dto import CatalogReadinessResponse
from src.modules.catalog.facade import PlacesFacade
from src.modules.catalog.queue import AcquireQueue, AcquireQueueError
from src.modules.catalog.repository import (
    PlaceRepository,
    filter_places_by_country,
)
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SessionRepository
from src.modules.chat.service import SessionAccessError
from src.ports import AuthPort, ObsPort


@dataclass
class AcquireResult:
    status: str  # ready | partial | failed
    place_count: int = 0
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.status in {"ready", "partial"} and self.place_count >= 0


@dataclass
class RetrieveResult:
    places: list[dict[str, Any]]
    empty: bool

    @property
    def place_ids(self) -> list[str]:
        return [str(p["id"]) for p in self.places if p.get("id")]


def scope_allows_acquire(trip_scope: dict[str, Any] | None) -> tuple[bool, str | None]:
    """Country without hubs must not silent-centroid scrape."""
    if not trip_scope:
        return False, "missing_trip_scope"
    kind = trip_scope.get("kind")
    hubs = trip_scope.get("hubs") or []
    bbox = trip_scope.get("bbox")
    if kind == "country" and not hubs:
        return False, "country_without_hubs"
    if kind in {"city", "region"} and not bbox and not hubs:
        return False, "missing_bbox"
    if kind == "country" and hubs:
        return True, None
    if bbox or hubs:
        return True, None
    return False, "missing_bbox"


class CatalogService:
    def __init__(
        self,
        *,
        auth: AuthPort,
        sessions: SessionRepository,
        places: PlaceRepository,
        facade: PlacesFacade,
        queue: AcquireQueue,
        obs: ObsPort,
    ) -> None:
        self._auth = auth
        self._sessions = sessions
        self._places = places
        self._facade = facade
        self._queue = queue
        self._obs = obs

    async def _require_owned(
        self, session_id: str, principal: GuestPrincipal
    ) -> TripSessionState:
        state = await self._sessions.get(session_id)
        if state is None or state.guest_id != principal.guest_id:
            raise SessionAccessError("unknown session")
        return state

    async def readiness(
        self, request: Request, session_id: str
    ) -> CatalogReadinessResponse:
        principal = self._auth.read_principal(request)
        if principal is None:
            raise SessionAccessError("unknown session")
        state = await self._require_owned(session_id, principal)
        return self._readiness_from_state(state)

    def _readiness_from_state(self, state: TripSessionState) -> CatalogReadinessResponse:
        catalog = state.catalog or {}
        status = str(catalog.get("status") or "idle")
        place_count = catalog.get("place_count")
        ready = status in {"ready", "partial"}
        return CatalogReadinessResponse(
            ready=ready,
            status=status,
            place_count=int(place_count) if place_count is not None else None,
            job_id=catalog.get("job_id"),
            error=catalog.get("error"),
        )

    async def enqueue_acquire(
        self, request: Request, session_id: str
    ) -> dict[str, Any]:
        principal = self._auth.read_principal(request)
        if principal is None:
            raise SessionAccessError("unknown session")
        state = await self._require_owned(session_id, principal)
        ok, reason = scope_allows_acquire(state.trip_scope)
        if not ok:
            state.catalog = {
                "status": "failed",
                "place_count": 0,
                "error": reason or "invalid_scope",
            }
            await self._sessions.save(state)
            return {"job_id": None, "status": "failed", "error": reason}

        existing = state.catalog or {}
        if existing.get("status") == "ready" and int(existing.get("place_count") or 0) > 0:
            return {
                "job_id": existing.get("job_id"),
                "status": "ready",
            }

        state.catalog = {
            "status": "pending",
            "place_count": existing.get("place_count"),
            "job_id": None,
            "error": None,
        }
        await self._sessions.save(state)

        try:
            job_id = await self._queue.enqueue_acquire(session_id)
        except AcquireQueueError as exc:
            state.catalog = {
                "status": "failed",
                "place_count": 0,
                "job_id": None,
                "error": str(exc) or "queue_unavailable",
            }
            await self._sessions.save(state)
            return {"job_id": None, "status": "failed", "error": "queue_unavailable"}

        # Inline/test queues may finish acquire before we return — do not clobber.
        refreshed = await self._sessions.get(session_id)
        if refreshed is None:
            return {"job_id": job_id, "status": "pending"}
        current = refreshed.catalog or {}
        terminal = current.get("status") in {"ready", "partial", "failed"}
        if terminal:
            refreshed.catalog = {**current, "job_id": job_id}
            await self._sessions.save(refreshed)
            return {
                "job_id": job_id,
                "status": str(current.get("status")),
            }

        refreshed.catalog = {
            "status": "pending",
            "place_count": current.get("place_count"),
            "job_id": job_id,
            "error": None,
        }
        await self._sessions.save(refreshed)
        return {"job_id": job_id, "status": "pending"}

    async def acquire(self, session_id: str) -> AcquireResult:
        """Worker entry — no HTTP principal; uses session trip_scope."""
        state = await self._sessions.get(session_id)
        if state is None:
            return AcquireResult(status="failed", error="unknown_session")
        ok, reason = scope_allows_acquire(state.trip_scope)
        if not ok:
            result = AcquireResult(status="failed", error=reason)
            await self._write_catalog(state, result)
            return result

        scope = dict(state.trip_scope or {})
        state.catalog = {
            **(state.catalog or {}),
            "status": "running",
            "error": None,
        }
        await self._sessions.save(state)

        fetch = self._facade.fetch_for_scope(scope)
        country = scope.get("country_code")
        filtered = filter_places_by_country(fetch.places, country)
        count = await self._places.upsert_many(filtered)

        if count == 0 and (fetch.partial or fetch.errors or not fetch.places):
            # Provider down / thin catalog — honest failed or partial empty.
            if fetch.errors and not fetch.places:
                result = AcquireResult(
                    status="failed",
                    place_count=0,
                    error="providers_down",
                )
            else:
                result = AcquireResult(
                    status="partial",
                    place_count=0,
                    error="thin_catalog",
                )
        elif fetch.partial:
            result = AcquireResult(status="partial", place_count=count)
        else:
            result = AcquireResult(
                status="ready" if count > 0 else "partial",
                place_count=count,
                error=None if count > 0 else "thin_catalog",
            )
        await self._write_catalog(state, result)
        return result

    async def _write_catalog(
        self, state: TripSessionState, result: AcquireResult
    ) -> None:
        prev = state.catalog or {}
        state.catalog = {
            "status": result.status,
            "place_count": result.place_count,
            "job_id": prev.get("job_id"),
            "error": result.error,
        }
        await self._sessions.save(state)

    async def mark_failed(self, session_id: str, error: str = "job_failed") -> None:
        state = await self._sessions.get(session_id)
        if state is None:
            return
        prev = state.catalog or {}
        state.catalog = {
            "status": "failed",
            "place_count": int(prev.get("place_count") or 0),
            "job_id": prev.get("job_id"),
            "error": error,
        }
        await self._sessions.save(state)

    async def retrieve(
        self, scope: dict[str, Any], prefs: dict[str, Any] | None = None
    ) -> RetrieveResult:
        prefs = prefs or {}
        records = await self._places.retrieve(scope, prefs)
        places = [r.to_dict() for r in records]
        empty = len(places) == 0
        with self._obs.span(
            "catalog.retrieve",
            empty=empty,
            category=prefs.get("category"),
            country_code=scope.get("country_code"),
            place_count=len(places),
        ):
            pass
        return RetrieveResult(places=places, empty=empty)
