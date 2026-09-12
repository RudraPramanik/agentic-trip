from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from src.modules.agents.dialogue import DialogueOutcome, DialogueRunner
from src.modules.auth import GuestPrincipal
from src.modules.chat.dto import (
    ChatMessage,
    CreateSessionResponse,
    SessionProjection,
)
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SessionRepository
from src.ports import AuthPort, ObsPort

CancelCheck = Callable[[], Awaitable[bool]]


class SessionAccessError(Exception):
    """Unknown or foreign session — map to 404 without leaking."""


class HitlStateError(Exception):
    """No pending HITL to resume."""


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
        obs: ObsPort,
        dialogue: DialogueRunner,
    ) -> None:
        self._auth = auth
        self._sessions = sessions
        self._obs = obs
        self._dialogue = dialogue

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

    async def resume_hitl(
        self,
        request: Request,
        session_id: str,
        *,
        choice_id: str | None = None,
        text: str | None = None,
    ) -> SessionProjection:
        principal = self._auth.read_principal(request)
        if principal is None:
            raise SessionAccessError("unknown session")
        state = await self._require_owned(session_id, principal)
        hitl = state.hitl or {}
        if hitl.get("status") != "pending":
            raise HitlStateError("no pending hitl")

        with self._obs.start_trace("chat.hitl_resume", session_id=session_id):
            outcome = await self._dialogue.resume(
                session_id, choice_id=choice_id, text=text
            )
            await self._apply_outcome(state, outcome)
            return self._project(state)

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

        # Dialogue graph only — never generate/catalog.
        outcome = await self._dialogue.run_turn(session_id, text)

        if cancel_check is not None and await cancel_check():
            return

        if outcome.status == "error" and outcome.error_code in {
            "checkpoint_or_graph_error",
            "checkpoint_unavailable",
        }:
            yield SseEvent(
                event="error",
                data={
                    "code": outcome.error_code or "dialogue_error",
                    "message": outcome.assistant_message,
                },
            )
            return

        await self._apply_outcome(state, outcome)

        if outcome.status == "hitl" and outcome.hitl:
            yield SseEvent(event="hitl", data=outcome.hitl)

        content = outcome.assistant_message or ""
        chunk_size = 24
        for i in range(0, len(content), chunk_size):
            if cancel_check is not None and await cancel_check():
                return
            yield SseEvent(event="token", data={"text": content[i : i + chunk_size]})

        if cancel_check is not None and await cancel_check():
            return

        yield SseEvent(event="message", data={"role": "assistant", "content": content})

    async def _apply_outcome(
        self, state: TripSessionState, outcome: DialogueOutcome
    ) -> None:
        messages = list(state.messages or [])
        if outcome.assistant_message:
            messages.append(
                {"role": "assistant", "content": outcome.assistant_message}
            )
        state.messages = messages

        if outcome.intent is not None:
            state.intent = outcome.intent

        if outcome.status == "hitl":
            state.hitl = outcome.hitl
            # Do not persist trip_scope while waiting.
        elif outcome.status == "confirmed":
            state.trip_scope = outcome.trip_scope
            state.hitl = outcome.hitl or {"status": "resolved"}
        elif outcome.status == "ask":
            # Clarification — do not write trip_scope from this turn.
            state.hitl = None
        elif outcome.status == "error":
            pass

        await self._sessions.save(state)

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
            catalog=state.catalog,
        )
