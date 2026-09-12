"""Trip artifact ORM — reopenable draft keyed by trip_id."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_trip_id() -> str:
    return str(uuid4())


class TripArtifact(Base):
    """Minimal owned trip row for GET /trips/{id} (v1 draft only)."""

    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    itinerary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    route_geometry: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "trip_id": self.trip_id,
            "guest_id": self.guest_id,
            "session_id": self.session_id,
            "status": self.status,
            "itinerary": dict(self.itinerary or {}),
            "validation": dict(self.validation) if self.validation else None,
            "saved": False,
            "unlocks_last_trip": False,
        }
        if self.route_geometry:
            out["route_geometry"] = list(self.route_geometry)
        return out
