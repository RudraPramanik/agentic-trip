# P2 Dialogue + TripScope + HITL — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Geocoder timeout/empty | HITL or ask; no silent country centroid |
| Ambiguous place | Candidates in chat; wait |
| Missing duration | Ask; do not persist trip |
| Checkpoint store down | Honest error; prefer Postgres checkpointer |

## SWE / LLD delta

- `geocode_search` never silently picks a country centroid.
- `classify_scope` is code + geo metadata first; LLM hubs only if country metadata is thin.
- Named city or region always wins over “best region” override.
- HITL = LangGraph interrupt + session projection; not an ARQ job.
- Graphs call `GeoGateway` / `LlmGateway` via ports — no Nominatim in the graph module.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
