"""P6.2 cap checker proofs."""

from __future__ import annotations

from types import SimpleNamespace

from src.modules.agents.revise import RevisionIntent
from src.modules.planner.caps import (
    ReviseCaps,
    bump_revise_loop,
    check_caps,
    ensure_revise_baseline,
)


def _state(*, loops: int = 0, bumped: bool = False) -> SimpleNamespace:
    itin = {
        "status": "draft",
        "days": [
            {"day_index": 1, "stops": [{"place_id": "a"}]},
            {"day_index": 2, "stops": [{"place_id": "b"}, {"place_id": "c"}]},
        ],
    }
    state = SimpleNamespace(itinerary=itin, run={})
    ensure_revise_baseline(state, ReviseCaps())
    state.run["revise_loop_count"] = loops
    if bumped:
        state.run["_loop_bumped"] = True
    return state


def test_loop_cap_stop_keeps_last_valid() -> None:
    state = _state(loops=4, bumped=True)
    last = dict(state.itinerary)
    patch = RevisionIntent(day_index=2, walk_budget_factor=0.6, max_stops_per_day=2)
    result = check_caps(state, patch, max_loops=3)
    assert result.ok is False
    assert result.reason == "loop_cap"
    assert state.itinerary == last


def test_silent_cap_raise_refused() -> None:
    state = _state(loops=1, bumped=True)
    last = dict(state.itinerary)
    patch = RevisionIntent(max_stops_per_day=99, walk_budget_factor=1.5)
    result = check_caps(state, patch, max_loops=3)
    assert result.ok is False
    assert result.reason == "cap_raise"
    assert state.itinerary == last


def test_less_walking_patch_ok_merges_day_overrides() -> None:
    state = _state(loops=1, bumped=True)
    patch = RevisionIntent(day_index=2, walk_budget_factor=0.6, max_stops_per_day=2)
    result = check_caps(state, patch, max_loops=3)
    assert result.ok is True
    assert 2 in result.prefs.get("day_overrides", {})
    over = result.prefs["day_overrides"][2]
    assert over["max_stops_per_day"] == 2
    assert over["day_travel_budget_s"] < state.run["revise_baseline"]["day_travel_budget_s"]


def test_bump_counts_failed_attempts() -> None:
    state = _state(loops=0)
    assert bump_revise_loop(state) == 1
    assert bump_revise_loop(state) == 2
    assert state.run["revise_loop_count"] == 2
