# P6 Revision — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P6.1 | [ ] parse revision intent unit |
| P6.2 | [ ] cap checker stop+keep last valid |
| P6.3 | [ ] revise_graph reuses engine |
| P6.4 | [ ] `POST .../revise` ASGI |
| P6.5 | [ ] less-walking-day-2 golden |

## Checks

- [ ] revision cap enforced
- [ ] structure updated golden

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p6-revision` tasks complete (when that change exists)
