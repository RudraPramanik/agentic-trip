from __future__ import annotations

from typing import Any, Protocol

from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_MakeEnvelope, ST_Within
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.models import Place, PlaceRecord


class PlaceRepository(Protocol):
    async def upsert_many(self, places: list[PlaceRecord]) -> int: ...

    async def retrieve(
        self, scope: dict[str, Any], prefs: dict[str, Any] | None = None
    ) -> list[PlaceRecord]: ...


def _normalize_country(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().lower()


def filter_places_by_country(
    places: list[PlaceRecord], country_code: str | None
) -> list[PlaceRecord]:
    """Exclude unknown-country and foreign POIs."""
    wanted = _normalize_country(country_code)
    if not wanted:
        # No resolvable trip country → keep nothing rather than guess.
        return []
    return [
        p
        for p in places
        if _normalize_country(p.country_code) == wanted
    ]


class SqlPlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, places: list[PlaceRecord]) -> int:
        if not places:
            return 0
        rows: list[dict[str, Any]] = []
        for p in places:
            if p.lon is None or p.lat is None:
                continue
            place_id = p.id or f"{p.provider}:{p.provider_id}"
            rows.append(
                {
                    "id": place_id,
                    "name": p.name,
                    "geom": WKTElement(f"POINT({p.lon} {p.lat})", srid=4326),
                    "category": p.category,
                    "tags": list(p.tags or []),
                    "country_code": _normalize_country(p.country_code),
                    "provider": p.provider,
                    "provider_id": p.provider_id,
                    "lon": float(p.lon),
                    "lat": float(p.lat),
                }
            )
        if not rows:
            return 0
        stmt = insert(Place).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["provider", "provider_id"],
            set_={
                "name": stmt.excluded.name,
                "geom": stmt.excluded.geom,
                "category": stmt.excluded.category,
                "tags": stmt.excluded.tags,
                "country_code": stmt.excluded.country_code,
                "lon": stmt.excluded.lon,
                "lat": stmt.excluded.lat,
                "id": stmt.excluded.id,
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()
        return len(rows)

    async def retrieve(
        self, scope: dict[str, Any], prefs: dict[str, Any] | None = None
    ) -> list[PlaceRecord]:
        prefs = prefs or {}
        bbox = scope.get("bbox")
        country = _normalize_country(scope.get("country_code"))
        if not bbox or len(bbox) != 4:
            return []
        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox)
        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        conditions = [ST_Within(Place.geom, envelope)]
        if country:
            conditions.append(Place.country_code == country)
        else:
            # Unknown trip country — never return guessed border POIs.
            return []

        category = prefs.get("category")
        if category:
            conditions.append(Place.category == category)
        tags = prefs.get("tags") or []
        stmt = select(Place).where(and_(*conditions))
        result = await self._session.execute(stmt)
        records = [row.to_record() for row in result.scalars().all()]
        if tags:
            tag_set = {str(t).lower() for t in tags}
            records = [
                r
                for r in records
                if tag_set.intersection({str(t).lower() for t in (r.tags or [])})
            ]
        return records


class InMemoryPlaceRepository:
    """Test double — bbox + country filter without PostGIS."""

    def __init__(self) -> None:
        self._rows: dict[str, PlaceRecord] = {}

    async def upsert_many(self, places: list[PlaceRecord]) -> int:
        count = 0
        for p in places:
            pid = p.id or f"{p.provider}:{p.provider_id}"
            stored = PlaceRecord(
                id=pid,
                name=p.name,
                lon=p.lon,
                lat=p.lat,
                provider=p.provider,
                provider_id=p.provider_id,
                country_code=_normalize_country(p.country_code),
                category=p.category,
                tags=list(p.tags or []),
            )
            self._rows[pid] = stored
            count += 1
        return count

    async def retrieve(
        self, scope: dict[str, Any], prefs: dict[str, Any] | None = None
    ) -> list[PlaceRecord]:
        prefs = prefs or {}
        bbox = scope.get("bbox")
        country = _normalize_country(scope.get("country_code"))
        if not bbox or len(bbox) != 4 or not country:
            return []
        min_lon, min_lat, max_lon, max_lat = (float(x) for x in bbox)
        category = prefs.get("category")
        tags = {str(t).lower() for t in (prefs.get("tags") or [])}
        out: list[PlaceRecord] = []
        for p in self._rows.values():
            if _normalize_country(p.country_code) != country:
                continue
            if not (min_lon <= p.lon <= max_lon and min_lat <= p.lat <= max_lat):
                continue
            if category and p.category != category:
                continue
            if tags and not tags.intersection({str(t).lower() for t in (p.tags or [])}):
                continue
            out.append(p)
        return out
