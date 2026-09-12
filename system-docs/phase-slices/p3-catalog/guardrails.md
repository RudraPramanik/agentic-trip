# P3 Catalog acquire + retrieve — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Overpass/OTM down | Fail-soft empty/partial; honest readiness |
| Thin catalog | Do not scrape country centroid or foreign fill |
| ARQ/Redis down | Marked failed job; user-visible status |
| Empty retrieve | Honest empty + HITL (PostGIS *is* v1 retrieve; vector geo-fallback later) |

## SWE / LLD delta

- Retrieve uses PostGIS bbox + tags with GiST — not an unbounded table scan.
- Acquire ingest = chosen region/hubs only; never country-centroid radius scrape.
- Country filter on upsert and retrieve; unknown-country border POIs excluded.
- ARQ bounded retry then `failed`; never hang without status.
- Workers call `CatalogService` / ports; Overpass HTTP stays in adapters.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
