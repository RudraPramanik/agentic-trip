# P9 Hardening — blueprint

> Status: planning blueprint (implement via later OpenSpec `p9-hardening`).  
> LLD: [`../../llm.md`](../../llm.md) §9, evals

## Goal

Eval CI gate, cost caps, abort harden, rate limits; golden harness pass.

## Scope / modules

obs/evals, CI, generate abort, rate limit middleware

## Step plan

Implement **one sub-phase at a time**.

### P9.1 — Golden CI gate

- **Goal:** CI fails on golden regression.
- **Modules:** `src/modules/evals/`, CI workflow
- **Types:** harness
- **Functions:** `run_eval_suite` (CI or ARQ `run_eval_suite`)
- **Services:** evals
- **Routes / APIs:** none required
- **Algorithms / data:** —
- **Depends on:** P2.9, P4.10, P0.9
- **Proof:** CI job runs goldens; failing fixture fails the job
- **Non-goals:** new product HTTP

### P9.2 — Cost caps

- **Goal:** Stop further LLM calls when token/cost cap hit.
- **Modules:** `src/modules/llm/`, generate runner
- **Types:** `CostCapExceeded`
- **Functions:** check cap around `LlmGateway.complete`
- **Services:** llm + runner
- **Routes / APIs:** none
- **Algorithms / data:** per-run counters
- **Depends on:** P4.1
- **Proof:** unit: cap → no further complete()
- **Non-goals:** billing product

### P9.3 — Abort harden

- **Goal:** Abort works multi-instance (Redis flag if needed).
- **Modules:** `GenerateRunner`, redis flag
- **Types:** —
- **Functions:** `abort_requested` durable
- **Services:** runner
- **Routes / APIs:** existing abort route
- **Algorithms / data:** shared flag if >1 API worker
- **Depends on:** P4.8
- **Proof:** test: abort under concurrent start; no unbounded continuation
- **Non-goals:** new UX

### P9.4 — Rate limit middleware

- **Goal:** Bound chat/generate abuse.
- **Modules:** `src/core/rate_limit.py`, `main.py`
- **Types:** —
- **Functions:** middleware `rate_limit`
- **Services:** none
- **Routes / APIs:** applies to `/api/v1/*` (429)
- **Algorithms / data:** token bucket / Redis counter; fail-soft if Redis down = documented conservative limit or fail closed (pick in p9 design; do not hang)
- **Depends on:** P0.10
- **Proof:** unit: over limit → 429
- **Non-goals:** Wandr gateway

### P9.5 — Harness pass

- **Goal:** Full golden harness green in CI.
- **Modules:** `tests/evals/`, monitor deepen
- **Types:** —
- **Functions:** suite entry
- **Services:** evals + obs
- **Routes / APIs:** none
- **Algorithms / data:** —
- **Depends on:** P9.1–P9.4
- **Proof:** CI runs goldens; cost/abort limits enforced in tests; obs still no-op without keys
- **Non-goals:** Qdrant, OAuth, live booking

## Proof

CI runs goldens; cost/abort limits enforced in tests

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
