# Shared fail-soft guardrails (snippet)

> Normative spec: [`openspec/specs/fail-soft-boundaries/spec.md`](../../openspec/specs/fail-soft-boundaries/spec.md)  
> Product table: [`product-goal.md`](../product-goal.md) — Failure boundaries.  
> SWE / LLD regulations: [`SHARED-SWE-LLD.md`](./SHARED-SWE-LLD.md)

Copy relevant rows into each slice `guardrails.md`. Do not invent coords, venues, or polylines to look nicer.

| Kind | On failure | Never |
|------|------------|--------|
| Geocoder / gazetteer | Dialogue HITL or honest ask | Silent country centroid |
| Catalog acquire | Honest readiness / partial | Foreign-country refill; unbounded hang |
| Retrieve | Honest empty + HITL. **Geo fallback** = PostGIS bbox retrieve when a later vector index is empty/down. P3 retrieve *is* PostGIS (no second scrape). | Invent POIs |
| LLM | Defaults / wrap-up where safe | Invent coords or stop order |
| Routing | Points only; fail-soft times | Fake polylines |
| GPS | Fall back to IP for Near me | Fake a city |
| IP | Honest empty Near me + retry | Fill last-trip from IP |
| Worker / ARQ | Bounded retry → marked failed | Infinite wait without status |
| Monitor (tracing) | No-op if unconfigured/down | Crash the request |
| Generate timeout | Same as abort: stop spend; no success persist; honest aborted/timeout outcome | Continue generate; persist as success |
| Evals runner | Record fail-soft / skip in CI config | Block product path mid-request |

## Spec scenarios to cover in tests (when the slice touches that kind)

1. Geocoder empty or ambiguous → HITL / ask  
2. Retrieve empty → honest empty + HITL (PostGIS is the v1 retrieve; vector geo-fallback is later)  
2b. Generate wall-clock timeout → abort path; no success persist
3. Routing geometry missing → points only  
4. Tracer unconfigured → request still succeeds  
5. Background job fails → failed/honest status  
6. Model names unknown venue → not scheduled  

Slice authors: link this file from `references.md` and keep slice-specific rows in `guardrails.md`.
