# Composition Content Specification

## Purpose

Defines the stored shape and API contract of a composition's editable content sections: the
multi-tablature `tabs` model, the per-section endpoint contract (chords, tablature, lyrics, todos),
the flat `CompositionResponse` shape the frontend must consume, backend-computed advisory role
state, and the optional composition metadata fields (key, tempo, time signature, style tags,
status). This is a new capability introduced to fix the frontend/backend contract drift and to
carry the multi-tablature model approved under decision D1.

## Requirements

### Requirement: A tablature section MUST store zero or more named tab entries

The `tablature` section of a composition MUST be represented as `{ tabs: TabEntry[] }`, where each
`TabEntry` has a stable `id`, a required non-empty `title` (1-80 characters), a `strings` count
(default 6), and a `columns` array. A `columns` element MUST be either a list of per-string
fret/technique strings or the literal barline marker `"|"`. This replaces the previous single-tab
`{ strings, content }` shape.

#### Scenario: A composition stores two independently titled tablatures

- GIVEN a composition with an empty tablature section
- WHEN a client submits `tabs: [{ id: "t1", title: "Riff intro", strings: 6, columns: [...] }, { id: "t2", title: "Solo", strings: 6, columns: [...] }]`
- THEN the backend MUST persist both entries under the composition's `tablature.tabs` array
- AND each entry's `title`, `strings`, and `columns` MUST be stored without alteration

#### Scenario: A tab round-trips through save and reload with its identity intact

- GIVEN a composition has a tablature section containing a tab entry with a given `id`, `title`,
  `strings`, and `columns`
- WHEN the composition is saved and then retrieved again
- THEN the returned tab entry MUST have the same `id`, `title`, `strings`, and `columns` as when it
  was saved

#### Scenario: A tab entry without a title is rejected

- GIVEN a client submits a tab entry with an empty or missing `title`
- WHEN the backend validates the request body
- THEN the backend MUST reject the request with a 422 validation error
- AND MUST NOT persist the invalid entry

#### Scenario: A composition with an empty tablature section returns an empty tabs array

- GIVEN a newly created composition that has never had a tablature saved
- WHEN its tablature section is read
- THEN the backend MUST return `{ tabs: [] }` rather than an error or null

### Requirement: Tablature add, rename, delete, and reorder operations MUST be expressed as a whole-array write

The tablature section MUST be read and written as a single unit via `GET /api/compositions/{id}/tablature`
and `PUT /api/compositions/{id}/tablature`. There MUST NOT be separate per-tab sub-resource
endpoints. Adding, renaming, deleting, or reordering tabs MUST be achieved by the client sending the
complete, updated `tabs` array in one `PUT` request.

#### Scenario: Adding a tab is a PUT of the full array including the new entry

- GIVEN a composition already has one tab entry
- WHEN a client calls `PUT /api/compositions/{id}/tablature` with a `tabs` array containing the
  existing entry plus one new entry
- THEN the backend MUST persist both entries
- AND the stored array order MUST match the order submitted in the request

#### Scenario: Deleting a tab is a PUT of the full array without that entry

- GIVEN a composition has two tab entries
- WHEN a client calls `PUT /api/compositions/{id}/tablature` with a `tabs` array containing only one
  of the two entries
- THEN the backend MUST persist only the remaining entry
- AND the removed entry MUST NOT appear in the next read of the section

#### Scenario: Reordering tabs is a PUT with entries in the new order

- GIVEN a composition has tab entries in order `[A, B]`
- WHEN a client calls `PUT /api/compositions/{id}/tablature` with the same entries in order `[B, A]`
- THEN a subsequent read of the section MUST return the entries in order `[B, A]`

### Requirement: Derived ASCII tablature text MUST NOT be persisted

The ASCII text representation of a tab (produced by `tabToText()`) is a derived, display-only
artifact computed from `columns`. The backend MUST NOT accept or store a separate ASCII/text field
alongside `columns` for a tab entry.

#### Scenario: A tab entry has no stored text field

- GIVEN a tab entry is persisted with a `columns` array
- WHEN the stored document is inspected
- THEN it MUST NOT contain a rendered ASCII text field for that entry
- AND any ASCII representation needed for display MUST be computed on read from `columns`

### Requirement: The composition response MUST be a flat object with typed sections, not a generic wrapper

`CompositionResponse` MUST expose `chords`, `tablature`, `lyrics`, `todos`, `demos`, and `members`
as top-level, individually typed fields. It MUST NOT nest them inside a generic
`sections: Record<string, any>` wrapper, and the frontend MUST consume this flat shape exactly as
the backend defines it.

#### Scenario: Reading a composition returns a flat, typed response

- GIVEN a composition exists with chords, tablature, lyrics, and todos
- WHEN a client calls `GET /api/compositions/{id}`
- THEN the response MUST include top-level `chords`, `tablature`, `lyrics`, `todos`, `demos`, and
  `members` fields
