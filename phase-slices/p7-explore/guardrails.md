# P7 Explore — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| GPS+IP fail | Honest empty + retry; never fake city |
| No saved trip | Last-trip tab empty/locked |
| Thin nearby catalog | Honest empty; no invented POIs |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
