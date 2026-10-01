# Sharing and Visibility Specification

## Purpose

Defines the behavioral contract for composition sharing, per AGENTS.md ("Compartir"): a
composition is shared via a link, and is either public (viewable by anyone with the link, editable
only by invited users) or private (viewable and editable only by invited users). This spec
describes authorization behavior only — it does not define how visibility or invitation state is
persisted (that is a MongoDB schema concern, out of scope per AGENTS.md rule 1).

## Requirements

### Requirement: A public composition MUST be viewable by anyone with its link, without an account

Anyone possessing the share link of a public composition MUST be able to view it, with no
authentication required.

#### Scenario: Anonymous visitor views a public composition via its link

- GIVEN a composition is marked public
- WHEN an unauthenticated visitor requests it using its share link
- THEN the backend MUST return the composition's viewable data
- AND MUST NOT require authentication for this request

#### Scenario: Anonymous visitor cannot edit a public composition

- GIVEN a composition is marked public
- WHEN an unauthenticated visitor attempts to modify it (any write operation)
- THEN the backend MUST reject the request with a 401 or 403 status code
- AND no data MUST be modified

### Requirement: Only invited users MUST be able to edit a public composition

Editing a public composition MUST be restricted to users who have been explicitly invited to that
composition, even though viewing is open to anyone with the link.

#### Scenario: An invited, authenticated user edits a public composition

- GIVEN a composition is marked public and a user has been invited to it
- WHEN that authenticated, invited user submits an edit request
- THEN the backend MUST verify the invitation and allow the modification

#### Scenario: An authenticated but non-invited user cannot edit a public composition

- GIVEN a composition is marked public and a user is authenticated but has not been invited to it
- WHEN that user submits an edit request
- THEN the backend MUST reject the request with a 403 status code
- AND no data MUST be modified

### Requirement: A private composition MUST be visible only to invited users

A composition marked private MUST NOT be viewable or editable by anyone except users explicitly
invited to it — the share link alone MUST NOT grant access.

#### Scenario: An invited user views a private composition

- GIVEN a composition is marked private and a user has been invited to it
- WHEN that authenticated, invited user requests the composition (via the link or directly)
- THEN the backend MUST return the composition's data

#### Scenario: A non-invited user cannot view a private composition, even with the link

- GIVEN a composition is marked private
- WHEN a user who has not been invited (authenticated or not) requests it using its share link
- THEN the backend MUST reject the request with a 403 or 404 status code
- AND MUST NOT include any of the composition's data in the response

#### Scenario: A non-invited user cannot edit a private composition

- GIVEN a composition is marked private
- WHEN a user who has not been invited attempts to modify it
- THEN the backend MUST reject the request with a 403 or 404 status code
- AND no data MUST be modified

### Requirement: Visibility and edit permissions MUST be enforced in the backend, never only in the frontend

Per AGENTS.md: permission checks MUST happen on the backend for every request. The frontend MAY
hide UI controls for a better experience, but that MUST NOT be the only enforcement mechanism.

#### Scenario: A direct API request bypassing the frontend is still checked

- GIVEN a client sends a request directly to a backend endpoint (not through the rendered UI)
- WHEN that request would modify or reveal a composition the requester is not authorized to access
- THEN the backend MUST apply the same visibility/edit checks as it would for a UI-originated
  request
- AND MUST reject the request identically regardless of how it was sent
