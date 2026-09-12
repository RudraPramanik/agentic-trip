# P9 Hardening — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P9.1 | [ ] golden CI gate |
| P9.2 | [ ] cost cap unit tests |
| P9.3 | [ ] abort harden test (incl. timeout flag); does not invent timeout or last-trip-from-draft |
| P9.4 | [ ] rate limit 429 |
| P9.5 | [ ] full bible golden union (P2.9 + P4.10) |

## Checks

- [ ] full bible golden union (city / region / country-short / Kyoto-wins / country-long / Paris / border / missing duration / abandoned generate / failed generate traced)
- [ ] rate limit / cost cap unit tests
- [ ] abort / timeout under load smoke

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p9-hardening` tasks complete (when that change exists)
