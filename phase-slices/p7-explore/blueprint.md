# P7 Explore — blueprint

> Status: planning blueprint (implement via later OpenSpec `p7-explore`).

## Goal

Near me (GPS→IP) + Last trip location only after saved trip; real catalog places only.

## Scope / modules

modules/explore, frontend explore

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p7-explore` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Near me works or honest empty; last-trip locked pre-save

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
