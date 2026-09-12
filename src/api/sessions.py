from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.modules.chat import (
    ChatService,
    HitlChoiceRequest,
    HitlStateError,
    SchemaUnavailableError,
    SendMessageRequest,
    SessionAccessError,
    SqlSessionRepository,
)
from src.modules.chat.service import SseEvent

router = APIRouter(prefix="/api/v1")

_SCHEMA_DETAIL = {
    "code": "schema_unavailable",
    "message": "Product schema is not applied",
}


def get_chat_service(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> ChatService:
    return ChatService(
        auth=request.app.state.auth_port,
        sessions=SqlSessionRepository(db),
        obs=request.app.state.obs_port,
        dialogue=request.app.state.dialogue_runner,
    )


@router.post("/sessions")
async def create_session(
    request: Request,
    response: Response,
    chat: ChatService = Depends(get_chat_service),
) -> dict:
    try:
        result = await chat.create_session(request, response)
    except SchemaUnavailableError:
        raise HTTPException(status_code=503, detail=_SCHEMA_DETAIL) from None
    return result.model_dump()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    chat: ChatService = Depends(get_chat_service),
) -> dict:
    try:
        projection = await chat.get_session(request, session_id)
    except SchemaUnavailableError:
        raise HTTPException(status_code=503, detail=_SCHEMA_DETAIL) from None
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None
    return projection.model_dump()


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    request: Request,
    chat: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    # user_id on the body is intentionally ignored (never trust client identity).
    _ = body.user_id

    async def event_stream() -> AsyncIterator[bytes]:
        async def cancel_check() -> bool:
            return await request.is_disconnected()

        try:
            async for event in chat.send_message(
                request,
                session_id,
                body.text,
                cancel_check=cancel_check,
            ):
                if await request.is_disconnected():
                    break
                yield event.encode()
        except SchemaUnavailableError:
            yield SseEvent(event="error", data=_SCHEMA_DETAIL).encode()
        except SessionAccessError:
            yield SseEvent(
                event="error",
                data={"code": "session_not_found", "message": "session not found"},
            ).encode()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/hitl")
async def resume_hitl(
    session_id: str,
    body: HitlChoiceRequest,
    request: Request,
    chat: ChatService = Depends(get_chat_service),
) -> dict:
    _ = body.user_id
    try:
        projection = await chat.resume_hitl(
            request,
            session_id,
            choice_id=body.choice_id,
            text=body.text,
        )
    except SchemaUnavailableError:
        raise HTTPException(status_code=503, detail=_SCHEMA_DETAIL) from None
    except SessionAccessError:
        raise HTTPException(status_code=404, detail="session not found") from None
    except HitlStateError:
        raise HTTPException(status_code=409, detail="no pending hitl") from None
    return projection.model_dump()
