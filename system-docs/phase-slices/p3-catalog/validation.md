# P3 Catalog acquire + retrieve — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P3.1 | [ ] Place migration + bbox query |
| P3.2 | [ ] Facade mock + down → empty/partial |
| P3.3 | [ ] acquire uses region/hubs |
| P3.4 | [ ] ARQ success + failure status |
| P3.5 | [ ] retrieve ids or empty; country filter |
| P3.6 | [ ] catalog HTTP ASGI |
| P3.7 | [ ] retrieve span or no-op |
| P3.8 | [ ] readiness + honest empty tests |

## Checks

- [ ] acquire job success + failure paths
- [ ] country filter excludes foreign POIs
- [ ] retrieve span emitted or fail-soft

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p3-catalog` tasks complete (when that change exists)
