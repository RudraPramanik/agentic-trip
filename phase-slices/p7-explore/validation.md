# P7 Explore — validation gate

A slice is **done** only when all checks below pass. Then proceed to the next phase-slice.

## Checks

- [ ] last-trip locked without save
- [ ] IP approximate labeling
- [ ] no fake POI ids

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- Proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p7-explore` tasks complete (when that change exists)
