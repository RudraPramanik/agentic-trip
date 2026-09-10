# P8 Booking placeholder — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Any vendor call attempted | Must not in this slice — non-goal |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
