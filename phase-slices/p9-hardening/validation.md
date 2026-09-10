# P9 Hardening — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] full golden harness
- [ ] rate limit / cost cap unit tests
- [ ] abort under load smoke

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p9-hardening` tasks complete (when that change exists)
