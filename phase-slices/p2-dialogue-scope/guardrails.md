# P2 Dialogue + TripScope + HITL — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Geocoder timeout/empty | HITL or ask; no silent country centroid |
| Ambiguous place | Candidates in chat; wait |
| Missing duration | Ask; do not persist trip |
| Checkpoint store down | Honest error; prefer Postgres checkpointer |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
