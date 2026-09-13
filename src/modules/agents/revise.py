"""Revise graph: parse intent → caps → re-enter generate (P6)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from src.modules.agents.generate import GenerateDeps, GenerateResult, run_generate
from src.modules.llm.types import LlmUnavailable
from src.modules.planner.caps import (
    DEFAULT_REVISE_MAX_LOOPS,
    bump_revise_loop,
    check_caps,
    ensure_revise_baseline,
)
from src.modules.planner.types import Itinerary
from src.ports import LlmGateway, ObsPort

REVISION_INTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "day_index": {"type": ["integer", "null"]},
        "walk_budget_factor": {"type": ["number", "null"]},
        "max_stops_per_day": {"type": ["integer", "null"]},
        "day_travel_budget_s": {"type": ["number", "null"]},
        "drop_place_ids": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "category": {"type": ["string", "null"]},
        "unknown_names": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}

_DAY_RE = re.compile(r"\bday\s+(\d+)\b", re.IGNORECASE)
_ADD_RE = re.compile(
    r"\b(?:add|include|visit)\s+[\"']?([A-Za-z][A-Za-z0-9 '\-]{1,40})[\"']?",
    re.IGNORECASE,
)
_QUOTED_RE = re.compile(r"[\"']([A-Za-z][^\"']{1,40})[\"']")


@dataclass
class RevisionIntent:
    """Structured prefs / day-constraint patch — never a new itinerary."""

    day_index: int | None = None
    walk_budget_factor: float | None = None
    max_stops_per_day: int | None = None
    day_travel_budget_s: float | None = None
    day_budget: int | None = None
    drop_place_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    category: str | None = None
    unknown_names: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "walk_budget_factor": self.walk_budget_factor,
            "max_stops_per_day": self.max_stops_per_day,
            "day_travel_budget_s": self.day_travel_budget_s,
            "drop_place_ids": list(self.drop_place_ids),
            "tags": list(self.tags),
            "category": self.category,
            "unknown_names": list(self.unknown_names),
        }


@dataclass
class ReviseDeps:
    generate: GenerateDeps
    sessions_save: Callable[[Any], Awaitable[Any]]
    max_loops: int = DEFAULT_REVISE_MAX_LOOPS


def _itinerary_from(itinerary: Itinerary | dict[str, Any] | None) -> Itinerary:
    if itinerary is None:
        return Itinerary()
    if isinstance(itinerary, Itinerary):
        return itinerary
    return Itinerary.from_dict(dict(itinerary))


def _known_place_ids(itin: Itinerary) -> set[str]:
    return {s.place_id for d in itin.days for s in d.stops} | set(itin.place_ids)


def _known_names(itin: Itinerary) -> set[str]:
    names = {s.name.strip().lower() for d in itin.days for s in d.stops if s.name}
    return {n for n in names if n}


def _sanitize_patch(raw: dict[str, Any], itin: Itinerary) -> RevisionIntent:
    """Keep only patch fields. Ignore days/stops/itinerary rewrite from the model."""
    known_ids = _known_place_ids(itin)
    known_names = _known_names(itin)
    drop: list[str] = []
    unknown: list[str] = [str(n) for n in (raw.get("unknown_names") or []) if str(n).strip()]
    for pid in raw.get("drop_place_ids") or []:
        sid = str(pid)
        if sid in known_ids:
            drop.append(sid)
        else:
            unknown.append(sid)

    day_index = raw.get("day_index")
    try:
        day_index_i = int(day_index) if day_index is not None else None
    except (TypeError, ValueError):
        day_index_i = None
    valid_days = {d.day_index for d in itin.days}
    if day_index_i is not None and valid_days and day_index_i not in valid_days:
        day_index_i = None

    factor = raw.get("walk_budget_factor")
    try:
        factor_f = float(factor) if factor is not None else None
    except (TypeError, ValueError):
        factor_f = None

    max_stops = raw.get("max_stops_per_day")
    try:
        max_stops_i = int(max_stops) if max_stops is not None else None
    except (TypeError, ValueError):
        max_stops_i = None

    # Dedup unknown; drop names that are already scheduled (not unknown).
    cleaned_unknown: list[str] = []
    seen: set[str] = set()
    for name in unknown:
        key = name.strip().lower()
        if not key or key in seen or key in known_names or name in known_ids:
            continue
        seen.add(key)
        cleaned_unknown.append(name.strip())

    return RevisionIntent(
        day_index=day_index_i,
        walk_budget_factor=factor_f,
        max_stops_per_day=max_stops_i,
        day_travel_budget_s=_maybe_float(raw.get("day_travel_budget_s")),
        drop_place_ids=drop,
        tags=[str(t) for t in (raw.get("tags") or [])],
        category=str(raw["category"]) if raw.get("category") else None,
        unknown_names=cleaned_unknown,
    )


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _heuristic_parse(text: str, itin: Itinerary) -> RevisionIntent:
    raw = (text or "").strip()
    day_m = _DAY_RE.search(raw)
    day_index = int(day_m.group(1)) if day_m else None
    valid_days = {d.day_index for d in itin.days}
    if day_index is not None and valid_days and day_index not in valid_days:
        day_index = None

    walk_factor = None
    max_stops = None
    lowered = raw.lower()
    if "less walking" in lowered or "less walk" in lowered or "fewer walks" in lowered:
        walk_factor = 0.6
        max_stops = 2

    unknown: list[str] = []
    known_names = _known_names(itin)
    for match in list(_ADD_RE.finditer(raw)) + list(_QUOTED_RE.finditer(raw)):
        name = match.group(1).strip().rstrip(".,!")
        if name.lower() not in known_names and name.lower() not in {
            "day",
            "walking",
            "walk",
        }:
            unknown.append(name)

    intent = RevisionIntent(
        day_index=day_index,
        walk_budget_factor=walk_factor,
        max_stops_per_day=max_stops,
        unknown_names=unknown,
    )
    if walk_factor is None and max_stops is None and not unknown and day_index is None:
        intent.error = "unparsed_revision"
    return intent


def _coerce_json(result: Any) -> dict[str, Any] | None:
    if isinstance(result, dict):
        # Never accept a whole-trip rewrite payload as the patch.
        cleaned = {
            k: v
            for k, v in result.items()
            if k
            not in {
                "days",
                "stops",
                "itinerary",
                "place_ids",
                "story",
                "narratives",
            }
        }
        return cleaned
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}")
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(result[start : end + 1])
                except json.JSONDecodeError:
                    return None
            else:
                return None
        return parsed if isinstance(parsed, dict) else None
    if hasattr(result, "content"):
        return _coerce_json(result.content)
    return None


async def parse_revision_intent(
    text: str,
    itinerary: Itinerary | dict[str, Any] | None,
    llm: LlmGateway,
) -> RevisionIntent:
    """Schema-first LLM patch; heuristic fail-soft when the gateway is unavailable."""
    itin = _itinerary_from(itinerary)
    raw_text = (text or "").strip()
    if not raw_text:
        return RevisionIntent(error="empty_text")

    messages = [
        {
            "role": "system",
            "content": (
                "Extract a revision patch as JSON. Keys: day_index, walk_budget_factor "
                "(<1 for less walking), max_stops_per_day, drop_place_ids (only ids "
                "already on the itinerary), tags, category, unknown_names. "
                "Do not invent days, stops, coordinates, or a rewritten itinerary."
            ),
        },
        {"role": "user", "content": raw_text},
    ]
    try:
        result = await llm.complete("dialogue", messages, schema=REVISION_INTENT_SCHEMA)
    except Exception:
        result = None
    if result is not None and not isinstance(result, LlmUnavailable):
        data = _coerce_json(result)
        if data is not None:
            intent = _sanitize_patch(data, itin)
            if _has_patch_signal(intent):
                return intent
    return _heuristic_parse(raw_text, itin)


def _has_patch_signal(intent: RevisionIntent) -> bool:
    return any(
        [
            intent.day_index is not None,
            intent.walk_budget_factor is not None,
            intent.max_stops_per_day is not None,
            intent.day_travel_budget_s is not None,
            bool(intent.drop_place_ids),
            bool(intent.tags),
            bool(intent.category),
        ]
    )


async def run_revise(
    session_id: str,
    text: str,
    deps: ReviseDeps,
    *,
    abort_check: Callable[[], bool] | None = None,
    on_progress: Callable[[str, dict[str, Any]], Awaitable[None] | None] | None = None,
) -> GenerateResult:
    """parse → caps → reuse generate stages. Services/ports only."""

    async def progress(stage: str, **extra: Any) -> None:
        if on_progress is None:
            return
        maybe = on_progress(stage, extra)
        if maybe is not None:
            await maybe

    def aborted() -> bool:
        return bool(abort_check and abort_check())

    obs: ObsPort = deps.generate.obs
    with obs.start_trace("revise.run", session_id=session_id):
        if aborted():
            return GenerateResult(status="aborted", reason="abort_requested")

        state = await deps.generate.sessions_get(session_id)
        if state is None:
            return GenerateResult(status="error", error="session_not_found")
        itinerary = getattr(state, "itinerary", None)
        if not itinerary:
            with obs.span("revise.outcome", status="error", error="missing_draft"):
                pass
            return GenerateResult(status="error", error="missing_draft")

        last_valid = dict(itinerary) if isinstance(itinerary, dict) else itinerary
        last_trip_id = getattr(state, "trip_id", None)
        ensure_revise_baseline(state)
        await deps.sessions_save(state)

        await progress("parse")
        if aborted():
            return GenerateResult(status="aborted", reason="abort_requested")

        with obs.span("revise.parse", session_id=session_id):
            intent = await parse_revision_intent(text, itinerary, deps.generate.llm)

        if intent.error == "empty_text":
            return GenerateResult(status="error", error="empty_text")

        bump_revise_loop(state)
        run = dict(getattr(state, "run", None) or {})
        run["_loop_bumped"] = True
        state.run = run
        await deps.sessions_save(state)

        await progress("caps")
        if aborted():
            return GenerateResult(status="aborted", reason="abort_requested")

        with obs.span("revise.caps", session_id=session_id):
            cap = check_caps(state, intent, max_loops=deps.max_loops)

        if not cap.ok:
            with obs.span(
                "revise.outcome",
                status="error",
                error=cap.reason or "cap_hit",
            ):
                pass
            # Last valid itinerary unchanged (only loop count/baseline written).
            return GenerateResult(
                status="error",
                error=cap.reason or "cap_hit",
                itinerary=last_valid if isinstance(last_valid, dict) else None,
            )

        state.budget = "revise"
        await deps.sessions_save(state)

        extra = dict(cap.prefs)
        result = await run_generate(
            session_id,
            deps.generate,
            abort_check=abort_check,
            on_progress=on_progress,
            extra_prefs=extra,
        )

        after = await deps.generate.sessions_get(session_id)
        if after is not None:
            if result.status != "done":
                # Keep last valid if generate refused persist.
                if after.itinerary != last_valid and result.status != "done":
                    # persist_draft only writes on success; nothing to restore.
                    pass
            after.budget = "dialogue"
            await deps.sessions_save(after)
            if result.status == "done":
                result.trip_id = after.trip_id or last_trip_id
        return result
