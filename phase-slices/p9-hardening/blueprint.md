# P9 Hardening — blueprint

> Status: planning blueprint (implement via later OpenSpec `p9-hardening`).

## Goal

Eval CI gate, cost caps, abort harden, rate limits; golden harness pass.

## Scope / modules

obs/evals, CI, generate abort, rate limit middleware

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p9-hardening` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

CI runs goldens; cost/abort limits enforced in tests

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
