"""Catalog place repository + country filter proofs (P3.1 / P3.5)."""

from __future__ import annotations

import pytest

from src.modules.catalog.models import PlaceRecord
from src.modules.catalog.repository import (
    InMemoryPlaceRepository,
    filter_places_by_country,
)


def test_filter_places_by_country_excludes_foreign_and_unknown() -> None:
    places = [
        PlaceRecord(
            name="A",
            lon=135.0,
            lat=35.0,
            provider="t",
            provider_id="1",
            country_code="jp",
        ),
        PlaceRecord(
            name="B",
            lon=135.1,
            lat=35.1,
            provider="t",
            provider_id="2",
            country_code="kr",
        ),
        PlaceRecord(
            name="C",
            lon=135.2,
            lat=35.2,
            provider="t",
            provider_id="3",
            country_code=None,
        ),
    ]
    kept = filter_places_by_country(places, "jp")
    assert [p.name for p in kept] == ["A"]
    assert filter_places_by_country(places, None) == []


@pytest.mark.asyncio
async def test_inmemory_upsert_and_bbox_retrieve_country_filter() -> None:
    repo = InMemoryPlaceRepository()
    await repo.upsert_many(
        [
            PlaceRecord(
                name="Fushimi",
                lon=135.77,
                lat=34.97,
                provider="overpass",
                provider_id="1",
                country_code="jp",
                category="tourism",
                tags=["shrine"],
            ),
            PlaceRecord(
                name="Busan Tower",
                lon=135.78,
                lat=34.98,
                provider="overpass",
                provider_id="2",
                country_code="kr",
                category="tourism",
            ),
        ]
    )
    scope = {
        "bbox": [135.6, 34.9, 135.9, 35.1],
        "country_code": "jp",
    }
    got = await repo.retrieve(scope, prefs={"category": "tourism"})
    assert len(got) == 1
    assert got[0].name == "Fushimi"
    assert got[0].id is not None

    empty = await repo.retrieve(
        {"bbox": [0.0, 0.0, 1.0, 1.0], "country_code": "jp"},
        prefs=None,
    )
    assert empty == []


@pytest.mark.asyncio
async def test_sql_place_repository_upsert_bbox_when_db_up() -> None:
    from src.db.session import get_engine, get_sessionmaker, ping_db

    if not await ping_db():
        pytest.skip("PostGIS not reachable (optional locally; required in CI)")

    from src.db.base import Base
    from src.modules.catalog.models import Place  # noqa: F401
    from src.modules.catalog.repository import SqlPlaceRepository
    from src.modules.chat.models import TripSessionState  # noqa: F401

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_sessionmaker()
    async with factory() as db:
        repo = SqlPlaceRepository(db)
        n = await repo.upsert_many(
            [
                PlaceRecord(
                    name="Kiyomizu",
                    lon=135.785,
                    lat=34.995,
                    provider="test",
                    provider_id="kiyomizu",
                    country_code="jp",
                    category="temple",
                    tags=["historic"],
                ),
                PlaceRecord(
                    name="Foreign",
                    lon=135.786,
                    lat=34.996,
                    provider="test",
                    provider_id="foreign",
                    country_code="cn",
                    category="temple",
                ),
            ]
        )
        assert n == 2
        got = await repo.retrieve(
            {"bbox": [135.7, 34.9, 135.9, 35.1], "country_code": "jp"},
            prefs={"category": "temple"},
        )
        assert len(got) == 1
        assert got[0].name == "Kiyomizu"
