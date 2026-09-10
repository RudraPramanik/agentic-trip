# P6 Revision — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Loop cap hit | Stop and explain; keep last valid |
| Validation fail on replan | Do not save invalid as success |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
