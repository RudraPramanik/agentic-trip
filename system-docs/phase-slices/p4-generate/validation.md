# P4 Generate + engine + validate — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P4.1 | [ ] Runner progress + abort **or timeout** stops stages |
| P4.2 | [ ] pack_days catalog-only |
| P4.3 | [ ] matrix no fake geometry |
| P4.4 | [ ] validate_itinerary unit gates |
| P4.5 | [ ] graph fakes persist rules |
| P4.6 | [ ] narrative cannot add place ids |
| P4.7 | [ ] no success persist on fail; success is `status=draft` only |
| P4.8 | [ ] abort route + cancel; timeout shares abort path; no success persist |
| P4.9 | [ ] generate SSE ASGI |
| P4.10 | [ ] Goldens: Meghalaya/Japan-shaped; Japan-10-days-or-HITL; border/country filter; abandoned generate; failed generate still traced |
| P4.11 | [ ] FE Build plan CTA after scope; not on every chat turn |

## Checks

- [ ] no invented place ids golden
- [ ] validation gate unit tests
- [ ] SSE abort + timeout tests
- [ ] GenerateRunner port smoke

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p4-generate` tasks complete (when that change exists)
