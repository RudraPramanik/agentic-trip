import pytest
from pydantic import ValidationError

from src.core.settings import Settings, get_settings


def test_missing_database_url_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    locations = [error["loc"] for error in exc_info.value.errors()]
    assert any("database_url" in location for location in locations)


def test_missing_langfuse_keys_are_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://at:at@localhost:5432/at")
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    get_settings.cache_clear()
    settings = Settings(_env_file=None)
    assert settings.database_url
    assert settings.langfuse_public_key is None
    assert settings.langfuse_secret_key is None
    assert settings.llm_api_key is None
    assert settings.apply_schema_on_boot is False
