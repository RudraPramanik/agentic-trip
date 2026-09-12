from src.boot import apply_schema, apply_schema_if_requested
from src.core.settings import Settings, get_settings
from src.main import create_app


def test_apply_schema_on_boot_defaults_false() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://at:at@localhost:5432/at",
    )
    assert settings.apply_schema_on_boot is False


def test_apply_schema_skipped_when_flag_false(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://at:at@localhost:5432/at")
    monkeypatch.delenv("APPLY_SCHEMA_ON_BOOT", raising=False)
    get_settings.cache_clear()
    called: list[str] = []
    monkeypatch.setattr(
        "src.boot.apply_schema",
        lambda: called.append("upgrade"),
    )
    apply_schema_if_requested()
    assert called == []


def test_apply_schema_runs_when_flag_true(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://at:at@localhost:5432/at")
    monkeypatch.setenv("APPLY_SCHEMA_ON_BOOT", "true")
    get_settings.cache_clear()
    called: list[str] = []
    monkeypatch.setattr(
        "src.boot.apply_schema",
        lambda: called.append("upgrade"),
    )
    apply_schema_if_requested()
    assert called == ["upgrade"]
    get_settings.cache_clear()


def test_apply_schema_invokes_alembic_head(monkeypatch) -> None:
    revs: list[str] = []
    monkeypatch.setattr(
        "src.boot.command.upgrade",
        lambda _cfg, rev: revs.append(rev),
    )
    apply_schema()
    assert revs == ["head"]


def test_create_app_does_not_migrate(monkeypatch) -> None:
    called: list[str] = []
    monkeypatch.setattr(
        "src.boot.apply_schema",
        lambda: called.append("upgrade"),
    )
    monkeypatch.setattr(
        "alembic.command.upgrade",
        lambda *_args, **_kwargs: called.append("alembic"),
    )
    create_app()
    assert called == []
