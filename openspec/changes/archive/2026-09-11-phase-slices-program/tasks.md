## 1. Docs index and layout sync

- [x] 1.1 docs: Ensure `phase-slices/README.md` catalogs all slices and delivery loop
- [x] 1.2 docs: Confirm `system-docs/architecture-draft.md` §3 uses root `/src` (not `/backend`) and L20–L23
- [x] 1.3 docs: Point `system-docs/README.md` at `phase-slices/` and settled architecture

## 2. Shared slice template content

- [x] 2.1 docs: Add `phase-slices/_template/` or document required files (blueprint, guardrails, validation, references)
- [x] 2.2 docs: Cross-link `fail-soft-boundaries` spec scenarios into a shared guardrails snippet for reuse

## 3. Author all phase-slice packages

- [x] 3.1 docs: Write `phase-slices/p0-foundation/{blueprint,guardrails,validation,references}.md`
- [x] 3.2 docs: Write `phase-slices/p1-chat/{blueprint,guardrails,validation,references}.md`
- [x] 3.3 docs: Write `phase-slices/p2-dialogue-scope/{blueprint,guardrails,validation,references}.md`
- [x] 3.4 docs: Write `phase-slices/p3-catalog/{blueprint,guardrails,validation,references}.md`
- [x] 3.5 docs: Write `phase-slices/p4-generate/{blueprint,guardrails,validation,references}.md`
- [x] 3.6 docs: Write `phase-slices/p5-guidebook-map/{blueprint,guardrails,validation,references}.md`
- [x] 3.7 docs: Write `phase-slices/p5b-pdf-export/{blueprint,guardrails,validation,references}.md`
- [x] 3.8 docs: Write `phase-slices/p6-revision/{blueprint,guardrails,validation,references}.md`
- [x] 3.9 docs: Write `phase-slices/p7-explore/{blueprint,guardrails,validation,references}.md`
- [x] 3.10 docs: Write `phase-slices/p8-booking-placeholder/{blueprint,guardrails,validation,references}.md`
- [x] 3.11 docs: Write `phase-slices/p9-hardening/{blueprint,guardrails,validation,references}.md`

## 4. Program validation (docs proof)

- [x] 4.1 docs: Verify every slice folder has all four files
- [x] 4.2 docs: Run `openspec validate phase-slices-program --strict` and fix issues
- [x] 4.3 docs: Note next OpenSpec code change is `p0-foundation` (do not scaffold `/src` in this change)

## 5. Handoff

- [x] 5.1 docs: Record in architecture-draft changelog that phase-slices program is ready to apply/archive
- [x] 5.2 docs: List follow-on change names for implementation (p0…p9) in `phase-slices/README.md` if missing
