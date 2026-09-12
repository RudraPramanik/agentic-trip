"""In-process GenerateRunner with cooperative abort and wall-clock timeout."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from src.modules.agents.generate import GenerateDeps, GenerateResult, run_generate
from src.modules.chat.service import SseEvent
from src.ports import GenerateRunner


@dataclass
class _RunState:
    abort_requested: bool = False
    abort_reason: str | None = None
    started_at: float = field(default_factory=time.monotonic)
    queue: asyncio.Queue[SseEvent | None] = field(default_factory=asyncio.Queue)
    task: asyncio.Task[GenerateResult] | None = None
    result: GenerateResult | None = None


class InProcessGenerateRunner(GenerateRunner):
    def __init__(
        self,
        deps_factory: Any,
        *,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._deps_factory = deps_factory
        self._timeout_seconds = float(timeout_seconds)
        self._runs: dict[str, _RunState] = {}
        self._lock = asyncio.Lock()

    async def start(self, session_id: str) -> AsyncIterator[SseEvent]:
        async with self._lock:
            existing = self._runs.get(session_id)
            if existing and existing.task and not existing.task.done():
                # Re-attach to in-flight run
                run = existing
            else:
                run = _RunState()
                self._runs[session_id] = run
                deps: GenerateDeps = await self._maybe_await(
                    self._deps_factory(session_id)
                )
                run.task = asyncio.create_task(
                    self._execute(session_id, run, deps),
                    name=f"generate:{session_id}",
                )

        assert run.task is not None
        try:
            while True:
                if run.task.done() and run.queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(run.queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    if run.task.done():
                        continue
                    continue
                if event is None:
                    break
                yield event
        finally:
            # Drain terminal if producer finished without sentinel consumed
            if run.result and run.queue.empty():
                pass

    async def abort(self, session_id: str) -> dict[str, Any]:
        async with self._lock:
            run = self._runs.get(session_id)
            if run is None:
                run = _RunState(abort_requested=True, abort_reason="abort_requested")
                self._runs[session_id] = run
            else:
                run.abort_requested = True
                run.abort_reason = run.abort_reason or "abort_requested"
        return {"abort_requested": True}

    async def _execute(
        self, session_id: str, run: _RunState, deps: GenerateDeps
    ) -> GenerateResult:
        async def on_progress(stage: str, extra: dict[str, Any]) -> None:
            await run.queue.put(
                SseEvent(event="progress", data={"stage": stage, **extra})
            )

        def abort_check() -> bool:
            if run.abort_requested:
                return True
            if time.monotonic() - run.started_at >= self._timeout_seconds:
                run.abort_requested = True
                run.abort_reason = "timeout"
                return True
            return False

        # Timeout watchdog shares abort path
        async def watchdog() -> None:
            while not run.task.done() if run.task else True:
                if time.monotonic() - run.started_at >= self._timeout_seconds:
                    run.abort_requested = True
                    run.abort_reason = "timeout"
                    return
                await asyncio.sleep(0.2)

        watch = asyncio.create_task(watchdog())
        try:
            result = await run_generate(
                session_id,
                deps,
                abort_check=abort_check,
                on_progress=on_progress,
            )
            if result.status == "aborted" and run.abort_reason == "timeout":
                result.reason = "timeout"
            run.result = result
            if result.status == "done":
                await run.queue.put(
                    SseEvent(
                        event="done",
                        data={
                            "itinerary": result.itinerary,
                            "validation": result.validation,
                        },
                    )
                )
            elif result.status == "aborted":
                await run.queue.put(
                    SseEvent(
                        event="aborted",
                        data={
                            "reason": result.reason or run.abort_reason or "abort_requested"
                        },
                    )
                )
            else:
                await run.queue.put(
                    SseEvent(
                        event="error",
                        data={
                            "code": result.error or "generate_failed",
                            "validation": result.validation,
                        },
                    )
                )
            return result
        finally:
            watch.cancel()
            await run.queue.put(None)

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        if asyncio.iscoroutine(value):
            return await value
        return value
