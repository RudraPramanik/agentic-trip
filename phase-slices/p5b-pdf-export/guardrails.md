# P5b PDF / print export — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Export DTO incomplete | Fail with clear error; do not invent hotels/prices |
| Render failure | User-visible error; trip data intact |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
