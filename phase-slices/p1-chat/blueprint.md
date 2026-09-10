# P1 Chat — blueprint

> Status: planning blueprint (implement via later OpenSpec `p1-chat`).

## Goal

Guest cookie session + streaming chat round-trip (dialogue budget only; no generate).

## Scope / modules

modules/chat, api chat routes, auth guest cookie, obs chat traces

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p1-chat` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Send message as guest; receive streamed reply; session persists cookie

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
