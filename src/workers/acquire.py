"""ARQ worker jobs for catalog acquire."""

from __future__ import annotations

import os
from typing import Any

from arq.connections import RedisSettings

from src.core.settings import get_settings
from src.db.session import get_sessionmaker
from src.modules.auth import CookieAuthAdapter
from src.modules.catalog.adapters import OtmAdapter, OverpassAdapter
from src.modules.catalog.facade import DefaultPlacesFacade
from src.modules.catalog.queue import InlineAcquireQueue
from src.modules.catalog.repository import SqlPlaceRepository
from src.modules.catalog.service import CatalogService
from src.modules.chat.repository import SqlSessionRepository
from src.modules.monitor import NoOpObs


async def acquire_catalog(ctx: dict[str, Any], session_id: str) -> dict[str, Any]:
    """Bounded ARQ job — calls CatalogService.acquire."""
    factory = get_sessionmaker()
    settings = get_settings()
    async with factory() as db:
        service = CatalogService(
            auth=CookieAuthAdapter(),
            sessions=SqlSessionRepository(db),
            places=SqlPlaceRepository(db),
            facade=DefaultPlacesFacade(
                overpass=OverpassAdapter(
                    base_url=settings.overpass_base_url,
                    timeout_seconds=settings.overpass_timeout_seconds,
                    user_agent=settings.places_user_agent,
                ),
                otm=OtmAdapter(
                    base_url=settings.otm_base_url,
                    api_key=settings.otm_api_key,
                    timeout_seconds=settings.otm_timeout_seconds,
                    user_agent=settings.places_user_agent,
                ),
            ),
            queue=InlineAcquireQueue(),
            obs=NoOpObs(),
        )
        try:
            result = await service.acquire(session_id)
            return {
                "status": result.status,
                "place_count": result.place_count,
                "error": result.error,
            }
        except Exception:
            await service.mark_failed(session_id, error="job_failed")
            raise


class WorkerSettings:
    """ARQ worker settings — `arq src.workers.acquire.WorkerSettings`."""

    functions = [acquire_catalog]
    max_tries = 3
    job_timeout = 300
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://localhost:6379")
    )
