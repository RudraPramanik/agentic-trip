## Purpose

Defines the reopenable trip guidebook surface: stable GuidebookExport JSON shared by UI and future PDF, trip get/export HTTP, MapLibre stop points (no invented polylines), hollow booking UI, and an off–hot-path media stub.

## ADDED Requirements

### Requirement: GuidebookExport is a pure mapping from structured trip

The system MUST expose a stable GuidebookExport JSON view-model that includes cover, hubs, days, stops, narratives, and map points sufficient for guidebook UI and later PDF. Export MUST map from the structured trip artifact only. Export MUST NOT call a language model to rewrite day structure, stop order, place identities, or coordinates.

#### Scenario: Export covers UI fields from draft

- **WHEN** an owning guest requests export for a trip with a validated draft itinerary
- **THEN** the response includes cover, ordered days/stops, narratives when present, and map points derived from those stops

#### Scenario: Export does not invent structure

- **WHEN** export runs on a structured trip
- **THEN** place ids, day order, and coordinates in the export match the trip artifact and are not LLM-rewritten

### Requirement: Guests can get and export their trip

The HTTP API MUST expose `GET /api/v1/trips/{id}` and `GET /api/v1/trips/{id}/export` for the owning guest. Get MUST return the trip artifact (days, stops, narratives, map payload). Export MUST return GuidebookExport JSON. Foreign or unknown trip ids MUST deny without leakage. The API MUST NOT use Wandr paths.

#### Scenario: Owner gets trip

- **WHEN** the owning guest calls `GET /api/v1/trips/{id}` for a draft trip created by their session
- **THEN** the API returns the trip artifact including ordered days and stops

#### Scenario: Owner exports guidebook JSON

- **WHEN** the owning guest calls `GET /api/v1/trips/{id}/export`
- **THEN** the API returns GuidebookExport JSON matching the trip’s structured content

#### Scenario: Foreign trip is denied

- **WHEN** a guest requests get or export for a trip owned by a different principal
- **THEN** the API denies the read and does not leak trip contents

### Requirement: Successful generate assigns a reopenable trip id

After a successful generate draft persist, the owning guest MUST be able to obtain a stable trip id (via session projection and/or generate done payload) that works with trip get/export. Draft status MUST remain draft until a later saved-trip slice. Explore last-trip MUST stay locked for guest drafts.

#### Scenario: Trip id after generate

- **WHEN** generate completes successfully for a session the guest owns
- **THEN** the guest can resolve a trip id and load get/export for that draft

### Requirement: Guidebook UI renders days and narratives

The frontend MUST render a guidebook view from trip get and/or export that shows cover, hub sequence when present, per-day sections, stop/POI lists, and narratives when present. Reopening after generate MUST show the same day list the draft contains.

#### Scenario: Reopen shows days

- **WHEN** a guest opens the guidebook for a trip after successful generate
- **THEN** the UI shows the trip’s days and stops without requiring login

### Requirement: Map shows stop points without inventing polylines

The trip map MUST plot stop coordinates as points. The map MUST draw a road polyline only when routing geometry already exists on the trip payload. v1 MUST be points-only unless a later slice stores route geometry. The client MUST NOT invent crow-flies lines as roads. If the map style fails to load, the UI MUST fall back to list-first guidebook content.

#### Scenario: Points without geometry

- **WHEN** the trip has stop coordinates but no routing geometry
- **THEN** the map shows points only and does not draw a fabricated polyline

#### Scenario: Map style failure is list-first

- **WHEN** the map basemap/style fails to load
- **THEN** the guidebook list/day content remains usable without claiming a rendered map

### Requirement: Hollow booking block in guidebook UI

The guidebook UI MUST show an empty stays/flights/activities booking placeholder (or “coming later” equivalent) with no rates, availability, or reservation claims. The UI MUST NOT require a booking vendor SDK. Booking product HTTP remains out of scope for this capability.

#### Scenario: Empty booking without prices

- **WHEN** a guest views the guidebook for a draft trip
- **THEN** the booking area is empty or explicitly unavailable and shows no fake prices

### Requirement: Media stub stays off the generate hot path

The system MUST provide a media provider stub that returns empty or fail-soft results for place media. Generate and draft persist MUST NOT call media resolution. Missing media MUST use an honest category/gradient (or equivalent) fallback and MUST NOT claim a real venue photograph.

#### Scenario: Generate does not call media

- **WHEN** generate runs retrieve → pack → validate → narrative → persist
- **THEN** the generate path does not invoke place media resolution

#### Scenario: Stub returns empty honestly

- **WHEN** a client or service asks the media stub for place media
- **THEN** the result is empty or fail-soft and does not invent photo URLs presented as venue photos
