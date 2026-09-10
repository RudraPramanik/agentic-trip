## 1. Product bible and architecture

- [ ] 1.1 [docs] Add a v1 footnote to `system-docs/product-goal.md` Auth/save: guest draft is reopenable in-cookie; `saved` requires OAuth later; last-trip stays locked through P0–P9
- [ ] 1.2 [docs] Update the product-goal roadmap P4/P5/P7 proof lines so they mention explicit generate CTA, wall-clock timeout, points-only map, and last-trip locked on draft
- [ ] 1.3 [docs] Footnote L18 and §4.6 in `system-docs/architecture-draft.md` with the same draft vs saved rule; do not add a save API

## 2. Shared LLD and fail-soft

- [ ] 2.1 [docs] Update `system-docs/llm.md`: draft vs saved on trip persist; generate sequence includes timeout → abort path; P4.11 CTA uses existing generate POST; P2.1 owns `LiteLlmAdapter`; v1 map is points-only
- [ ] 2.2 [docs] Add generate-timeout row to `system-docs/phase-slices/SHARED-FAIL-SOFT.md` and clarify retrieve “geo fallback” = PostGIS when a later vector index is empty
- [ ] 2.3 [docs] Mention generate timeout on the existing abort line in `system-docs/phase-slices/SHARED-SWE-LLD.md`

## 3. P2 dialogue owners

- [ ] 3.1 [docs] Extend P2.1 so live `LiteLlmAdapter` is in scope when keys exist (stub remains when missing)
- [ ] 3.2 [docs] Extend P2.4 / P2.9 / P2 validation: country-long writes `hubs[]` or HITL; goldens list city, region (Tuscany-style), country-short, Kyoto-wins, Japan-10-days-or-HITL, Paris, missing duration

## 4. P4 generate owners

- [ ] 4.1 [docs] Fold wall-clock timeout into P4.1 / P4.8 proofs (same abort path; no success persist)
- [ ] 4.2 [docs] Clarify P4.7 persist is `draft` only; not a saved trip
- [ ] 4.3 [docs] Add P4.11 FE generate CTA (Build plan after scope; existing generate POST); keep P1.8 without a generate button
- [ ] 4.4 [docs] Extend P4.10 / P4 validation: Japan-10-days-or-HITL, border/country filter, abandoned generate, failed generate still traced

## 5. P5 / P7 / P9

- [ ] 5.1 [docs] Note on P5.4: v1 maps are points-only unless a later slice stores route geometry; no crow-flies
- [ ] 5.2 [docs] Extend P7.2 / P7.4 / P7.5 / P7 validation: draft does not unlock last-trip; tab anchors persist; plan-from-card uses real place identity; IP approximate copy
- [ ] 5.3 [docs] Note on P9.3 / P9.5: harden abort/timeout and run the full bible golden union; do not introduce timeout or last-trip-from-draft as new product behavior

## 6. Catalog and proof

- [ ] 6.1 [docs] Touch `system-docs/phase-slices/README.md` P4/P7 proof summaries so they match the new owners (P4.11 listed)
- [ ] 6.2 [docs] Proof: each law in the `phase-slice-lld` delta has a named sub-phase and a validation checkbox; `llm.md` names the same owners; no new `p10-*` folder
