"""API process entry: optional Alembic upgrade, then uvicorn.

``create_app()`` does not migrate — unit tests must not apply schema.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from src.core.settings import get_settings


def _alembic_ini() -> Path:
    return Path(__file__).resolve().parents[1] / "alembic.ini"


def apply_schema() -> None:
    command.upgrade(Config(str(_alembic_ini())), "head")


def apply_schema_if_requested() -> None:
    if not get_settings().apply_schema_on_boot:
        return
    apply_schema()


def main() -> None:
    apply_schema_if_requested()
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
