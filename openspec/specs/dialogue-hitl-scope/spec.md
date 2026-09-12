# dialogue-hitl-scope Specification

## Purpose

Defines dialogue-phase trip intake: structured intent, geo candidate search, deterministic TripScope classification, in-chat HITL interrupt/resume, and golden proofs that one city/region/country scope is confirmed before catalog or generate work.

## Requirements

### Requirement: Structured intent is parsed before scope is persisted

Dialogue turns that plan a trip MUST extract a structured intent (at least duration and vibe/constraints when present) from user text on the dialogue budget. When duration is missing, the system MUST ask for clarification and MUST NOT persist a trip scope or itinerary from that turn. When language-model provider keys are missing, intent complete MUST fail soft via the structured unavailable path rather than crashing the process.

#### Scenario: Rich prompt fills duration and vibe

- **WHEN** the user sends a prompt such as "10 days Japan food slow"
- **THEN** the structured intent includes a duration of about 10 days and food/slow vibe or constraints without requiring a separate destination typeahead

#### Scenario: Missing duration asks and does not persist

- **WHEN** the user names a place but omits trip duration
- **THEN** the system asks for duration in chat and does not persist a trip_scope from that turn

#### Scenario: Missing LLM keys do not crash intent parse

- **WHEN** dialogue intent complete runs with no provider keys configured
- **THEN** the call returns a structured unavailable outcome (or honest dialogue error) and does not raise solely due to missing keys

### Requirement: Geo search returns candidates and never silently picks

Place resolution MUST go through a single geo gateway that returns ranked candidates only. Zero matches, timeouts, or multiple plausible matches MUST lead to HITL or an honest ask. The system MUST NOT silently pick a country centroid or invent coordinates to continue.

#### Scenario: Geocoder timeout yields empty candidates

- **WHEN** the geocoder times out or fails for a place query
- **THEN** the result is an empty candidate list (or equivalent fail-soft empty) and planning does not invent a country centroid

#### Scenario: Zero or many candidates require HITL or ask

- **WHEN** geocode search returns zero candidates or more than one plausible match
- **THEN** the system does not silently select one place and instead asks or presents candidates for a user choice

#### Scenario: Single clear candidate may proceed without HITL

- **WHEN** geocode search returns exactly one plausible city-scale (or otherwise unambiguous) candidate and duration is known
- **THEN** the system may classify scope without interrupting for place choice

### Requirement: Scope classification is deterministic and geo-first

The system MUST classify each resolved place into exactly one trip scope kind: city, region, or country. Classification MUST prefer deterministic geo metadata (admin level, bbox span, place class) before any language-model hub suggestion. A named city or region MUST win over a “best region” override. Country stays longer than the short-stay threshold MUST write hubs or HITL rather than country-without-hubs. Short country stays MUST collapse toward a best-region outcome (or flag that outcome for explain) per adaptive-country-scope behavior.

#### Scenario: Named city wins

- **WHEN** the user asks for a few days in a named city such as Kyoto
- **THEN** the trip_scope kind is city for that place and is not overridden by a different best region

#### Scenario: Region-scale place

- **WHEN** the user names a region-scale place (for example a Tuscany-style region) confirmed by geo metadata
- **THEN** the trip_scope kind is region for that place

#### Scenario: Short country stay prefers best region

- **WHEN** the user asks for about 3 days in a country without naming a city or region
- **THEN** the system does not leave a nationwide hop as the confirmed scope without a best-region (or equivalent) outcome explained in chat

#### Scenario: Long country stay writes hubs or HITL

- **WHEN** the user asks for about 10 days in a country such as Japan without naming cities
- **THEN** the confirmed outcome includes hubs for the day budget, or HITL between coherent hub alternatives — not country-without-hubs

### Requirement: Ambiguous geography interrupts with in-chat HITL

When geography (or material hub choice) is ambiguous, the dialogue flow MUST interrupt, persist a pending HITL projection on the session, and wait. HITL MUST continue in the same chat session. HITL MUST NOT be implemented as a background job queue item, and MUST NOT require a separate search-first page as the only path forward.

#### Scenario: Ambiguous Paris interrupts

- **WHEN** the user says "Paris" and more than one city-scale match is plausible
- **THEN** the session shows pending HITL with candidates and does not silently pick one country or city

#### Scenario: HITL is not a background job

- **WHEN** the dialogue flow needs a place or hub choice from the user
- **THEN** the wait is an interrupt/resume on the dialogue session path, not an ARQ (or equivalent) job

### Requirement: Confirmed choice writes exactly one trip_scope

After an unambiguous classify or a resumed HITL choice, the system MUST write exactly one `trip_scope` (kind city|region|country with grounded geo identity) on the session and explain the chosen scope in chat. Confirming scope MUST NOT start catalog acquire or generate.

#### Scenario: Resume choice sets trip_scope

- **WHEN** a session has pending HITL and the owning guest submits a valid choice
- **THEN** the session projection includes exactly one trip_scope.kind and HITL is no longer pending

#### Scenario: Confirm scope does not generate

- **WHEN** trip_scope is confirmed on a session
- **THEN** the system does not start generate work and does not persist an itinerary as a successful plan from that confirmation alone

### Requirement: In-chat chips resume HITL on the same session

The chat UI MUST present HITL candidates (or equivalent chips) when the session has pending HITL, and submitting a chip MUST POST the choice to the session HITL resume API and continue the same session.

#### Scenario: Pick chip continues same session

- **WHEN** the user picks a HITL candidate chip for a pending session
- **THEN** the client posts that choice for the same session id and the conversation continues without requiring a separate destination-search page as the only path

### Requirement: Scope goldens cover the bible cases

An offline eval/golden harness MUST assert the scope outcomes for at least: city (e.g. Kyoto ~4d); Tuscany-style region; country-short (e.g. Japan ~3d); named-city-wins (e.g. “3 days in Kyoto”); Japan-10-days-or-HITL; ambiguous Paris; missing duration (ask, no persist).

#### Scenario: Golden suite lists required cases

- **WHEN** the scope golden suite is run in CI or the documented eval script
- **THEN** each listed bible case has an assertion and failures block merging the slice
