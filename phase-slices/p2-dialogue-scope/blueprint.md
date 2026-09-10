# P2 Dialogue + TripScope + HITL — blueprint

> Status: planning blueprint (implement via later OpenSpec `p2-dialogue-scope`).

## Goal

Dialogue graph: intent parse, geocode candidates, classify scope, LangGraph interrupt HITL, confirm TripScope.

## Scope / modules

modules/agents/dialogue, modules/geo, chat HITL projection

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p2-dialogue-scope` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Goldens: city/region/country/ambiguous Paris; Meghalaya intent→region-ish scope; Japan short→best region explained

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
