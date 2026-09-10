# P5 Guidebook UI + map + export DTO — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P5.1 | [ ] GuidebookExport schema |
| P5.2 | [ ] GET trip + export ASGI |
| P5.3 | [ ] FE guidebook days (smoke) |
| P5.4 | [ ] map points without fake polyline |
| P5.5 | [ ] empty booking UI no prices |
| P5.6 | [ ] media not on generate path |

## Checks

- [ ] export DTO schema test
- [ ] map points without fake polyline
- [ ] FE render smoke if applicable

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p5-guidebook-map` tasks complete (when that change exists)
