# P5b PDF / print export — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P5b.1 | [ ] Print view from export DTO |
| P5b.2 | [ ] react-pdf fixture or explicitly skipped for print-only |
| P5b.3 | [ ] Download/print action works |
| P5b.4 | [ ] No LLM on PDF path test |

## Checks

- [ ] DTO → PDF/print fixture
- [ ] no booking rates invented assert

## CI

- [ ] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [ ] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p5b-pdf-export` tasks complete (when that change exists)
