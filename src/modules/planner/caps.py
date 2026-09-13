"""Revise loop / walk / day cap checker — hard gate before another generate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Keep in sync with pack_days defaults (engine.py).
DEFAULT_MAX_STOPS_PER_DAY = 4
DEFAULT_DAY_TRAVEL_BUDGET_S = 4 * 3600.0
DEFAULT_REVISE_MAX_LOOPS = 3


@dataclass
class ReviseCaps:
    max_loops: int = DEFAULT_REVISE_MAX_LOOPS
    max_stops_per_day: int = DEFAULT_MAX_STOPS_PER_DAY
    day_travel_budget_s: float = DEFAULT_DAY_TRAVEL_BUDGET_S
    day_budget: int = 3


@dataclass
class CapCheckResult:
    ok: bool
    reason: str | None = None
    message: str | None = None
    prefs: dict[str, Any] = field(default_factory=dict)


def Ok(*, prefs: dict[str, Any] | None = None) -> CapCheckResult:
    return CapCheckResult(ok=True, prefs=dict(prefs or {}))


def StopAndExplain(reason: str, message: str) -> CapCheckResult:
    return CapCheckResult(ok=False, reason=reason, message=message, prefs={})


def _run_dict(state: Any) -> dict[str, Any]:
    raw = getattr(state, "run", None)
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(state, dict) and isinstance(state.get("run"), dict):
        return dict(state["run"])
    return {}


def _itinerary_dict(state: Any) -> dict[str, Any]:
    raw = getattr(state, "itinerary", None)
    if isinstance(raw, dict):
        return raw
    if isinstance(state, dict) and isinstance(state.get("itinerary"), dict):
        return state["itinerary"]
    return {}


def _set_run(state: Any, run: dict[str, Any]) -> None:
    if hasattr(state, "run"):
        state.run = run
    elif isinstance(state, dict):
        state["run"] = run


def ensure_revise_baseline(state: Any, caps: ReviseCaps | None = None) -> dict[str, Any]:
    """Snapshot walk/day/stop budgets on first successful generate (or first revise)."""
    caps = caps or ReviseCaps()
    run = _run_dict(state)
    existing = run.get("revise_baseline")
    if isinstance(existing, dict) and existing:
        return existing
    itin = _itinerary_dict(state)
    days = itin.get("days") or []
    day_budget = caps.day_budget
    if isinstance(days, list) and days:
        day_budget = len(days)
    baseline = {
        "max_stops_per_day": caps.max_stops_per_day,
        "day_travel_budget_s": caps.day_travel_budget_s,
        "day_budget": day_budget,
    }
    run["revise_baseline"] = baseline
    run.setdefault("revise_loop_count", 0)
    _set_run(state, run)
    return baseline


def bump_revise_loop(state: Any) -> int:
    run = _run_dict(state)
    count = int(run.get("revise_loop_count") or 0) + 1
    run["revise_loop_count"] = count
    _set_run(state, run)
    return count


def check_caps(
    state: Any,
    patch: Any,
    *,
    caps: ReviseCaps | None = None,
    max_loops: int | None = None,
) -> CapCheckResult:
    """Enforce loop/walk/day budgets. Never raise caps silently.

    Failed and capped attempts still count (caller should bump before or after).
    This function reads the *already incremented* loop count when present, or
    treats the current attempt as count+1 if the caller has not bumped yet.
    """
    caps = caps or ReviseCaps()
    limit = int(max_loops if max_loops is not None else caps.max_loops)
    run = _run_dict(state)
    baseline = run.get("revise_baseline") if isinstance(run.get("revise_baseline"), dict) else None
    if not baseline:
        baseline = ensure_revise_baseline(state, caps)
        run = _run_dict(state)

    stored = int(run.get("revise_loop_count") or 0)
    # If caller already bumped, stored is this attempt; else this attempt is stored+1.
    attempt = stored if stored > 0 and run.get("_loop_bumped") else stored + 1
    if stored and run.get("_loop_bumped"):
        attempt = stored
    else:
        attempt = stored + 1

    if attempt > limit:
        return StopAndExplain(
            "loop_cap",
            "Revision loop cap reached. The last valid plan is unchanged.",
        )

    base_stops = int(baseline.get("max_stops_per_day") or caps.max_stops_per_day)
    base_walk = float(baseline.get("day_travel_budget_s") or caps.day_travel_budget_s)
    base_days = int(baseline.get("day_budget") or caps.day_budget)

    factor = getattr(patch, "walk_budget_factor", None)
    max_stops = getattr(patch, "max_stops_per_day", None)
    travel_s = getattr(patch, "day_travel_budget_s", None)
    day_budget = getattr(patch, "day_budget", None)
    day_index = getattr(patch, "day_index", None)

    if factor is not None and float(factor) > 1.0:
        return StopAndExplain(
            "cap_raise",
            "Walk budget cannot be raised above the original plan cap.",
        )
    if max_stops is not None and int(max_stops) > base_stops:
        return StopAndExplain(
            "cap_raise",
            "Stops-per-day cannot be raised above the original plan cap.",
        )
    if travel_s is not None and float(travel_s) > base_walk:
        return StopAndExplain(
            "cap_raise",
            "Day travel budget cannot be raised above the original plan cap.",
        )
    if day_budget is not None and int(day_budget) > base_days:
        return StopAndExplain(
            "cap_raise",
            "Day count cannot be raised above the original plan cap.",
        )

    prefs: dict[str, Any] = {}
    drop_ids = list(getattr(patch, "drop_place_ids", None) or [])
    if drop_ids:
        prefs["drop_place_ids"] = [str(x) for x in drop_ids]
    tags = list(getattr(patch, "tags", None) or [])
    if tags:
        prefs["tags"] = [str(t) for t in tags]
    category = getattr(patch, "category", None)
    if category:
        prefs["category"] = str(category)

    override: dict[str, Any] = {}
    if factor is not None and float(factor) < 1.0:
        override["day_travel_budget_s"] = base_walk * float(factor)
    if max_stops is not None:
        override["max_stops_per_day"] = int(max_stops)
    if travel_s is not None:
        override["day_travel_budget_s"] = float(travel_s)

    if day_index is not None and override:
        prefs["day_overrides"] = {int(day_index): override}
    elif override:
        prefs.update(override)

    return Ok(prefs=prefs)
