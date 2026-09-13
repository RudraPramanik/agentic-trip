# P6 Revision — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P6.1 | [x] parse revision intent unit (`tests/test_revise_intent.py`) |
| P6.2 | [x] cap checker stop+keep last valid (`tests/test_revise_caps.py`) |
| P6.3 | [x] revise_graph reuses engine (`tests/test_revise.py`) |
| P6.4 | [x] `POST .../revise` ASGI (`tests/test_revise_api.py`) |
| P6.5 | [x] less-walking-day-2 golden (`tests/evals/test_revise_goldens.py`) |

## Checks

- [x] revision cap enforced
- [x] structure updated golden

## CI

- [x] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [x] Failures block merging/applying the next slice

`.github/workflows/ci.yml` runs `uv run pytest` (includes P6 unit/ASGI/goldens) and `frontend` `npm run test:e2e` (includes `e2e/revise-plan.spec.ts`). Local terminal: `uv run python scripts/smoke_revise.py`.

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p6-revision` tasks complete (when that change exists)
