from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AcquireQueueError(Exception):
    """Job queue unavailable (Redis/ARQ down)."""


class AcquireQueue(Protocol):
    async def enqueue_acquire(self, session_id: str) -> str:
        """Return job_id. Raise AcquireQueueError when queue is down."""
        ...


@dataclass
class InlineAcquireQueue:
    """Test/dev double: run acquire coroutine immediately (or fail)."""

    acquire_fn: Any = None
    fail: bool = False

    async def enqueue_acquire(self, session_id: str) -> str:
        if self.fail:
            raise AcquireQueueError("redis unavailable")
        if self.acquire_fn is not None:
            await self.acquire_fn(session_id)
        return f"inline:{session_id}"


class ArqAcquireQueue:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def enqueue_acquire(self, session_id: str) -> str:
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
        except ImportError as exc:  # pragma: no cover
            raise AcquireQueueError("arq not installed") from exc
        try:
            settings = RedisSettings.from_dsn(self._redis_url)
            pool = await create_pool(settings)
            try:
                job = await pool.enqueue_job("acquire_catalog", session_id)
                if job is None:
                    raise AcquireQueueError("enqueue returned no job")
                return str(job.job_id)
            finally:
                await pool.aclose()
        except AcquireQueueError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise AcquireQueueError(str(exc) or "redis unavailable") from exc
