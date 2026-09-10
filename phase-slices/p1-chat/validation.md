# P1 Chat — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] ASGI test: guest message round-trip
- [ ] trace id present or fail-soft
- [ ] no generate invoked on chat-only turn

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p1-chat` tasks complete (when that change exists)
