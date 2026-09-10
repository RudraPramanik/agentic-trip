# P8 Booking placeholder — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P8.1 | [ ] booking field on trip model |
| P8.2 | [ ] BookingService no HTTP |
| P8.3 | [ ] GET booking placeholder |
| P8.4 | [ ] FE placeholder no prices |
| P8.5 | [ ] save with status=placeholder |

## Checks

- [ ] placeholder shape on trip artifact
- [ ] UI shows coming later without prices

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p8-booking-placeholder` tasks complete (when that change exists)
