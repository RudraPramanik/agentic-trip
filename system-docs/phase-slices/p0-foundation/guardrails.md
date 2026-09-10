# P0 Foundation — guardrails

Start from [`../SHARED-FAIL-SOFT.md`](../SHARED-FAIL-SOFT.md) and [`../SHARED-SWE-LLD.md`](../SHARED-SWE-LLD.md).

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Settings/env missing | Fail fast on boot with clear error; do not half-start |
| DB down | Health shows dependency unhealthy; API does not pretend ready |
| Langfuse unconfigured | No-op tracer; requests still work |
| LLM keys missing | Gateway returns structured unavailable; no crash on import |

## SWE / LLD delta

- `GET /health` is liveness; `GET /health/ready` is dependency probe — do not conflate.
- Ports in P0 are stubs/Protocols only; no vendor SDKs in `main.py` or routers.
- Feature modules must import without network I/O or required third-party keys.
- Settings fail-fast; do not default secrets to empty and continue as if configured.
- Naming: `*Port` / `*Gateway` in `ports/`; composition root wires stubs.

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
