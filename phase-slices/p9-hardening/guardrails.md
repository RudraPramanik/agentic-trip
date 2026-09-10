# P9 Hardening — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Eval failure | CI fails; do not ship |
| Cost cap | Stop further LLM calls for run |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
