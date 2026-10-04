# Delta for Composition Content

Repo: `erato`. Versioning behavior is specified in `composition-versioning`; this delta covers the
API contract changes only.

## ADDED Requirements

### Requirement: Versioned section writes MUST accept an optional expected revision and MAY return 409

The lyrics, chords and tablature write endpoints MUST accept an optional `expected_rev`. When
supplied and not equal to the stored revision, the endpoint MUST respond 409 with the conflict
payload defined in `composition-versioning`. When omitted, the write MUST behave as today
(unconditional). The todos endpoint MUST NOT accept or enforce `expected_rev` and MUST remain
last-write-wins with its bare-array body. Responses of successful writes MUST include the new
revision.

#### Scenario: Matching revision

- GIVEN chords at revision 2
- WHEN an editor calls `PUT /api/compositions/{id}/chords` with `expected_rev: 2`
- THEN the response MUST be successful and report revision 3

#### Scenario: Stale revision

- GIVEN chords at revision 3
- WHEN a client sends `expected_rev: 2`
- THEN the response MUST be 409 and the stored chords MUST be unchanged

#### Scenario: Todos unaffected

- GIVEN a todos write as a bare array
- WHEN an editor submits it
- THEN it MUST succeed with no revision check and return the bare array

#### Scenario: Tablature whole-array write

- GIVEN tablature at revision 1
- WHEN a client sends the full `tabs` array with `expected_rev: 1`
- THEN the whole array MUST be replaced and the revision MUST be 2

#### Scenario: Validation still applies

- GIVEN an invalid body together with a stale `expected_rev`
- WHEN the backend validates the request
- THEN it MUST respond 422 before any conflict check

## MODIFIED Requirements

### Requirement: The composition response MUST be a flat object with typed sections, not a generic wrapper

`CompositionResponse` MUST expose `chords`, `tablature`, `lyrics`, `todos`, `demos`, `members` and
`section_revs` (the per-section revision counters for lyrics, chords and tablature) as top-level,
individually typed fields. It MUST NOT nest them inside a generic `sections: Record<string, any>`
wrapper, and the frontend MUST consume this flat shape exactly as the backend defines it.
(Previously: the response had no revision counters field.)

#### Scenario: Reading a composition returns a flat, typed response

- GIVEN a composition exists with chords, tablature, lyrics, and todos
- WHEN a client calls `GET /api/compositions/{id}`
- THEN the response MUST include top-level `chords`, `tablature`, `lyrics`, `todos`, `demos`,
  `members` and `section_revs` fields
- AND MUST NOT include a `sections` wrapper object

#### Scenario: The frontend's response type matches the backend's actual fields

- GIVEN the frontend's `CompositionResponse` TypeScript type
- WHEN compared against the backend's `CompositionResponse` Pydantic model
- THEN every field present in the frontend type MUST correspond to a field the backend actually
  returns
- AND the frontend type MUST NOT declare fields the backend never sends (e.g. a phantom `slug` or
  `is_public`)

#### Scenario: Legacy composition reports zero revisions

- GIVEN a composition stored without revision counters
- WHEN it is read
- THEN `section_revs` MUST report 0 for lyrics, chords and tablature

### Requirement: The backend MUST compute and return an advisory user role on the composition response

`CompositionResponse` MUST include a `user_role` field computed server-side (using the same
resolution logic the backend already applies for authorization, including band-derived roles)
reflecting the requesting user's relationship to the composition (e.g. `owner`, `editor`, `viewer`,
or absent/null for an unauthenticated or unrelated requester). This field is advisory UI state only;
it MUST NOT be used by the backend as the sole authorization mechanism for any write.
(Previously: resolution did not include band-derived roles.)

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

#### Scenario: A band member sees a band-derived role

- GIVEN a member of a band with a composition shared as `band_editable` true
- WHEN they call `GET /api/compositions/{id}`
- THEN `user_role` MUST be `"editor"`, and `"viewer"` when `band_editable` is false
