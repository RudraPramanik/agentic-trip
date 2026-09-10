# P5 Guidebook UI + map + export DTO — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] export DTO schema test
- [ ] map points without fake polyline
- [ ] FE render smoke if applicable

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p5-guidebook-map` tasks complete (when that change exists)
