from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


def place_id_for(provider: str, provider_id: str) -> str:
    raw = f"{provider}:{provider_id}"
    # Stable short id; truncate to fit column.
    return raw[:64] if len(raw) <= 64 else f"{provider}:{uuid4().hex[:24]}"


@dataclass
class PlaceRecord:
    """Domain place used by adapters and repository upsert."""

    name: str
    lon: float
    lat: float
    provider: str
    provider_id: str
    country_code: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = place_id_for(self.provider, self.provider_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "lon": self.lon,
            "lat": self.lat,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "country_code": self.country_code,
            "category": self.category,
            "tags": list(self.tags),
        }


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(128), nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_record(self) -> PlaceRecord:
        return PlaceRecord(
            id=self.id,
            name=self.name,
            lon=self.lon,
            lat=self.lat,
            provider=self.provider,
            provider_id=self.provider_id,
            country_code=self.country_code,
            category=self.category,
            tags=list(self.tags or []),
        )
