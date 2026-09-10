# P2 Dialogue + TripScope + HITL — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] Golden scope classification cases
- [ ] HITL interrupt resume with choice
- [ ] geo gateway fail-soft tests

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p2-dialogue-scope` tasks complete (when that change exists)
