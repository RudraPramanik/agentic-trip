# P0 Foundation — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Settings/env missing | Fail fast on boot with clear error; do not half-start |
| DB down | Health shows dependency unhealthy; API does not pretend ready |
| Langfuse unconfigured | No-op tracer; requests still work |
| LLM keys missing | Gateway returns structured unavailable; no crash on import |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
