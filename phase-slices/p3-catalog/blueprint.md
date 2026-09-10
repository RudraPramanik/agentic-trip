# P3 Catalog acquire + retrieve — blueprint

> Status: planning blueprint (implement via later OpenSpec `p3-catalog`).

## Goal

Acquire POIs by region/hubs (ARQ); store PostGIS; retrieve by bbox/category/tags; retrieve spans in obs.

## Scope / modules

modules/catalog, workers acquire, geo places adapters (Overpass/OTM)

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p3-catalog` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Acquire for a hub/region returns readiness; retrieve returns real place ids or honest empty

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
