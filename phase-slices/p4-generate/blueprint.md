# P4 Generate + engine + validate — blueprint

> Status: planning blueprint (implement via later OpenSpec `p4-generate`).

## Goal

GenerateRunner in-process SSE; retrieve → greedy packer → validate → narrative → session draft persist; abort on disconnect.

## Scope / modules

modules/agents/generate, planner, trips draft, GenerateRunner

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p4-generate` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Meghalaya/Japan-shaped generate produces structured days with catalog-only stops; abort stops work

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
