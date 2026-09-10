# <Slice> — validation

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P{n}.1 | [ ] |

## Checks

- [ ]

## CI

- [ ] Job or script runs checks
- [ ] Failures block the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof satisfied
- Fail-soft covered by test or explicit note
