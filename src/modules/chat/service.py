from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from src.modules.auth import GuestPrincipal
from src.modules.chat.dto import (
    ChatMessage,
    CreateSessionResponse,
    SessionProjection,
)
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SessionRepository
from src.modules.llm.types import LlmUnavailable
from src.ports import AuthPort, LlmGateway, ObsPort

CancelCheck = Callable[[], Awaitable[bool]]


class SessionAccessError(Exception):
    """Unknown or foreign session — map to 404 without leaking."""


@dataclass(frozen=True)
class SseEvent:
    event: str
    data: dict[str, Any]

    def encode(self) -> bytes:
        payload = json.dumps(self.data, ensure_ascii=False)
        return f"event: {self.event}\ndata: {payload}\n\n".encode()


class ChatService:
    def __init__(
        self,
        *,
        auth: AuthPort,
        sessions: SessionRepository,
        llm: LlmGateway,
        obs: ObsPort,
    ) -> None:
        self._auth = auth
        self._sessions = sessions
        self._llm = llm
        self._obs = obs

    def _principal_from_request(
        self, request: Request, response: Response | None = None
    ) -> GuestPrincipal:
        principal = self._auth.read_principal(request)
        if principal is not None:
            return principal
        if response is None:
            raise SessionAccessError("guest cookie required")
        return self._auth.issue_guest(response)

    async def create_session(
        self, request: Request, response: Response
    ) -> CreateSessionResponse:
        principal = self._principal_from_request(request, response)
        state = await self._sessions.create(guest_id=principal.guest_id)
        return CreateSessionResponse(session_id=state.session_id, guest=True)

    async def get_session(
        self, request: Request, session_id: str
    ) -> SessionProjection:
        principal = self._auth.read_principal(request)
        if principal is None:
            raise SessionAccessError("unknown session")
        state = await self._require_owned(session_id, principal)
        return self._project(state)

    async def send_message(
        self,
        request: Request,
        session_id: str,
        text: str,
        *,
        cancel_check: CancelCheck | None = None,
    ) -> AsyncIterator[SseEvent]:
        principal = self._auth.read_principal(request)
        if principal is None:
            raise SessionAccessError("unknown session")

        with self._obs.start_trace("chat.turn", session_id=session_id):
            with self._obs.span("chat.send_message", session_id=session_id):
                async for event in self._send_message_inner(
                    principal, session_id, text, cancel_check=cancel_check
                ):
                    yield event

    async def _send_message_inner(
        self,
        principal: GuestPrincipal,
        session_id: str,
        text: str,
        *,
        cancel_check: CancelCheck | None,
    ) -> AsyncIterator[SseEvent]:
        state = await self._require_owned(session_id, principal)
        messages = list(state.messages or [])
        messages.append({"role": "user", "content": text})
        state.messages = messages
        await self._sessions.save(state)

        if cancel_check is not None and await cancel_check():
            return

        result = await self._llm.complete(
            "dialogue",
            [{"role": m["role"], "content": m["content"]} for m in messages],
        )

        if cancel_check is not None and await cancel_check():
            return

        if isinstance(result, LlmUnavailable):
            yield SseEvent(
                event="error",
                data={
                    "code": "llm_unavailable",
                    "message": "Dialogue model is unavailable. Your session is intact — try again later.",
                },
            )
            return

        content = _dialogue_text(result)
        # Stream in small chunks for SSE token events.
        chunk_size = 24
        for i in range(0, len(content), chunk_size):
            if cancel_check is not None and await cancel_check():
                return
            yield SseEvent(event="token", data={"text": content[i : i + chunk_size]})

        if cancel_check is not None and await cancel_check():
            return

        messages.append({"role": "assistant", "content": content})
        state.messages = messages
        await self._sessions.save(state)
        yield SseEvent(event="message", data={"role": "assistant", "content": content})

    async def _require_owned(
        self, session_id: str, principal: GuestPrincipal
    ) -> TripSessionState:
        state = await self._sessions.get(session_id)
        if state is None or state.guest_id != principal.guest_id:
            raise SessionAccessError("unknown session")
        return state

    @staticmethod
    def _project(state: TripSessionState) -> SessionProjection:
        return SessionProjection(
            session_id=state.session_id,
            messages=[
                ChatMessage(role=m["role"], content=m["content"])
                for m in (state.messages or [])
            ],
            budget=state.budget,
            hitl=state.hitl,
            trip_scope=state.trip_scope,
        )


def _dialogue_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict) and "content" in result:
        return str(result["content"])
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)
