## 1. Shared LLD SSOT and SWE rules

- [x] 1.1 docs: Add `system-docs/phase-slices/SHARED-SWE-LLD.md` with SWE architecture, algorithm locks (design D5), system-design constraints, LLD patterns, naming/consistency, and anti-patterns (design D4/D6)
- [x] 1.2 docs: Write `system-docs/llm.md` with all required LLD sections (design D7): how to use, L-decision pointer, module map, class/Protocol catalog, HTTP catalog (design D3), data shapes, sequence diagrams, algorithms, SWE pointer, sub-phase index, non-goals — no Wandr paths
- [x] 1.3 docs: Keep `SHARED-FAIL-SOFT.md`; add a one-line pointer to `SHARED-SWE-LLD.md` so fail-soft and SWE/LLD are both discoverable

## 2. Template and indexes

- [x] 2.1 docs: Update `_template/blueprint.md` with the sub-phase section template (design D2) and a placeholder `### P{n}.1` example
- [x] 2.2 docs: Update `_template/guardrails.md` to include fail-soft table plus SWE/LLD rules section linking both shared files
- [x] 2.3 docs: Update `_template/validation.md` with a Sub-phase checks table (design D9)
- [x] 2.4 docs: Update `_template/references.md` to link `system-docs/llm.md`, architecture, bible, `SHARED-FAIL-SOFT.md`, `SHARED-SWE-LLD.md`
- [x] 2.5 docs: Update `system-docs/phase-slices/README.md` delivery loop: blueprint sub-phases → implement → validation; catalog `llm.md`
- [x] 2.6 docs: Add `llm.md` row to `system-docs/README.md`

## 3. P0 foundation slice

- [x] 3.1 docs: Expand `p0-foundation/blueprint.md` with P0.1–P0.12 per design D8 (template D2: modules, types, functions, services, routes, proofs)
- [x] 3.2 docs: Expand `p0-foundation/guardrails.md` with SWE/LLD delta (settings fail-fast, ports stubs, health vs ready)
- [x] 3.3 docs: Expand `p0-foundation/validation.md` with sub-phase checkboxes for P0.1–P0.12; keep phase CI/exit
- [x] 3.4 docs: Update `p0-foundation/references.md` to `llm.md` + `SHARED-SWE-LLD.md`

## 4. P1 chat slice

- [x] 4.1 docs: Expand `p1-chat/blueprint.md` with P1.1–P1.9 (session routes, `ChatService`, SSE, FE shell)
- [x] 4.2 docs: Expand `p1-chat/guardrails.md` with SWE/LLD delta (cookie auth, SSE abort, traces)
- [x] 4.3 docs: Expand `p1-chat/validation.md` with P1.1–P1.9 sub-phase checks
- [x] 4.4 docs: Update `p1-chat/references.md` LLD + SWE links

## 5. P2 dialogue-scope slice

- [x] 5.1 docs: Expand `p2-dialogue-scope/blueprint.md` with P2.1–P2.9 (parse, geo, classify, HITL API, goldens)
- [x] 5.2 docs: Expand `p2-dialogue-scope/guardrails.md` with SWE/LLD delta (no silent geocode pick; metadata-first scope)
- [x] 5.3 docs: Expand `p2-dialogue-scope/validation.md` with P2.1–P2.9 checks
- [x] 5.4 docs: Update `p2-dialogue-scope/references.md` LLD + SWE links

## 6. P3 catalog slice

- [x] 6.1 docs: Expand `p3-catalog/blueprint.md` with P3.1–P3.8 (PostGIS repo, acquire ARQ, retrieve, catalog HTTP)
- [x] 6.2 docs: Expand `p3-catalog/guardrails.md` with SWE/LLD delta (GiST retrieve, no centroid scrape, bounded ARQ)
- [x] 6.3 docs: Expand `p3-catalog/validation.md` with P3.1–P3.8 checks
- [x] 6.4 docs: Update `p3-catalog/references.md` LLD + SWE links

## 7. P4 generate slice

- [x] 7.1 docs: Expand `p4-generate/blueprint.md` with P4.1–P4.10 (GenerateRunner, greedy pack, validate, SSE, abort)
- [x] 7.2 docs: Expand `p4-generate/guardrails.md` with SWE/LLD delta (engine purity, haversine/OSRM, no LLM stop-order)
- [x] 7.3 docs: Expand `p4-generate/validation.md` with P4.1–P4.10 checks
- [x] 7.4 docs: Update `p4-generate/references.md` LLD + SWE links

