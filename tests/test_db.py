from pathlib import Path

from src.db.base import Base
from src.db.session import get_engine, get_session, get_sessionmaker, ping_db


def test_session_factory_importable() -> None:
    assert callable(get_engine)
    assert callable(get_sessionmaker)
    assert callable(get_session)
    assert callable(ping_db)


def test_alembic_env_points_at_metadata() -> None:
    env_text = Path("alembic/env.py").read_text(encoding="utf-8")
    assert "target_metadata = Base.metadata" in env_text
    assert Base.metadata is not None
