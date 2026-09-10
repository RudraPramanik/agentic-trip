# P8 Booking placeholder — blueprint

> Status: planning blueprint (implement via later OpenSpec `p8-booking-placeholder`).  
> LLD: [`../../llm.md`](../../llm.md) §5, §6

## Goal

Empty stays/flights/activities slot on trip; save itinerary without vendors.

## Scope / modules

modules/booking, trips booking field, FE placeholder

## Step plan

Implement **one sub-phase at a time**.

### P8.1 — Booking field on trip

- **Goal:** Persist `booking.status=placeholder` with empty arrays.
- **Modules:** `src/modules/trips/` model
- **Types:** `BookingSlot`
- **Functions:** default booking on persist
- **Services:** `TripService` field
- **Routes / APIs:** none
- **Algorithms / data:** `{ status: "placeholder", stays: [], flights: [], activities: [] }`
- **Depends on:** P4.7
- **Proof:** saved/draft trip JSON includes placeholder shape
- **Non-goals:** vendor rows

### P8.2 — Hollow BookingService

- **Goal:** Read-only placeholder service; no vendor HTTP.
- **Modules:** `src/modules/booking/`
- **Types:** `BookingService`
- **Functions:** `get_placeholder(trip_id)`
- **Services:** `BookingService`
- **Routes / APIs:** none yet
- **Algorithms / data:** —
- **Depends on:** P8.1
- **Proof:** unit: never calls httpx; returns empty lists
- **Non-goals:** GDS, affiliate, priced activities

### P8.3 — Booking GET

- **Goal:** HTTP placeholder payload.
- **Modules:** `src/api/booking.py`
- **Types:** booking response DTO
- **Functions:** `get_booking`
- **Services:** `BookingService`
- **Routes / APIs:** `GET /api/v1/trips/{id}/booking`
- **Algorithms / data:** —
- **Depends on:** P8.2
- **Proof:** ASGI 200 placeholder; no rates
- **Non-goals:** Wandr booking OpenAPI

### P8.4 — FE placeholder

- **Goal:** Guidebook booking block wired to API or static empty.
- **Modules:** `frontend/` `BookingPlaceholder`
- **Types:** component
- **Functions:** fetch booking GET
- **Services:** none
- **Routes / APIs:** consumes P8.3
- **Algorithms / data:** —
- **Depends on:** P5.5, P8.3
- **Proof:** UI coming-later without prices
- **Non-goals:** checkout

### P8.5 — Save without rates

- **Goal:** Trip save succeeds with placeholder only.
- **Modules:** tests + `TripService`
- **Types:** —
- **Functions:** persist with booking field
- **Services:** trips
- **Routes / APIs:** existing trip persist
- **Algorithms / data:** —
- **Depends on:** P8.1
- **Proof:** Trip saves with `booking.status=placeholder`; no fake rates
- **Non-goals:** live vendors

## Proof

Trip saves with booking.status=placeholder; no fake rates

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
