# P8 Booking placeholder — blueprint

> Status: planning blueprint (implement via later OpenSpec `p8-booking-placeholder`).

## Goal

Empty stays/flights/activities slot on trip; save itinerary without vendors.

## Scope / modules

modules/booking, trips booking field, FE placeholder

## Step plan (high level)

1. Read this blueprint + guardrails + validation before coding.
2. OpenSpec propose/apply `p8-booking-placeholder` when starting implementation.
3. Implement behind ports/services; no vendor SDKs in routers.
4. Meet proof below; do not start the next slice until validation passes.

## Proof

Trip saves with booking.status=placeholder; no fake rates

## Explicit non-goals

- Do not pull work from later slices.
- Do not invent Wandr APIs or DTOs.
