from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.chat.models import TripSessionState, new_session_id


class SchemaUnavailableError(Exception):
    """Product schema (e.g. trip_sessions) is missing or unapplied."""


def _is_missing_schema(exc: BaseException) -> bool:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if type(current).__name__ == "UndefinedTableError":
            return True
        text = str(current).lower()
        if "does not exist" in text and (
            "trip_sessions" in text or "relation" in text
        ):
            return True
        nxt = current.__cause__ or current.__context__
        orig = getattr(current, "orig", None)
        current = nxt if nxt is not None else orig
    return False


def _reraise_schema(exc: BaseException) -> None:
    if _is_missing_schema(exc):
        raise SchemaUnavailableError(
            "Product schema is not applied"
        ) from exc
    raise exc


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
        try:
            await self._session.commit()
            await self._session.refresh(state)
        except Exception as exc:  # noqa: BLE001 — map missing table
            await self._session.rollback()
            _reraise_schema(exc)
        return state

    async def get(self, session_id: str) -> TripSessionState | None:
        try:
            result = await self._session.execute(
                select(TripSessionState).where(
                    TripSessionState.session_id == session_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            _reraise_schema(exc)
            return None

    async def save(self, state: TripSessionState) -> TripSessionState:
        try:
            merged = await self._session.merge(state)
            await self._session.commit()
            await self._session.refresh(merged)
            return merged
        except Exception as exc:  # noqa: BLE001
            await self._session.rollback()
            _reraise_schema(exc)
            raise


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
