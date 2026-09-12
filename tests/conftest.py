"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://at:at@localhost:5432/at",
)
# Keep guest cookies non-Secure for ASGI TestClient (matches Settings.environment=local).
os.environ.setdefault("ENVIRONMENT", "local")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from src.core.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
