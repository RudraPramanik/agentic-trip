## 1. Local env for NVIDIA + Gemini

- [x] 1.1 infra: Ensure `.env` (not committed) has settings from `.env.demo` needed for end-to-end generate → guidebook → print/download: `DATABASE_URL`, CORS/frontend URLs as needed, `LLM_MODEL` / `LLM_API_KEY` / `LLM_API_BASE` for NVIDIA NIM primary, `LLM_MODEL_FALLBACKS` including Gemini, `GEMINI_API_KEY`, `EMBEDDING_MODEL`; never commit secrets or paste keys into docs
- [x] 1.2 infra: Proof — API and frontend boot with `.env`; Settings reads LLM trio; document which vars were needed (names only)

## 2. Shared GuidebookExport projection (P5b.1 prep)

- [x] 2.1 frontend: Add shared projection helpers that map `GuidebookExport` → print/PDF field sections (cover, hubs, days, stops, narratives) without inventing fields, venues, coords, or rates
- [x] 2.2 frontend: Proof — unit: fixture export maps to expected day/stop ids/names only

## 3. Print CSS / print view (P5b.1)

- [x] 3.1 frontend: Add print-friendly layout + `@media print` (hide chat chrome/map canvas noise; keep days/stops readable) consuming the shared projection
- [x] 3.2 frontend: Proof — fixture or component test: print view days/stops match export fixture

## 4. react-pdf document (P5b.2)

- [x] 4.1 frontend: Add `@react-pdf/renderer` dependency and `renderGuidebookPdf(export)` (or equivalent) Document components from the shared projection
- [x] 4.2 frontend: Proof — fixture DTO → PDF blob/text includes fixture days/stops and no extra venues

## 5. Print + Download actions (P5b.3)

- [x] 5.1 frontend: Wire guidebook **Print** (`window.print()` / print view) and **Download PDF** (client blob download) using owned `GET .../export` data already loaded or refetched
- [x] 5.2 frontend: Incomplete export or render failure → clear user-visible error; trip data unchanged; no invented fill
- [x] 5.3 frontend: Proof — manual or component: Print and Download succeed on fixture/live export; error path does not mutate trip

## 6. No LLM / no rates on PDF path (P5b.4)

- [x] 6.1 frontend: Ensure PDF/print modules do not import or call any LLM client; add test that fails if a fake LLM gateway is invoked during render
- [x] 6.2 frontend: Proof — assert printed/PDF content has no invented booking rates; hollow booking posture preserved
- [x] 6.3 backend: Proof — confirm no `GET /api/v1/trips/{id}/pdf` is required/shipped; export-only path unchanged (ASGI ownership still holds)

## 7. Playwright + terminal validation + CI

- [x] 7.1 infra: Add Playwright (or extend existing) smoke: open guidebook → Print control present → Download PDF produces a file/blob; print DOM shows fixture days when applicable
- [x] 7.2 backend: Local terminal smoke — Compose API up; `GET /api/v1/trips/{id}/export` days/stops still match saved structured trip; foreign cookie denied
- [x] 7.3 infra: Ensure CI or documented script runs fixture PDF/print tests + Playwright smoke; failures block merge
- [x] 7.4 docs: Align `system-docs/phase-slices/p5b-pdf-export/` validation checkboxes with proofs; if blueprint and `llm.md` §5 disagree on FE-only vs `GET .../pdf`, resolve both (no third shape); mark blueprint status implemented via this change
