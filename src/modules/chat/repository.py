from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.chat.models import TripSessionState, new_session_id


class SessionRepository(Protocol):
    async def create(self, guest_id: str) -> TripSessionState: ...

    async def get(self, session_id: str) -> TripSessionState | None: ...

    async def save(self, state: TripSessionState) -> TripSessionState: ...


class SqlSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, guest_id: str) -> TripSessionState:
        state = TripSessionState(
            session_id=new_session_id(),
            guest_id=guest_id,
            messages=[],
            budget="dialogue",
        )
        self._session.add(state)
        await self._session.commit()
        await self._session.refresh(state)
        return state

    async def get(self, session_id: str) -> TripSessionState | None:
        result = await self._session.execute(
            select(TripSessionState).where(TripSessionState.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def save(self, state: TripSessionState) -> TripSessionState:
        merged = await self._session.merge(state)
        await self._session.commit()
        await self._session.refresh(merged)
        return merged


class InMemorySessionRepository:
    """Test double — not for production."""

    def __init__(self) -> None:
        self._rows: dict[str, TripSessionState] = {}

    async def create(self, guest_id: str) -> TripSessionState:
        state = TripSessionState(
            session_id=new_session_id(),
            guest_id=guest_id,
            messages=[],
            budget="dialogue",
        )
        self._rows[state.session_id] = state
        return state

    async def get(self, session_id: str) -> TripSessionState | None:
        return self._rows.get(session_id)

    async def save(self, state: TripSessionState) -> TripSessionState:
        self._rows[state.session_id] = state
        return state
