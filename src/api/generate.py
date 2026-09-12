"""Generate product routes — SSE progress + abort."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.catalog import (
    DefaultPlacesFacade,
    SqlPlaceRepository,
)
from src.modules.catalog.service import CatalogService
from src.modules.chat import SqlSessionRepository
from src.modules.chat.service import SessionAccessError, SseEvent
from src.modules.planner import GreedyTravelEngine
from src.modules.trips import TripService
from src.modules.trips.repository import SqlTripRepository
from src.ports import AuthPort

router = APIRouter(prefix="/api/v1")


def get_generate_runner(request: Request) -> InProcessGenerateRunner:
    runner = getattr(request.app.state, "generate_runner", None)
    if runner is None:
        raise HTTPException(status_code=503, detail="generate runner unavailable")
    return runner


async def _require_owned_session(
    request: Request,
    session_id: str,
    db: AsyncSession,
) -> None:
    auth: AuthPort = request.app.state.auth_port
    principal = auth.read_principal(request)
    if principal is None:
        raise SessionAccessError("unknown session")
    sessions = SqlSessionRepository(db)
    state = await sessions.get(session_id)
    if state is None or state.guest_id != principal.guest_id:
        raise SessionAccessError("unknown session")


def _build_deps_factory(request: Request, db: AsyncSession):
    async def factory(session_id: str):
        sessions = SqlSessionRepository(db)
        places = SqlPlaceRepository(db)
        facade = getattr(request.app.state, "places_facade", None) or DefaultPlacesFacade()
        queue = getattr(request.app.state, "acquire_queue", None)
        catalog = CatalogService(
            auth=request.app.state.auth_port,
            sessions=sessions,
            places=places,
            facade=facade,
            queue=queue,
            obs=request.app.state.obs_port,
        )
        trips = TripService(sessions, SqlTripRepository(db))
        engine = getattr(request.app.state, "travel_engine", None) or GreedyTravelEngine()

        async def sessions_get(sid: str):
            return await sessions.get(sid)

        from src.modules.agents.generate import GenerateDeps

        return GenerateDeps(
            catalog=catalog,
            engine=engine,
            trips=trips,
            llm=request.app.state.llm_gateway,
            obs=request.app.state.obs_port,
            sessions_get=sessions_get,
        )

    return factory


@router.post("/sessions/{session_id}/generate")
async def start_generate(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    runner: InProcessGenerateRunner = Depends(get_generate_runner),
) -> StreamingResponse:
    try:
        await _require_owned_session(request, session_id, db)
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None

    # Bind deps factory for this request's DB session onto runner if needed.
    # Runner is app-scoped; deps_factory is set at composition root with a
    # request-aware override via app.state._generate_deps_factory when testing.
    factory = getattr(request.app.state, "generate_deps_factory", None)
    if factory is not None:
        runner._deps_factory = factory
    else:
        runner._deps_factory = _build_deps_factory(request, db)

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async for event in runner.start(session_id):
                if await request.is_disconnected():
                    await runner.abort(session_id)
                    break
                yield event.encode()
        except SessionAccessError:
            yield SseEvent(
                event="error",
                data={"code": "session_not_found", "message": "session not found"},
            ).encode()
        except Exception as exc:
            yield SseEvent(
                event="error",
                data={"code": "generate_failed", "message": type(exc).__name__},
            ).encode()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/generate/abort")
async def abort_generate(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
    runner: InProcessGenerateRunner = Depends(get_generate_runner),
) -> dict:
    try:
        await _require_owned_session(request, session_id, db)
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None
    return await runner.abort(session_id)
