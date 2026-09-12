# P5 Guidebook UI + map + export DTO — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P5.1 | [x] GuidebookExport schema (`tests/test_trips.py`) |
| P5.2 | [x] GET trip + export ASGI (`tests/test_trips_api.py`) |
| P5.3 | [x] FE guidebook days (smoke notes in `frontend/GUIDEBOOK.md`) |
| P5.4 | [x] map points without fake polyline; v1 points-only unless later geometry exists (`TripMap` + export omits `route_geometry`) |
| P5.5 | [x] empty booking UI no prices (`BookingPlaceholder`) |
| P5.6 | [x] media not on generate path (`tests/test_media_stub.py`) |

## Checks

- [x] export DTO schema test
- [x] map points without fake polyline
- [x] FE render smoke if applicable (`frontend/GUIDEBOOK.md`)

## CI

- [x] Job or documented script runs these checks (`.github/workflows/ci.yml` → `uv run pytest`)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p5-guidebook-map` tasks complete (when that change exists)
