# P0 Foundation — validation gate

A slice is **done** only when every sub-phase proof below and the phase-level checks pass. Then proceed to the next phase-slice.

## Sub-phase checks

| ID | Proof |
|----|--------|
| P0.1 | [x] Package + Compose `api`/`db` exist |
| P0.2 | [x] Settings fail-fast test; logging importable |
| P0.3 | [x] Alembic baseline + session factory importable |
| P0.4 | [x] Ports import; abstract/stub methods |
| P0.5 | [x] All feature modules import with no I/O |
| P0.6 | [x] Guest issue/read unit test |
| P0.7 | [x] LlmGateway stub returns unavailable without keys |
| P0.8 | [x] Obs no-op without keys |
| P0.9 | [x] Evals smoke runner importable |
| P0.10 | [x] `GET /health` and `GET /health/ready` ASGI tests |
| P0.11 | [x] `workers/` importable; API boots without Redis |
| P0.12 | [x] pytest + CI (or documented script) green |

## Checks

- [x] pytest health/smoke
- [x] import all modules without side effects
- [x] obs fail-soft unit test

## CI

- [x] Job or documented script runs these checks (introduce CI provider in p0 if missing)
- [x] Failures block merging/applying the next slice

## Exit criteria

- All sub-phase proofs satisfied
- Phase-level proof in blueprint satisfied
- Fail-soft cases in guardrails covered by at least one test or explicit manual note
- OpenSpec `p0-foundation` tasks complete (when that change exists)
