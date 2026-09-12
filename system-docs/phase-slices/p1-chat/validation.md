# P1 Chat — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P1.1 | [x] Guest cookie issue/read unit test |
| P1.2 | [x] Session save/load |
| P1.3 | [x] ChatService unit test (stub LLM) |
| P1.4 | [x] `POST /api/v1/sessions` + cookie |
| P1.5 | [x] SSE message stream |
| P1.6 | [x] GET session; disconnect cancel |
| P1.7 | [x] Trace span or no-op |
| P1.8 | [x] FE shell streams (manual note OK) |
| P1.9 | [x] Guest round-trip; generate not invoked |

## Checks

- [x] ASGI test: guest message round-trip
- [x] trace id present or fail-soft
- [x] no generate invoked on chat-only turn

## CI

- [x] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p1-chat` tasks complete (when that change exists)
