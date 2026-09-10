# P5 Guidebook UI + map + export DTO — blueprint

> Status: planning blueprint (implement via later OpenSpec `p5-guidebook-map`).

## Goal

Frontend trip guidebook + MapLibre map; backend GuidebookExport DTO; booking placeholder empty block in UI.

## Scope / modules

frontend features/trip|map; modules/trips export; media optional later

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p5-guidebook-map` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Reopen trip shows days + mapped stops; export DTO matches UI fields for future PDF

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
