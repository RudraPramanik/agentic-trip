# P6 Revision — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Loop cap hit | Stop and explain; keep last valid |
| Validation fail on replan | Do not save invalid as success |

## SWE / LLD delta

- Replan re-enters `TravelEngine.pack` + `validate_itinerary`; not a prose-only rewrite.
- Cap checker is mandatory before another expensive generate.
- Same fail-soft as P4: no invented stops; abort cooperative.
- `revise_graph` calls services/ports only.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
