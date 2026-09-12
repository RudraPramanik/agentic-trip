"""Generate pipeline: retrieve → pack → validate → narrative → persist_draft."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from src.modules.catalog.service import CatalogService, RetrieveResult
from src.modules.planner import (
    Itinerary,
    ValidateResult,
    validate_itinerary,
    write_narrative,
)
from src.modules.trips import TripPersistError, TripService
from src.ports import LlmGateway, ObsPort, TravelEngine

AbortCheck = Callable[[], bool]
ProgressCb = Callable[[str, dict[str, Any]], Awaitable[None] | None]


@dataclass
class GenerateResult:
    status: str  # done | error | aborted
    itinerary: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    error: str | None = None
    reason: str | None = None


@dataclass
class GenerateDeps:
    catalog: CatalogService
    engine: TravelEngine
    trips: TripService
    llm: LlmGateway
    obs: ObsPort
    sessions_get: Callable[[str], Awaitable[Any]]


async def run_generate(
    session_id: str,
    deps: GenerateDeps,
    *,
    abort_check: AbortCheck | None = None,
    on_progress: ProgressCb | None = None,
) -> GenerateResult:
    """Orchestrate generate stages. Services/ports only — no vendor HTTP/SQL here."""

    async def progress(stage: str, **extra: Any) -> None:
        if on_progress is None:
            return
        maybe = on_progress(stage, extra)
        if maybe is not None:
            await maybe

    def aborted() -> bool:
        return bool(abort_check and abort_check())

    with deps.obs.start_trace("generate.run", session_id=session_id):
        try:
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            state = await deps.sessions_get(session_id)
            if state is None:
                return GenerateResult(status="error", error="session_not_found")
            trip_scope = getattr(state, "trip_scope", None) or {}
            if not trip_scope:
                return GenerateResult(status="error", error="missing_trip_scope")

            intent = getattr(state, "intent", None) or {}
            prefs: dict[str, Any] = {}
            if isinstance(intent, dict) and intent.get("duration_days") is not None:
                prefs["day_budget"] = intent["duration_days"]
            # Do not pass vibe as retrieve category — that would empty the catalog.

            await progress("retrieve")
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            with deps.obs.span("generate.retrieve", session_id=session_id):
                retrieved: RetrieveResult = await deps.catalog.retrieve(
                    trip_scope, prefs
                )

            if retrieved.empty or not retrieved.places:
                with deps.obs.span(
                    "generate.outcome", status="error", error="empty_retrieve"
                ):
                    pass
                return GenerateResult(status="error", error="empty_retrieve")

            await progress("pack", place_count=len(retrieved.places))
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            with deps.obs.span("generate.pack", session_id=session_id):
                itinerary = deps.engine.pack(trip_scope, retrieved.places, prefs)
                if not isinstance(itinerary, Itinerary):
                    itinerary = Itinerary.from_dict(dict(itinerary))

            await progress("validate")
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            catalog_ids = set(retrieved.place_ids)
            place_countries = {
                str(p["id"]): p.get("country_code")
                for p in retrieved.places
                if p.get("id")
            }
            with deps.obs.span("generate.validate", session_id=session_id):
                validation = validate_itinerary(
                    itinerary,
                    catalog_ids,
                    trip_scope,
                    day_budget=prefs.get("day_budget"),
                    place_countries=place_countries,
                )

            if not validation.ok:
                with deps.obs.span(
                    "generate.outcome",
                    status="error",
                    error="validation_failed",
                ):
                    pass
                return GenerateResult(
                    status="error",
                    error="validation_failed",
                    validation=validation.to_dict(),
                    itinerary=itinerary.to_dict(),
                )

            await progress("narrative")
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            with deps.obs.span("generate.narrative", session_id=session_id):
                itinerary = await write_narrative(itinerary, deps.llm)

            await progress("persist")
            if aborted():
                return GenerateResult(status="aborted", reason="abort_requested")

            with deps.obs.span("generate.persist", session_id=session_id):
                try:
                    await deps.trips.persist_draft(
                        session_id, itinerary, validation, aborted=False
                    )
                except TripPersistError as exc:
                    with deps.obs.span(
                        "generate.outcome", status="error", error=str(exc)
                    ):
                        pass
                    return GenerateResult(status="error", error=str(exc))

            with deps.obs.span("generate.outcome", status="done"):
                pass
            await progress("done")
            return GenerateResult(
                status="done",
                itinerary=itinerary.to_dict(),
                validation=validation.to_dict(),
            )
        except Exception as exc:  # honest fail; still traced via outer span
            with deps.obs.span("generate.outcome", status="error", error=type(exc).__name__):
                pass
            return GenerateResult(status="error", error=type(exc).__name__)
