# P4 Generate + engine + validate — guardrails

## Fail-soft / error boundaries

| Kind | Fallback |
|------|----------|
| Validation fail | Do not persist successful trip |
| LLM narrative fail | Structure may still save if valid; or honest fail — never invent stops |
| Abort | No unbounded continuation |
| Model invents venue | Not scheduled |

## Abstraction rules

- Routers → services → ports/adapters only.
- Agents call services/ports; no raw vendor HTTP in graphs.
- Prefer honest user-visible outcomes over decorative fake data.

## Non-goals

See blueprint. Especially: no hallucinated coords/POIs/polylines.
