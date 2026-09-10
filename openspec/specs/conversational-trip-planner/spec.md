# conversational-trip-planner Specification

## Purpose

Defines the conversational trip OS from first prompt to a saved, map-backed itinerary and in-chat revision. This is a new-product contract captured in the parent vault; it is not a Wandr module feature and MUST NOT invent Wandr OpenAPI fields.

## Requirements

### Requirement: Chat is the only trip intake

The new product MUST accept a natural-language trip prompt (country, region, place, vibe, or mix) on a chat surface. The user MUST NOT be required to pick a destination from a place-search API before chatting. Guests MUST be able to start a chat without a login wall.

#### Scenario: Prompt without a prior place pick

- **WHEN** a visitor opens the product and types a trip request such as "10 days in Japan, food, slow"
- **THEN** the system begins planning from that message and does not block on a separate destination typeahead as a required first step

#### Scenario: Guest can start

- **WHEN** a visitor has no authenticated account
- **THEN** they can send a first trip prompt and receive a planning response or a clarification turn

### Requirement: Dialogue turns stay cheap; full plans are explicit

The system MUST distinguish short dialogue turns (intent, clarification, small talk, HITL choice) from expensive generate/replan turns that acquire catalogs and build day structure. A full itinerary generation MUST be abortable if the user leaves. The system MUST NOT run a full generate on every chat message.

#### Scenario: Clarification does not generate a trip

- **WHEN** the prompt is ambiguous (two cities with the same name, or missing duration)
- **THEN** the system asks in chat and does not persist a trip itinerary from that turn

#### Scenario: User abandons generate

- **WHEN** a full plan generation is in progress and the client disconnects or cancels
- **THEN** the server stops the generation work for that turn (no orphaned unbounded LLM spend)

### Requirement: HITL happens inside the conversation

When geography or prefs are ambiguous or oversized, the system MUST ask in chat (candidates, hub/region chips, or equivalent). The user’s answer MUST continue the same chat session. HITL MUST NOT require a separate search-first page as the only way to proceed.

#### Scenario: Ambiguous place name

- **WHEN** the user says "Paris" and more than one city-scale match is plausible
- **THEN** the system lists candidates in chat and waits; it does not silently pick one country

#### Scenario: Country needs a choice

- **WHEN** the user names a country and the day budget or hubs are not yet decided
- **THEN** the system MAY ask a short HITL question in chat, or proceed with an adaptive default per `adaptive-country-scope`, and MUST explain the chosen scope in the conversation

### Requirement: Saved trip is a structured artifact with a map

After a successful generate, the system MUST persist a trip the user can reopen. The artifact MUST include ordered days and stops grounded in real places (stable place identity and coordinates from geo/catalog tools, not free-form LLM invention). The map MUST show those stops; road polylines MUST appear when routing geometry exists, otherwise points only. The system MUST NOT invent coordinates to draw a prettier line.

#### Scenario: Itinerary is reopenable

- **WHEN** generate completes successfully
- **THEN** the user can open the trip later and see the same day list and mapped stops

#### Scenario: No hallucinated map geometry

- **WHEN** routing geometry is missing for a leg
- **THEN** the map still shows stop points and does not fabricate a polyline

### Requirement: Structure from planning engine; narrative from language model

Day structure, stop order, visit windows, and coordinates MUST come from deterministic planning/validation (a travel-engine-class layer), not from unconstrained model prose. Language models MAY write titles, day stories, and preference parsing. A finish/save MUST NOT succeed if validation of the structured itinerary failed, unless the run was explicitly aborted.

#### Scenario: Model prose cannot invent a stop

- **WHEN** the language model names a venue that is not in the retrieved catalog
- **THEN** that venue is not scheduled as a stop with invented coordinates

#### Scenario: Invalid structure is not saved as a success

- **WHEN** validation of day caps, travel, or catalog grounding fails and the run is not aborted
- **THEN** the system does not persist a successful trip artifact from that generate

### Requirement: Revision stays in chat after save

The user MUST be able to request changes in chat after a trip exists (drop a stop, change pace, swap a day). Revisions that change structure MUST go through the same grounded planning path (not silent rewrite of coordinates in prose). Unbounded revision loops MUST be capped.

#### Scenario: Pace change

- **WHEN** the user says "make day 2 less walking" on a saved trip
- **THEN** the system updates the structured itinerary and map from planning/validation, not by editing only the narrative text

### Requirement: Observability and evaluation are part of generate

Every generate and material replan MUST be traceable (fail-soft if the tracer is unconfigured) and MUST record an evaluation/quality record even on partial failure. Golden prompt cases (city, region, country, short vs long country stay) MUST exist as an eval harness before calling the planner production-quality.

#### Scenario: Failed generate still leaves a trace outcome

- **WHEN** a generate ends in error or clarification
- **THEN** observability still records an outcome and evaluation is not skipped solely because no trip was saved
