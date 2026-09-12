from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.settings import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None

READY_PING_TIMEOUT_SECONDS = 5.0


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_sessionmaker()
    async with factory() as session:
        yield session


async def ping_db() -> bool:
    """Return True if the database accepts a short ping. Never raises to the caller."""
    import asyncio

    engine = get_engine()
    try:
        async with engine.connect() as connection:
            await asyncio.wait_for(
                connection.execute(text("SELECT 1")),
                timeout=READY_PING_TIMEOUT_SECONDS,
            )
        return True
    except Exception:
        return False


def reset_engine() -> None:
    global _engine, _sessionmaker
    _engine = None
    _sessionmaker = None
