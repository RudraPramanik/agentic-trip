# P1 Chat — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| LLM dialogue down | Honest error message in stream; session intact |
| Client disconnect | Stop work for that turn |
| Invalid session | Issue new guest session; do not leak another user |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
