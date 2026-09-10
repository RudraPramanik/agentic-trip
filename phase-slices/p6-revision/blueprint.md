# P6 Revision — blueprint

> Status: planning blueprint (implement via later OpenSpec `p6-revision`).

## Goal

In-chat capped replan; structure+map update via engine, not prose-only rewrite.

## Scope / modules

revise_graph, planner, trips

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p6-revision` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Less walking day 2 updates structured itinerary within cap

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
