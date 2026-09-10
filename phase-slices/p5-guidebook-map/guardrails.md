# P5 Guidebook UI + map + export DTO — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| No routing geometry | Points only |
| Map style fail | List-first fallback |
| Missing media | Category/gradient honest fallback — not fake venue photo claim |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
