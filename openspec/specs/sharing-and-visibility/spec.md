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

### Requirement: Only invited editor-role users MUST be able to edit a public composition

Editing a public composition MUST be restricted to users who have been explicitly invited to that
composition **with the editor role**. A user invited with the viewer-only role ("solo ver") MUST be
able to view the composition per the public-visibility rule, but MUST NOT be able to edit it, even
though they are an invited member.
(Previously: editing a public composition was restricted to "invited users" without a role
distinction, because only the `editor` role existed.)

#### Scenario: An invited editor-role user edits a public composition

- GIVEN a composition is marked public and a user has been invited to it with the editor role
- WHEN that authenticated, invited user submits an edit request
- THEN the backend MUST verify the invitation and role and allow the modification

#### Scenario: An authenticated but non-invited user cannot edit a public composition

- GIVEN a composition is marked public and a user is authenticated but has not been invited to it
- WHEN that user submits an edit request
- THEN the backend MUST reject the request with a 403 status code
- AND no data MUST be modified

#### Scenario: An invited viewer-role user cannot edit a public composition

- GIVEN a composition is marked public and a user has been invited to it with the viewer-only role
- WHEN that authenticated, invited user submits an edit request
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
### Requirement: Composition visibility MUST offer exactly two options everywhere in the UI

Per decision D7, composition visibility has exactly two values, `public` ("con enlace") and
`private` ("privada"). Every UI surface that lets a user set or change visibility — including the
composition-creation flow and the sharing modal — MUST present exactly these two options and MUST
NOT offer a third category (e.g. a "la banda" / band-wide option) that the backend does not support.

#### Scenario: The composition-creation form offers two visibility options

- GIVEN the full-page composition-creation flow
- WHEN its visibility control renders
- THEN it MUST present exactly two options, public ("con enlace") and private ("privada")
- AND MUST NOT present a third option

#### Scenario: The sharing modal offers two visibility options

- GIVEN the sharing modal for an existing composition
- WHEN its visibility control renders
- THEN it MUST present exactly two options, matching the creation flow exactly

### Requirement: An invite MUST support an editor role and a viewer-only role

Creating an invitation MUST accept a `role` of either `editor` or `viewer` (displayed as "solo
ver"). A viewer-role invitation MUST grant the invited user the ability to view the composition
(per existing public/private view rules) and MUST NOT grant edit access.

#### Scenario: Creating a viewer-only invite succeeds

- GIVEN an authorized owner creates an invitation for a composition
- WHEN they submit `role: "viewer"`
- THEN the backend MUST accept the request and create the invitation with the viewer role
- AND MUST reject any `role` value other than `editor` or `viewer`

#### Scenario: A redeemed viewer invite grants view but not edit access

- GIVEN a user redeems an invitation created with `role: "viewer"`
- WHEN that user subsequently requests the composition
- THEN the backend MUST allow the view request
- AND MUST reject any edit request from that user with a 403 status code

### Requirement: The member list response MUST return a resolved display projection, not raw identifiers

The backend MUST return a member list containing, for each member, a display name, email, avatar
initials, a role label (including a distinguishable "solo ver" / viewer label), and whether the
member's invitation is still pending. This projection MUST be computed server-side from existing
user and invitation data; it is a response-shape addition, not a change to the underlying stored
`MemberItem`/invitation schema's authoritative fields beyond the new viewer role value.

#### Scenario: The member list includes name, email, initials, role, and pending state

- GIVEN a composition has one active editor member and one pending viewer invitation
- WHEN an authorized user requests the composition's member list
- THEN the response MUST include, for the active member, their display name, email, computed
  avatar initials, and a role label of "editor"
- AND MUST include, for the pending invitation, its invited email, a role label of "solo ver", and
  a pending-state indicator

#### Scenario: A non-owner, non-invited requester cannot read the member list

- GIVEN a composition a user has no relationship to
- WHEN that user requests the member list
- THEN the backend MUST reject the request per existing visibility/authorization rules
- AND MUST NOT include any member's name, email, or role in the response
