# P5b PDF / print export — blueprint

> Status: planning blueprint (implement via later OpenSpec `p5b-pdf-export`).

## Goal

PDF or print from GuidebookExport DTO only; no LLM inventing PDF content.

## Scope / modules

frontend print/react-pdf; optional ARQ render later

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p5b-pdf-export` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Download/print matches saved structured trip

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
