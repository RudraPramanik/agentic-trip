"""Revise product route — SSE progress + shared generate abort."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.modules.agents.generate import GenerateDeps
from src.modules.agents.revise import ReviseDeps
from src.modules.agents.runner import InProcessGenerateRunner
from src.modules.catalog import DefaultPlacesFacade, SqlPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat import SqlSessionRepository
from src.modules.chat.service import SessionAccessError, SseEvent
from src.modules.planner import GreedyTravelEngine
from src.modules.trips import TripService
from src.modules.trips.repository import SqlTripRepository
from src.ports import AuthPort

router = APIRouter(prefix="/api/v1")


class ReviseRequest(BaseModel):
    text: str = Field(min_length=1)


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


def _build_revise_deps_factory(request: Request, db: AsyncSession):
    async def factory(session_id: str) -> ReviseDeps:
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
        settings = getattr(request.app.state, "settings", None)
        max_loops = int(getattr(settings, "revise_max_loops", 3))

        generate = GenerateDeps(
            catalog=catalog,
            engine=engine,
            trips=trips,
            llm=request.app.state.llm_gateway,
            obs=request.app.state.obs_port,
            sessions_get=sessions.get,
        )
        return ReviseDeps(
            generate=generate,
            sessions_save=sessions.save,
            max_loops=max_loops,
        )

    return factory


@router.post("/sessions/{session_id}/revise")
async def start_revise(
    session_id: str,
    body: ReviseRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
    runner: InProcessGenerateRunner = Depends(get_generate_runner),
) -> StreamingResponse:
    try:
        await _require_owned_session(request, session_id, db)
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None

    factory = getattr(request.app.state, "revise_deps_factory", None)
    if factory is not None:
        runner._revise_deps_factory = factory
    else:
        runner._revise_deps_factory = _build_revise_deps_factory(request, db)

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async for event in runner.start_revise(session_id, body.text):
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
                data={"code": "revise_failed", "message": type(exc).__name__},
            ).encode()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
