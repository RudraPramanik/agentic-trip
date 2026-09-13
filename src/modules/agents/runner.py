"""In-process GenerateRunner with cooperative abort, timeout, and revise."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from src.modules.agents.generate import GenerateDeps, GenerateResult, run_generate
from src.modules.agents.revise import ReviseDeps, run_revise
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
    kind: str = "generate"
    text: str = ""


class InProcessGenerateRunner(GenerateRunner):
    def __init__(
        self,
        deps_factory: Any,
        *,
        timeout_seconds: float = 120.0,
        revise_timeout_seconds: float | None = None,
        revise_deps_factory: Any | None = None,
        max_revise_loops: int = 3,
    ) -> None:
        self._deps_factory = deps_factory
        self._revise_deps_factory = revise_deps_factory
        self._timeout_seconds = float(timeout_seconds)
        self._revise_timeout_seconds = float(
            revise_timeout_seconds if revise_timeout_seconds is not None else timeout_seconds
        )
        self._max_revise_loops = int(max_revise_loops)
        self._runs: dict[str, _RunState] = {}
        self._lock = asyncio.Lock()

    def _in_flight(self, session_id: str) -> _RunState | None:
        existing = self._runs.get(session_id)
        if existing and existing.task and not existing.task.done():
            return existing
        return None

    async def start(self, session_id: str) -> AsyncIterator[SseEvent]:
        refuse: SseEvent | None = None
        run: _RunState | None = None
        async with self._lock:
            existing = self._in_flight(session_id)
            if existing is not None:
                if existing.kind == "revise":
                    refuse = SseEvent(
                        event="error",
                        data={
                            "code": "run_in_progress",
                            "message": "A revise run is already in progress",
                        },
                    )
                else:
                    run = existing
            else:
                run = _RunState(kind="generate")
                self._runs[session_id] = run
                deps: GenerateDeps = await self._maybe_await(
                    self._deps_factory(session_id)
                )
                run.task = asyncio.create_task(
                    self._execute(session_id, run, deps),
                    name=f"generate:{session_id}",
                )
        if refuse is not None:
            yield refuse
            return
        assert run is not None
        async for event in self._consume(run):
            yield event

    async def start_revise(self, session_id: str, text: str) -> AsyncIterator[SseEvent]:
        refuse: SseEvent | None = None
        run: _RunState | None = None
        async with self._lock:
            existing = self._in_flight(session_id)
            if existing is not None:
                refuse = SseEvent(
                    event="error",
                    data={
                        "code": "run_in_progress",
                        "message": "A generate or revise run is already in progress",
                    },
                )
            else:
                run = _RunState(kind="revise", text=text)
                self._runs[session_id] = run
                factory = self._revise_deps_factory or self._deps_factory
                deps = await self._maybe_await(factory(session_id))
                run.task = asyncio.create_task(
                    self._execute_revise(session_id, run, deps, text),
                    name=f"revise:{session_id}",
                )
        if refuse is not None:
            yield refuse
            return
        assert run is not None
        async for event in self._consume(run):
            yield event

    async def _consume(self, run: _RunState) -> AsyncIterator[SseEvent]:
        assert run.task is not None
        try:
            while True:
                if run.task.done() and run.queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(run.queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                if event is None:
                    break
                yield event
        finally:
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

    def _timeout_for(self, run: _RunState) -> float:
        if run.kind == "revise":
            return self._revise_timeout_seconds
        return self._timeout_seconds

    async def _execute(
        self, session_id: str, run: _RunState, deps: GenerateDeps
    ) -> GenerateResult:
        return await self._safe_pipeline(
            run,
            lambda abort_check, on_progress: run_generate(
                session_id,
                deps,
                abort_check=abort_check,
                on_progress=on_progress,
            ),
        )

    async def _execute_revise(
        self, session_id: str, run: _RunState, deps: Any, text: str
    ) -> GenerateResult:
        if isinstance(deps, ReviseDeps):
            revise_deps = deps
        else:
            if not isinstance(deps, GenerateDeps):
                await run.queue.put(
                    SseEvent(
                        event="error",
                        data={"code": "revise_deps_unavailable"},
                    )
                )
                await run.queue.put(None)
                return GenerateResult(status="error", error="revise_deps_unavailable")
            sessions_save = getattr(deps, "sessions_save", None)
            if sessions_save is None:
                # Fall back: factory returned generate deps only.
                async def _no_save(_state: Any) -> Any:
                    return _state

                sessions_save = _no_save
            revise_deps = ReviseDeps(
                generate=deps,
                sessions_save=sessions_save,
                max_loops=self._max_revise_loops,
            )

        return await self._safe_pipeline(
            run,
            lambda abort_check, on_progress: run_revise(
                session_id,
                text,
                revise_deps,
                abort_check=abort_check,
                on_progress=on_progress,
            ),
        )

    async def _safe_pipeline(self, run: _RunState, work: Any) -> GenerateResult:
        try:
            result = await self._run_pipeline(run, work)
        except Exception as exc:
            result = GenerateResult(status="error", error=type(exc).__name__)
        await self._emit_result(run, result)
        return result

    async def _run_pipeline(
        self,
        run: _RunState,
        work: Any,
    ) -> GenerateResult:
        timeout = self._timeout_for(run)

        async def on_progress(stage: str, extra: dict[str, Any]) -> None:
            await run.queue.put(
                SseEvent(event="progress", data={"stage": stage, **extra})
            )

        def abort_check() -> bool:
            if run.abort_requested:
                return True
            if time.monotonic() - run.started_at >= timeout:
                run.abort_requested = True
                run.abort_reason = "timeout"
                return True
            return False

        async def watchdog() -> None:
            while not run.task.done() if run.task else True:
                if time.monotonic() - run.started_at >= timeout:
                    run.abort_requested = True
                    run.abort_reason = "timeout"
                    return
                await asyncio.sleep(0.2)

        watch = asyncio.create_task(watchdog())
        try:
            result = await work(abort_check, on_progress)
            if result.status == "aborted" and run.abort_reason == "timeout":
                result.reason = "timeout"
            run.result = result
            return result
        finally:
            watch.cancel()

    async def _emit_result(self, run: _RunState, result: GenerateResult) -> None:
        try:
            if result.status == "done":
                done_data: dict[str, Any] = {
                    "itinerary": result.itinerary,
                    "validation": result.validation,
                }
                if result.trip_id:
                    done_data["trip_id"] = result.trip_id
                await run.queue.put(SseEvent(event="done", data=done_data))
            elif result.status == "aborted":
                await run.queue.put(
                    SseEvent(
                        event="aborted",
                        data={
                            "reason": result.reason
                            or run.abort_reason
                            or "abort_requested"
                        },
                    )
                )
            else:
                payload: dict[str, Any] = {
                    "code": result.error or "generate_failed",
                    "validation": result.validation,
                }
                if result.error:
                    payload["message"] = result.error
                await run.queue.put(SseEvent(event="error", data=payload))
        finally:
            await run.queue.put(None)

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        if asyncio.iscoroutine(value):
            return await value
        return value
