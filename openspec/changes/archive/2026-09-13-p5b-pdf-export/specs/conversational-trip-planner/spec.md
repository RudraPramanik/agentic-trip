## ADDED Requirements

### Requirement: Reopenable trip is printable and downloadable

After a successful generate produces a reopenable structured trip, the guest MUST be able to print or download a guidebook document that projects that same structured artifact. The print/PDF document MUST NOT be produced by a separate language-model rewrite of days, stops, or coordinates.

#### Scenario: Print or download matches reopenable days

- **WHEN** a guest reopens a generated trip and prints or downloads the guidebook
- **THEN** the document’s days and stops match the reopenable structured trip (via GuidebookExport)

#### Scenario: No LLM rewrite for the export document

- **WHEN** print or PDF is produced for a trip
- **THEN** day structure and stop identities are not rewritten by a language-model call on that path
