"""Trip artifact repository — in-memory + SQL."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.trips.models import TripArtifact


class TripRepository(Protocol):
    async def get(self, trip_id: str) -> TripArtifact | None: ...

    async def save(self, trip: TripArtifact) -> TripArtifact: ...


class InMemoryTripRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, TripArtifact] = {}

    async def get(self, trip_id: str) -> TripArtifact | None:
        return self._by_id.get(trip_id)

    async def save(self, trip: TripArtifact) -> TripArtifact:
        self._by_id[trip.trip_id] = trip
        return trip


class SqlTripRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, trip_id: str) -> TripArtifact | None:
        result = await self._session.execute(
            select(TripArtifact).where(TripArtifact.trip_id == trip_id)
        )
        return result.scalar_one_or_none()

    async def save(self, trip: TripArtifact) -> TripArtifact:
        merged = await self._session.merge(trip)
        await self._session.commit()
        await self._session.refresh(merged)
        return merged
