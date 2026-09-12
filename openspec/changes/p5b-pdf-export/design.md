## Context

See proposal.md — Why. P5 (`p5-guidebook-map`) is complete: `GuidebookExport`, `GET /api/v1/trips/{id}` + `.../export`, FE guidebook + MapLibre points, hollow booking, media stub. Guests can reopen a draft but cannot print/download. Phase docs: `system-docs/phase-slices/p5b-pdf-export/`; LLD `system-docs/llm.md` §5 (optional `GET .../pdf` or FE print-only). Constraints: PDF/print = pure projection of `GuidebookExport`; no `LlmGateway` on that path; no invented rates/venues/coords; no Wandr paths.

## Goals / Non-Goals

**Goals:**

- Print CSS / print layout from export DTO (P5b.1).
- Client `@react-pdf/renderer` PDF from the same DTO (P5b.2 — included).
- Guidebook Print + Download PDF actions (P5b.3) using existing export only.
- Tests: no LLM on PDF path; fixture days/stops match; no booking rates (P5b.4).
- Local NVIDIA primary + Gemini fallback/embeddings; terminal + Playwright/browser validation.

**Non-Goals:**

- `GET /api/v1/trips/{id}/pdf` server bytes / ARQ `render_pdf` (later optional).
- Email delivery; revise (P6); Explore; booking HTTP; Wandr APIs.

## Decisions

### 1. FE-only print + react-pdf; defer server PDF

**Choice:** Product path is browser print stylesheet + `@react-pdf/renderer` download in the Next.js frontend. Do not add `GET .../pdf` in this slice. Export remains `GET .../export`.

**Why:** Matches architecture (print CSS first, react-pdf next; optional ARQ later). Keeps PDF off the API process (CPU/memory), makes “no LLM on PDF path” trivial to prove, and reuses the DTO P5 already froze for PDF.

**Alternatives:** Server PDF via WeasyPrint/Puppeteer (ops weight, ownership/auth duplication); FE print-only without download (weaker product proof); ship both FE and `GET .../pdf` now (scope creep).

### 2. Single shared projection helpers from GuidebookExport

**Choice:** One FE module (e.g. `lib/guidebook-export-view` or `features/trip-pdf`) that maps `GuidebookExport` → print DOM sections and → react-pdf `<Document>` trees. Guidebook on-screen view stays the interactive surface; print/PDF share field selection (cover, hubs, days, stops, narratives) without inventing fields.

**Why:** Avoid dual pipelines (UI vs PDF drift). Guardrail: structure from DTO only.

**Alternatives:** Screenshot the live guidebook DOM (fragile); separate hardcoded PDF layout that re-fetches trip and reshapes (drift risk).

### 3. Print CSS via dedicated print media / print route panel

**Choice:** Add a print-friendly layout (CSS `@media print` and/or a print panel) triggered from guidebook “Print” (`window.print()`). Hide chrome (chat shell, map canvas, booking CTA noise) in print media; keep days/stops readable.

**Why:** P5b.1 proof; works without new backend; Playwright can assert print DOM or trigger print dialog flow as far as automation allows.

**Alternatives:** Only react-pdf (skips blueprint P5b.1); server-rendered HTML print page (extra route).

### 4. Download = client blob from react-pdf; no email

**Choice:** `pdf()` / `toBlob()` from `@react-pdf/renderer`, then browser download (`URL.createObjectURL` + anchor). File name from trip cover title or `trip_id`. On failure, toast/inline error; trip state unchanged.

**Why:** Full working download without ARQ; scales with client device; server stays thin.

**Alternatives:** Open print dialog only; upload PDF to object storage (premature).

### 5. No LLM / no booking rates — enforced by architecture + tests

**Choice:** PDF/print modules MUST NOT import or call LLM clients. Unit/component tests render fixture export with a spy/fake that fails if LLM is invoked (FE: mock assert; BE: if any helper exists, spy `LlmGateway`). Assert document text/fixtures contain fixture stop names only and contain no synthetic rate patterns.

**Why:** P5b.4 + booking hollow law.

### 6. Local LLM env: NVIDIA primary, Gemini fallback/embeddings

**Choice:** At apply/validation, ensure `.env` (not committed) has NVIDIA NIM `LLM_*` primary and Gemini fallback/embeddings from `.env.demo`, same posture as P5 — so generate → guidebook → print E2E still works. Never paste secrets into OpenSpec artifacts.

**Why:** User-requested local stack for full workingness.

### 7. Validation: Playwright + terminal + CI

**Choice:**

- Terminal: fixture or live `GET .../export` asserts days/stops schema (reuse P5 smoke).
- Unit: fixture DTO → react-pdf extractable text / print DOM match; no rates; no LLM call.
- Playwright: open guidebook → Print control present → Download produces blob/download; optional print DOM visible.
- CI: pytest (if any BE asserts) + FE test script + Playwright job or documented script that blocks merge.

**Why:** User asked for browser/terminal FE testing with Playwright as needed; validation.md gate.

### 8. Reliability / scale posture

**Choice:** Client-side O(stops) projection; no LLM spend on download; export JSON remains the cacheable SSOT (server can cache later); defer server PDF to avoid API memory spikes under concurrent downloads; keep routers → services → ports unchanged.

**Alternatives:** Always-on ARQ PDF workers (ops cost before need).

## Risks / Trade-offs

- [react-pdf layout ≠ screen guidebook] → Mitigation: shared field mapper; fixture golden text for days/stops only (not pixel-perfect).
- [Playwright cannot fully assert system print dialog] → Mitigation: assert print DOM / `@media print` content and Download blob; manual print preview note allowed for dialog chrome.
- [Large itineraries slow client PDF] → Mitigation: v1 multi-day drafts are small; document soft limit; later ARQ if needed.
- [Incomplete export edge cases] → Mitigation: fail soft with clear error; no fill invention.
- [Scope creep to server PDF] → Mitigation: non-goal + api-foundation keeps `GET .../pdf` non-product.

## Migration Plan

1. Add FE print layout + react-pdf package and shared projection from `GuidebookExport`.
2. Wire Print / Download actions on guidebook; error states.
3. Add fixture unit tests + Playwright smoke; CI/docs scripts.
4. Configure local `.env` from `.env.demo` (NVIDIA + Gemini).
5. Run terminal export smoke + browser print/download proof; align `p5b-pdf-export/validation.md`.
6. Rollback: hide Print/Download actions; guidebook/export remain valid.

## Open Questions

None material. Exact print CSS polish and PDF typography left to apply-time FE craft within the shared DTO field set.