- AND MUST NOT include a `sections` wrapper object

#### Scenario: The frontend's response type matches the backend's actual fields

- GIVEN the frontend's `CompositionResponse` TypeScript type
- WHEN compared against the backend's `CompositionResponse` Pydantic model
- THEN every field present in the frontend type MUST correspond to a field the backend actually
  returns
- AND the frontend type MUST NOT declare fields the backend never sends (e.g. a phantom `slug` or
  `is_public`)

### Requirement: Each content section MUST have its own typed read and write endpoint

Chords, tablature, lyrics, and todos MUST each be read and written through their own typed
endpoint (`/chords`, `/tablature`, `/lyrics`, `/todos`) accepting and returning that section's
specific shape. There MUST NOT be a single generic `/sections/{type}` endpoint accepting an
untyped `{ content }` envelope.

#### Scenario: Updating chords uses the typed chords endpoint

- GIVEN a composition an authorized editor wants to update
- WHEN the client calls `PUT /api/compositions/{id}/chords` with a `ChordsSection` body
  (`instrument`, `entries[]` with `bar`, `notes`, `name`)
- THEN the backend MUST persist the chords section
- AND MUST return the updated `ChordsSection` directly, not wrapped in a generic envelope

#### Scenario: Updating lyrics uses the typed lyrics endpoint

- GIVEN a composition an authorized editor wants to update
- WHEN the client calls `PUT /api/compositions/{id}/lyrics` with a `LyricsSection` body
  (`content`, bracket markup text)
- THEN the backend MUST persist the lyrics section
- AND MUST return the updated `LyricsSection` directly

#### Scenario: Updating todos uses the typed todos endpoint with a bare array

- GIVEN a composition an authorized editor wants to update
- WHEN the client calls `PUT /api/compositions/{id}/todos` with a bare array of `TodoItem`
  (`text`, `done`)
- THEN the backend MUST persist the todos as a bare array under the composition
- AND MUST return the updated bare array, not an object wrapping it

### Requirement: The backend MUST compute and return an advisory user role on the composition response

`CompositionResponse` MUST include a `user_role` field computed server-side (using the same
resolution logic the backend already applies for authorization) reflecting the requesting user's
relationship to the composition (e.g. `owner`, `editor`, `viewer`, or absent/null for an
unauthenticated or unrelated requester). This field is advisory UI state only; it MUST NOT be used
by the backend as the sole authorization mechanism for any write.

#### Scenario: An owner sees their own role on the response

- GIVEN a user owns a composition
- WHEN that user calls `GET /api/compositions/{id}`
- THEN the response's `user_role` MUST reflect ownership (e.g. `"owner"`)

#### Scenario: An editor-invited user sees an editor role on the response

- GIVEN a user has been invited to a composition with editor permissions
- WHEN that user calls `GET /api/compositions/{id}`
- THEN the response's `user_role` MUST reflect editing permission (e.g. `"editor"`)

#### Scenario: user_role is advisory only and never substitutes for backend enforcement

- GIVEN a response's `user_role` field indicates editing permission due to a client-side bug or
  stale cache
- WHEN that client submits a write request the backend's authorization logic would reject
- THEN the backend MUST reject the write based on its own authorization check
- AND MUST NOT consult or trust a client-supplied `user_role` value for that decision

### Requirement: A composition MAY declare optional descriptive metadata fields

A composition document MAY include `key` (tonalidad), `bpm` (tempo), `time_signature` (compás),
`style_tags` (a list of free-text style labels), and `status` (one of `in_progress`, `ready`, or
`idea`, mapped from `en progreso` / `lista` / `idea`). All of these fields MUST be optional and
nullable, and none of them MUST be required to create a composition.

#### Scenario: A composition is created without any metadata fields

- GIVEN a client creates a composition supplying only a title
- WHEN the composition is created
- THEN the creation MUST succeed
- AND `key`, `bpm`, `time_signature`, `style_tags`, and `status` MUST be absent or null on the
  response

#### Scenario: A composition is created or updated with metadata fields

- GIVEN a client supplies `key: "Am"`, `bpm: 72`, `time_signature: "4/4"`,
  `style_tags: ["acústico"]`, and `status: "in_progress"` when creating or updating a composition
- WHEN the composition is persisted
- THEN all five fields MUST be stored
- AND a subsequent read MUST return them unchanged

#### Scenario: Status accepts only the three defined values

- GIVEN a client submits a `status` value outside `in_progress`, `ready`, `idea`
- WHEN the backend validates the request
- THEN the backend MUST reject the request with a 422 validation error

#### Scenario: A pre-existing composition with no metadata fields is read without error

- GIVEN a composition persisted before metadata fields existed, with no `key`, `bpm`,
  `time_signature`, `style_tags`, or `status` stored
- WHEN that composition is read
- THEN the read MUST succeed
- AND the missing fields MUST be returned as null/absent rather than causing a validation error
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
