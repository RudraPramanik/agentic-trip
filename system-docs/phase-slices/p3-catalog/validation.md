# P3 Catalog acquire + retrieve — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P3.1 | [x] Place migration + bbox query |
| P3.2 | [x] Facade mock + down → empty/partial |
| P3.3 | [x] acquire uses region/hubs |
| P3.4 | [x] ARQ success + failure status |
| P3.5 | [x] retrieve ids or empty; country filter |
| P3.6 | [x] catalog HTTP ASGI |
| P3.7 | [x] retrieve span or no-op |
| P3.8 | [x] readiness + honest empty tests |

## Checks

- [x] acquire job success + failure paths
- [x] country filter excludes foreign POIs
- [x] retrieve span emitted or fail-soft

## CI

- [x] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p3-catalog` tasks complete (when that change exists)

## Manual FE note (P3.6 optional)

After scope lock, chat shell shows **Acquire places**; readiness/status updates via `GET .../catalog` (no Build plan CTA).
