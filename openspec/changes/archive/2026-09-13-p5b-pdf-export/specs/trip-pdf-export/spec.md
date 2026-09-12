## Purpose

Defines printable and downloadable trip guidebook export as a pure client projection of GuidebookExport JSON—no LLM rewrite, no invented venues, prices, or coordinates.

## ADDED Requirements

### Requirement: Print view projects GuidebookExport only

The frontend MUST provide a print-oriented view of a trip that consumes the same GuidebookExport JSON used by the on-screen guidebook. Print content MUST include the trip’s days and stops from that export. Print MUST NOT call a language model to invent or rewrite day structure, stop identities, coordinates, hotels, or prices.

#### Scenario: Print preview matches export days

- **WHEN** an owning guest opens print preview for a trip with a valid GuidebookExport
- **THEN** the print view shows the same ordered days and stops as the export JSON

#### Scenario: Print does not invent venues

- **WHEN** print renders from GuidebookExport
- **THEN** no venue, hotel, or price appears that is absent from the export DTO

### Requirement: Downloadable PDF projects GuidebookExport only

The frontend MUST allow the owning guest to download a PDF guidebook generated from GuidebookExport. The PDF MUST reflect the export’s days and stops. PDF generation MUST NOT call a language model and MUST NOT invent venues, coordinates, hotels, or booking rates.

#### Scenario: Fixture export yields matching PDF content

- **WHEN** a fixture GuidebookExport with known days and stops is rendered to PDF
- **THEN** the PDF content includes those days and stops and does not add extra venues

#### Scenario: PDF path does not use the language model

- **WHEN** PDF or print rendering runs for a trip export
- **THEN** the language-model gateway is not invoked for that render

### Requirement: Guests can print or download from the guidebook

The guidebook UI MUST expose Print and Download PDF actions for a trip the guest owns. Those actions MUST use the existing trip export JSON (via `GET /api/v1/trips/{id}/export` or an equivalent owned export already loaded). Incomplete or missing export MUST fail with a clear user-visible error and MUST NOT invent content to fill gaps.

#### Scenario: Owner downloads PDF

- **WHEN** the owning guest chooses Download PDF on a trip with a complete GuidebookExport
- **THEN** the client produces a downloadable PDF derived from that export

#### Scenario: Owner prints

- **WHEN** the owning guest chooses Print on a trip with a complete GuidebookExport
- **THEN** the browser print flow uses the print view of that export

#### Scenario: Incomplete export fails honestly

- **WHEN** export JSON is missing or incomplete for print/PDF
- **THEN** the UI shows a clear error, does not invent hotels/prices/stops, and leaves the stored trip data intact

### Requirement: Render failure keeps trip data intact

When print or PDF rendering fails, the system MUST show a user-visible error. The underlying trip artifact and export JSON MUST remain unchanged. Failure MUST NOT be recovered by inventing schedule facts or calling a language model to fabricate document content.

#### Scenario: Renderer error is visible

- **WHEN** PDF or print rendering throws or returns failure
- **THEN** the guest sees an honest error and the trip remains reopenable with its prior days and stops
