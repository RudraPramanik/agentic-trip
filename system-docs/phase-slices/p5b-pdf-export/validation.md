# P5b PDF / print export — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P5b.1 | [x] Print view from export DTO (`GuidebookPrintView` + `@media print`; vitest fixture) |
| P5b.2 | [x] react-pdf fixture (`renderGuidebookPdf` + vitest blob) |
| P5b.3 | [x] Download/print action works (guidebook actions + Playwright `/guidebook-fixture`) |
| P5b.4 | [x] No LLM on PDF path test (`guidebook-export-view.test.ts`) |

## Checks

- [x] DTO → PDF/print fixture
- [x] no booking rates invented assert

## CI

- [x] Job or documented script runs these checks (`frontend` job: `npm test` + `npm run test:e2e`; pytest `tests/test_trips_pdf.py`)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p5b-pdf-export` tasks complete (when that change exists)
