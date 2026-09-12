## Why

P5 shipped a reopenable guidebook + MapLibre points map + stable `GuidebookExport` JSON, but guests still cannot print or download that artifact. Without P5b the “PDF/print from export DTO only” product law stays unproven and revise (P6) has no shareable offline surface. P5 OpenSpec change `p5-guidebook-map` is complete (23/23); P5b is the next product proof.

Work type: **cross-cutting** (frontend print CSS + react-pdf download from export DTO; guidebook download/print actions; tests asserting no LLM on the PDF path; Playwright/browser + terminal validation). Not docs-only.

## What Changes

- Ship a **print view** that renders the same `GuidebookExport` JSON used by the guidebook UI (browser print stylesheet / print layout).
- Ship **`@react-pdf/renderer`** client PDF generation from that DTO so download works without a second narrative pipeline (P5b.2 included — not skipped).
- Add guidebook **Print** and **Download PDF** actions that consume `GET /api/v1/trips/{id}/export` only.
- Keep PDF/print a **pure projection** of `GuidebookExport`: no `LlmGateway`, no invented hotels/prices/venues/coords, no booking rates in the document.
- Choose **FE-only** print/download for this slice (architecture: browser print CSS first + react-pdf; optional `GET /api/v1/trips/{id}/pdf` / ARQ deferred).
- Local validation: fixture DTO → print/PDF content match; Playwright (or documented browser) smoke for print/download; terminal smoke that export DTO still matches saved days/stops; configure local `.env` from `.env.demo` for **NVIDIA NIM primary + Gemini fallback/embeddings** (keys stay out of git/docs).
- Follow `system-docs/phase-slices/p5b-pdf-export/` (P5b.1–P5b.4, guardrails, validation), `system-docs/llm.md` §5, `SHARED-SWE-LLD.md`, and `SHARED-FAIL-SOFT.md`.

**Non-goals:** Server `GET .../pdf` / ARQ `render_pdf` job; email delivery; regenerating narrative for PDF; inventing Wandr paths/DTOs; revise (P6); Explore (P7); booking vendor API (P8); fake booking rates in the document; second LLM pipeline for PDF copy.

**BREAKING:** none. Additive FE surfaces on top of existing trip export. **Spec-level:** PDF/print becomes a product FE capability from `GuidebookExport`; optional server PDF route remains non-product until a later slice chooses it.

## Capabilities

### New Capabilities

- `trip-pdf-export`: Print CSS + react-pdf projection of `GuidebookExport`; guidebook Print/Download actions; no-LLM and no-invented-rates proofs; local Playwright/terminal validation.

### Modified Capabilities

- `api-foundation`: Clarify that after this slice, product PDF/print is FE print + client PDF from export JSON; optional `GET /api/v1/trips/{id}/pdf` stays non-product until explicitly shipped; explore/booking/trip-save remain gated.
- `fail-soft-boundaries`: Add P5b fallbacks — incomplete export → clear error (no invented content); render/print failure → user-visible error with trip data intact; PDF path MUST NOT call LLM or invent booking rates.
- `conversational-trip-planner`: Reopenable draft trip MUST be printable/downloadable as a guidebook projection of the same structured artifact (no LLM rewrite for export document).
- `booking-placeholder`: PDF/print MUST keep the hollow booking posture — no rates or availability claims in the exported document.

## Impact

- **Frontend:** print stylesheet / print layout from export; `@react-pdf/renderer` document components; Print + Download handlers on guidebook; fixture-driven unit/component tests; Playwright smoke for print/download UI.
- **Backend:** reuse existing `GET .../export` only; no new PDF route in this slice; optional spy/tests that trip PDF helpers (if any) never touch `LlmGateway`.
- **Tests / CI:** fixture DTO → print/PDF content (days/stops match, no extra venues); no-LLM-on-PDF-path test; no-booking-rates-in-document assert; Playwright or documented browser script; CI job or documented script blocks merge.
- **Env / local run:** Apply copies non-secret config + LLM settings from `.env.demo` into `.env` for NVIDIA (`LLM_*` / NIM) + Gemini (`GEMINI_API_KEY`, embedding model) so generate → guidebook → print/download stays end-to-end — never commit secrets.
- **Reliability / scale (v1 posture):** PDF/print is O(stops) client projection of cached export JSON; no LLM spend on download; export remains CPU-cheap and cacheable later; FE-only avoids server PDF CPU/memory spikes; optional later ARQ/server PDF can reuse the same DTO without dual pipelines; routers → services → ports unchanged.
- **Docs:** implement against `system-docs/phase-slices/p5b-pdf-export/`; if blueprint and `llm.md` §5 disagree on FE-only vs `GET .../pdf`, resolve both in this change (no third shape).
