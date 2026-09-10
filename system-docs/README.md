# Central context vault

Short, shared map for humans and AI agents working across **`guideagent`** (API) and **`guideagent-frontend`** (Next.js).

## Purpose

- Route cross-boundary bugs to **both** FE and BE investigation paths
- Point at **existing** module docs and code — never invent APIs
- Stay small; update when a real cross-bug is fixed

## Contents

| File | Use when |
|------|----------|
| [`system-map.md`](./system-map.md) | Need FE↔BE boundary overview (auth, SSE, trips, types) |
| [`symptoms.md`](./symptoms.md) | Have a user-visible symptom and need where to look first |
| [`cursor/`](./cursor/) | Canonical templates for user-scoped `/sq-*` Cursor commands |
| [`free-media-map-guidebook.md`](./free-media-map-guidebook.md) | Planning: free map/satellite, place photos, Layla guidebook UI; Google-ready facade |
| [`chat-first-trip-os.md`](./chat-first-trip-os.md) | **Sibling product bible** (conversational trip OS). Not Wandr. |

**This product (not Wandr):** [`chat-first-trip-os.md`](./chat-first-trip-os.md) is the living bible. OpenSpec root is `../openspec/` (specs: `conversational-trip-planner`, `adaptive-country-scope`, `explore-geo-feed`, `booking-placeholder`). Do **not** invent Wandr endpoints/DTOs/env vars from it.

**Active cross-boundary (trip route lines):** OpenSpec `cross-trip-route-polylines` → module changes `hybrid-routing-trip-polylines` (guideagent) + `trip-route-polyline-map` (guideagent-frontend). See Trips / GeoJSON in [`system-map.md`](./system-map.md).

**Planning (map + media + guidebook):** OpenSpec `free-media-map-guidebook` → future module changes `place-media-enrich` (guideagent), `map-basemap-toggle` + `guidebook-trip-ui` (guideagent-frontend). See [`free-media-map-guidebook.md`](./free-media-map-guidebook.md).

## Agent usage

1. Read parent [`AGENTS.md`](../../AGENTS.md).
2. For cross-boundary work, open [`symptoms.md`](./symptoms.md) before choosing a single-package fix.
3. Obey module rules when editing code (`guideagent/.cursorrules`, `guideagent-frontend/AGENTS.md`).
4. Verify paths still exist before editing — this table can drift.

## MCP layering

| Scope | Where | What |
|-------|--------|------|
| **User (always-on)** | `%USERPROFILE%\.cursor\mcp.json` | Sequential Thinking; Context7; Playwright (plugin or user) — available in FE, BE, or parent windows |
| **Project (parent)** | [`../../.cursor/mcp.json`](../../.cursor/mcp.json) | `tripplanner-context` filesystem allowlist for this vault + package `docs/` |

### Sequential slash commands (user-scoped)

Live under `%USERPROFILE%\.cursor\commands\` (templates in [`cursor/`](./cursor/)):

- `/sq-think` — general sequential planning
- `/sq-architect` — boundaries / ownership / FE↔BE shape
- `/sq-debug` — hypothesis elimination

Agents may also call Sequential Thinking MCP without a slash command when multi-step reasoning helps.

### Filesystem MCP (`tripplanner-context`)

Allowlisted roots only:

- `docs/context` (this vault)
- `guideagent/docs`
- `guideagent-frontend/docs`

**Enable:** Cursor Settings → MCP → ensure project servers are loaded (reload window if needed after editing `.cursor/mcp.json`). Server name: `tripplanner-context`.

**Fallback:** If the filesystem MCP server fails to start or is disabled, use built-in Read/Grep on the `tripplanner/` workspace. The same files are available without MCP.

MCP is **read-oriented context** (filesystem) or **reasoning aid** (Sequential Thinking), not a substitute for native workspace tools, and it does not change how the apps run. Do **not** put Sequential Thinking into FE/BE project `mcp.json` — keep it user-scoped.
