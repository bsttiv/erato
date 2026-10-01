# Delta: composition-content

## ADDED Requirements

### Requirement: Composition status MUST be editable by editors in the create form and detail header
The create form and the detail header MUST offer a status control with the existing values `idea`, `in_progress`, `ready` (labels in Spanish). The detail control MUST be shown only to users who can edit, and read-only to others. A change MUST persist through the existing update (PATCH) call; on failure the UI MUST show an error and revert to the previous value. No backend or schema change is permitted.

#### Scenario: Editor changes status
- GIVEN an editor on the detail view with status "idea"
- WHEN they select "Lista"
- THEN the composition is PATCHed with `status: "ready"` and the dashboard groups it under Listas

#### Scenario: Non-editor
- GIVEN a viewer without edit permission
- WHEN the detail header renders
- THEN status is displayed as a read-only tag with no selectable control

#### Scenario: Save failure
- GIVEN the PATCH fails
- WHEN the user changes status
- THEN an error message is visible and the previous status is restored

#### Scenario: Create with status
- GIVEN the create form
- WHEN the user picks "En progreso" and saves
- THEN the composition is created with `status: "in_progress"`

### Requirement: Demo take dates MUST render in Spanish with an invalid-date guard
Demo take dates in the demo player and detail view MUST be formatted via a shared `formatDate` helper as day, short month, year in Spanish (e.g. "1 oct 2026"). An invalid or missing value MUST yield the raw value or an empty string, never "Invalid Date".

#### Scenario: Valid date
- GIVEN a demo dated `2026-10-01`
- WHEN it renders
- THEN the text is "1 oct 2026"

#### Scenario: Invalid date
- GIVEN a demo with date `not-a-date`
- WHEN it renders
- THEN the text does not contain "Invalid Date"
