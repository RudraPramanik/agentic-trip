# P7 Explore — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| GPS+IP fail | Honest empty + retry; never fake city |
| No saved trip | Last-trip tab empty/locked |
| Thin nearby catalog | Honest empty; no invented POIs |

## SWE / LLD delta

- `near_me`: GPS then IP; never fabricate a city.
- IP must not populate last-trip.
- Last-trip requires a **saved** trip (auth when save exists).
- Places must be catalog ids from `retrieve_places` — Explore is not a LangGraph.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
