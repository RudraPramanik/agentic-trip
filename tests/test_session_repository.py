import pytest

from src.db.session import get_sessionmaker, ping_db
from src.modules.chat.models import TripSessionState
from src.modules.chat.repository import SqlSessionRepository


@pytest.mark.asyncio
async def test_session_repository_save_load_round_trip() -> None:
    if not await ping_db():
        pytest.skip("PostGIS not reachable (optional locally; required in CI)")

    factory = get_sessionmaker()
    async with factory() as db:
        # Ensure table exists for local runs without alembic.
        from src.db.base import Base
        from src.db.session import get_engine

        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        repo = SqlSessionRepository(db)
        created = await repo.create(guest_id="guest-repo-1")
        created.messages = [{"role": "user", "content": "hi"}]
        await repo.save(created)

    async with factory() as db:
        repo = SqlSessionRepository(db)
        loaded = await repo.get(created.session_id)
        assert loaded is not None
        assert isinstance(loaded, TripSessionState)
        assert loaded.guest_id == "guest-repo-1"
        assert loaded.messages == [{"role": "user", "content": "hi"}]
        assert loaded.itinerary is None