## 8. P5 guidebook-map slice

- [x] 8.1 docs: Expand `p5-guidebook-map/blueprint.md` with P5.1–P5.6 (export DTO, trip routes, MapLibre, empty booking UI)
- [x] 8.2 docs: Expand `p5-guidebook-map/guardrails.md` with SWE/LLD delta (points-only without geom; media off hot path)
- [x] 8.3 docs: Expand `p5-guidebook-map/validation.md` with P5.1–P5.6 checks
- [x] 8.4 docs: Update `p5-guidebook-map/references.md` LLD + SWE links

## 9. P5b PDF slice

- [x] 9.1 docs: Expand `p5b-pdf-export/blueprint.md` with P5b.1–P5b.4 (print CSS / react-pdf from DTO only; optional PDF route)
- [x] 9.2 docs: Expand `p5b-pdf-export/guardrails.md` with SWE/LLD delta (no LLM on PDF path)
- [x] 9.3 docs: Expand `p5b-pdf-export/validation.md` with P5b.1–P5b.4 checks
- [x] 9.4 docs: Update `p5b-pdf-export/references.md` LLD + SWE links

## 10. P6 revision slice

- [x] 10.1 docs: Expand `p6-revision/blueprint.md` with P6.1–P6.5 (caps, revise graph, revise HTTP)
- [x] 10.2 docs: Expand `p6-revision/guardrails.md` with SWE/LLD delta (capped re-enter generate; structure not prose-only)
- [x] 10.3 docs: Expand `p6-revision/validation.md` with P6.1–P6.5 checks
- [x] 10.4 docs: Update `p6-revision/references.md` LLD + SWE links

## 11. P7 explore slice

- [x] 11.1 docs: Expand `p7-explore/blueprint.md` with P7.1–P7.5 (near-me GPS→IP, last-trip after save, explore HTTP)
- [x] 11.2 docs: Expand `p7-explore/guardrails.md` with SWE/LLD delta (honest empty; no fake city; last-trip lock)
- [x] 11.3 docs: Expand `p7-explore/validation.md` with P7.1–P7.5 checks
- [x] 11.4 docs: Update `p7-explore/references.md` LLD + SWE links

## 12. P8 booking-placeholder slice

- [x] 12.1 docs: Expand `p8-booking-placeholder/blueprint.md` with P8.1–P8.5 (placeholder field, hollow service, GET booking)
- [x] 12.2 docs: Expand `p8-booking-placeholder/guardrails.md` with SWE/LLD delta (no fake rates; no vendor SDKs)
- [x] 12.3 docs: Expand `p8-booking-placeholder/validation.md` with P8.1–P8.5 checks
- [x] 12.4 docs: Update `p8-booking-placeholder/references.md` LLD + SWE links

## 13. P9 hardening slice

- [x] 13.1 docs: Expand `p9-hardening/blueprint.md` with P9.1–P9.5 (eval CI, cost caps, abort harden, rate limit)
- [x] 13.2 docs: Expand `p9-hardening/guardrails.md` with SWE/LLD delta (obs no-op still; caps in tests)
- [x] 13.3 docs: Expand `p9-hardening/validation.md` with P9.1–P9.5 checks
- [x] 13.4 docs: Update `p9-hardening/references.md` LLD + SWE links

## 14. Architecture alignment

- [x] 14.1 docs: Update `system-docs/architecture-draft.md` §14–§15 for sub-phase-inside-slice loop, LLD pointer (`llm.md`), package table; changelog row
- [x] 14.2 docs: Confirm architecture HTTP mentions do not contradict design D3; do not invent Wandr paths

## 15. Docs proof

- [x] 15.1 docs: Verify every slice folder still has four files (no nested `p0.1/` dirs) and every blueprint contains its D8 sub-phase headings
- [x] 15.2 docs: Verify every `guardrails.md` has a SWE/LLD section and every `validation.md` has sub-phase checks
- [x] 15.3 docs: Run `openspec validate phase-slices-function-level-lld --strict` and fix issues
- [x] 15.4 docs: Note next **code** OpenSpec change remains `p0-foundation`, executed as P0.1 → P0.12 using `llm.md` (do not scaffold `/src` in this change)
