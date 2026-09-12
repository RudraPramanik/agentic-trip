from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TripSessionState(Base):
    """Persisted planning session for a guest (itinerary nullable until generate)."""

    __tablename__ = "trip_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    messages: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    budget: Mapped[str] = mapped_column(String(32), nullable=False, default="dialogue")
    intent: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    trip_scope: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    hitl: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    catalog: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    itinerary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    trip_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    run: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    obs_trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


def new_session_id() -> str:
    return str(uuid4())
