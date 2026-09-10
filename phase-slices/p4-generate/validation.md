# P4 Generate + engine + validate — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] no invented place ids golden
- [ ] validation gate unit tests
- [ ] SSE abort test
- [ ] GenerateRunner port smoke

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p4-generate` tasks complete (when that change exists)
