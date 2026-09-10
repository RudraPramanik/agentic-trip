# P7 Explore — blueprint

> Status: planning blueprint (implement via later OpenSpec `p7-explore`).  
> LLD: [`../../llm.md`](../../llm.md) §7.6

## Goal

Near me (GPS→IP) + Last trip location only after saved trip; real catalog places only.

## Scope / modules

modules/explore, frontend explore

## Step plan

Implement **one sub-phase at a time**.

### P7.1 — GPS→IP near_me

- **Goal:** Nearby catalog places with honest empty.
- **Modules:** `src/modules/explore/`
- **Types:** `ExploreService`, `NearMeQuery`
- **Functions:** `near_me(gps?, ip?)`
- **Services:** `ExploreService`
- **Routes / APIs:** none yet
- **Algorithms / data:** GPS if present else IP; retrieve catalog; never fake city
- **Depends on:** P3.5
- **Proof:** unit: GPS used first; IP fallback; both fail → empty
- **Non-goals:** last-trip fill from IP

### P7.2 — last_trip after saved trip

- **Goal:** Last-trip tab only after a **saved** trip.
- **Modules:** `ExploreService.last_trip`
- **Types:** `LastTripResult` (`locked` | places)
- **Functions:** `last_trip(principal)`
- **Services:** `ExploreService` + trips
- **Routes / APIs:** none yet
- **Algorithms / data:** no saved trip → locked; catalog around last saved location
- **Depends on:** P7.1, P4.7 (saved vs draft rules L18)
- **Proof:** unit: draft-only guest → locked; saved → catalog ids or empty
- **Non-goals:** inventing POIs

### P7.3 — Explore HTTP

- **Goal:** Dual-tab APIs.
- **Modules:** `src/api/explore.py`
- **Types:** place list DTO
- **Functions:** routers
- **Services:** `ExploreService`
- **Routes / APIs:** `GET /api/v1/explore/near-me`, `GET /api/v1/explore/last-trip`
- **Algorithms / data:** query `lat,lng` optional
- **Depends on:** P7.2
- **Proof:** ASGI both paths; last-trip locked pre-save
- **Non-goals:** Wandr explore paths

### P7.4 — FE dual-tab

- **Goal:** Near me + Last trip UI.
- **Modules:** `frontend/` explore
- **Types:** `ExploreTabs`
- **Functions:** fetch both endpoints
- **Services:** none
- **Routes / APIs:** consumes P7.3
- **Algorithms / data:** —
- **Depends on:** P7.3
- **Proof:** UI smoke: locked last-trip; near-me list or empty copy
- **Non-goals:** booking

### P7.5 — Proof tests

- **Goal:** No fake POI ids; last-trip lock.
- **Modules:** `tests/`
- **Types:** —
- **Functions:** pytest
- **Services:** —
- **Routes / APIs:** P7
- **Algorithms / data:** —
- **Depends on:** P7.3
- **Proof:** Near me works or honest empty; last-trip locked pre-save; ids ∈ catalog
- **Non-goals:** generate

## Proof

Near me works or honest empty; last-trip locked pre-save

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
