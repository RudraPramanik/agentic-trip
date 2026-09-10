# P3 Catalog acquire + retrieve — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] acquire job success + failure paths
- [ ] country filter excludes foreign POIs
- [ ] retrieve span emitted or fail-soft

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p3-catalog` tasks complete (when that change exists)
