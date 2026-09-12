# P4 Generate + engine + validate — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P4.1 | [x] Runner progress + abort **or timeout** stops stages |
| P4.2 | [x] pack_days catalog-only |
| P4.3 | [x] matrix no fake geometry |
| P4.4 | [x] validate_itinerary unit gates |
| P4.5 | [x] graph fakes persist rules |
| P4.6 | [x] narrative cannot add place ids |
| P4.7 | [x] no success persist on fail; success is `status=draft` only |
| P4.8 | [x] abort route + cancel; timeout shares abort path; no success persist |
| P4.9 | [x] generate SSE ASGI |
| P4.10 | [x] Goldens: Meghalaya/Japan-shaped; Japan-10-days-or-HITL; border/country filter; abandoned generate; failed generate still traced |
| P4.11 | [x] FE Build plan CTA after scope; not on every chat turn |

## Checks

- [x] no invented place ids golden
- [x] validation gate unit tests
- [x] SSE abort + timeout tests
- [x] GenerateRunner port smoke

## CI

- [x] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p4-generate` tasks complete (when that change exists)

## Local validation

- Terminal: `uv run python scripts/smoke_generate.py` (ASGI fakes) or `uv run pytest tests/test_generate_api.py tests/evals/test_generate_goldens.py`
- Browser: see `frontend/GENERATE_CTA.md`
