# P3 Catalog acquire + retrieve — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Overpass/OTM down | Fail-soft empty/partial; honest readiness |
| Thin catalog | Do not scrape country centroid or foreign fill |
| ARQ/Redis down | Marked failed job; user-visible status |
| Empty retrieve | Geo fallback then HITL |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
