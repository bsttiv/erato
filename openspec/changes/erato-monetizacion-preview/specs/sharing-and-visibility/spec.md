# Delta for Sharing and Visibility

Repo: `erato`. Plan-dependent gates are expressed through `PlanPolicy`; the paid rules live in
`plans-and-subscriptions` (`erato-cloud`). Under the default `UnlimitedPlanPolicy` every gate allows.

## ADDED Requirements

### Requirement: Effective role MUST be resolved in a fixed order including band roles

The effective role on a composition MUST be resolved in this order, first match wins: owner; invited
composition member role (`editor` or `viewer`); band member of the composition's `band_id` with
`band_editable` true gives `editor`; band member with `band_editable` false gives `viewer`; public
composition gives `viewer`; otherwise no access (404). Band context MUST be loaded only when
`band_id` is set. Compositions without `band_id` MUST resolve exactly as before.

#### Scenario: Owner outranks everything

- GIVEN a user who owns a composition that is also shared with their band
- WHEN the role is resolved
- THEN it MUST be `owner`

#### Scenario: Invited role outranks band role

- GIVEN a band member with `band_editable` true who is also invited as `viewer`
- WHEN the role is resolved
- THEN it MUST be `viewer`

#### Scenario: Band member editable

- GIVEN a composition with `band_id = G`, `band_editable` true, and a member of G
- WHEN the role is resolved
- THEN it MUST be `editor`

#### Scenario: Band member not editable

- GIVEN the same composition with `band_editable` false
- WHEN the role is resolved
- THEN it MUST be `viewer`

#### Scenario: Private composition and non-member

- GIVEN a private composition shared with band G and a user outside G
- WHEN the user requests it
- THEN the backend MUST respond 404

#### Scenario: No band context loaded without band_id

- GIVEN a composition with no `band_id`
- WHEN the role is resolved
- THEN no band lookup MUST occur

### Requirement: Band-derived and invited write access MUST end while the band is not active

When `PlanPolicy` reports a composition's band as not active, `require()` MUST reject writes from
band-derived and invited roles on that composition with 403 and a band-inactive code. The owner MUST
keep full edit. Sharing changes (inviting, changing member roles, changing band association) MUST be
refused while inactive. Reads MUST remain allowed. Under `UnlimitedPlanPolicy` bands are always
active.

#### Scenario: Member blocked

- GIVEN an inactive band and an editor-derived member
- WHEN they write
- THEN the backend MUST respond 403 with the band-inactive code and change nothing

#### Scenario: Owner exempt

- GIVEN the same band
- WHEN the composition owner writes
- THEN it MUST succeed

#### Scenario: Always active by default

- GIVEN `UnlimitedPlanPolicy`
- WHEN a band member with edit access writes
- THEN it MUST succeed

### Requirement: Sharing with people MUST be gated by the policy

Granting composition-level member roles to people MUST consult `PlanPolicy`'s sharing gate; when it
denies, the backend MUST respond 403 with the sharing gate code. The public read-only link MUST NOT
be gated and MUST work for every owner.

#### Scenario: Denied

- GIVEN a policy denying sharing
- WHEN an owner grants a member role
- THEN the backend MUST respond 403 with the sharing code

#### Scenario: Public link always available

- GIVEN a policy denying sharing
- WHEN an owner sets the composition public
- THEN it MUST succeed and anonymous visitors MUST be able to view it

### Requirement: Anonymous viewers of a public composition MUST see the "Guardado en Erato" footer

An unauthenticated viewer of a public composition MUST see a footer reading "Guardado en Erato"
with a link to the registration page. Authenticated users MUST NOT see it. It MUST be styled with
design-system tokens, work in both themes and be keyboard accessible.

#### Scenario: Anonymous

- GIVEN a public composition
- WHEN an unauthenticated visitor opens its link
- THEN the footer MUST be present and its link MUST target the register route

#### Scenario: Authenticated

- GIVEN the same composition
- WHEN a logged-in user views it
- THEN the footer MUST NOT be rendered

#### Scenario: Private composition

- GIVEN a private composition the visitor cannot access
- WHEN the visitor opens it
- THEN no composition content and no footer MUST be shown

### Requirement: Band sharing MUST be a control separate from visibility

The sharing modal MUST offer band sharing (choose a band and editable or view-only) as its own
control, shown only when the user's entitlements allow it (user-scoped: own subscription or
membership in an active band, OD-4) and the user belongs to a band. It MUST NOT
appear as a third visibility option. Per-member roles MUST be assignable only to members of the
composition's band.

#### Scenario: Separate control

- GIVEN the sharing modal for a user in a band
- WHEN it renders
- THEN visibility MUST show exactly two options and band sharing MUST be a distinct control

#### Scenario: Hidden when not allowed

- GIVEN entitlements deny sharing with people
- WHEN the modal renders
- THEN band sharing and member-role controls MUST NOT be actionable and the public link control MUST remain

#### Scenario: Inherited from the band

- GIVEN a user with no own subscription who is a member of an active band, so the policy grants sharing
- WHEN they open the sharing modal of any composition they own, including one not yet shared with a band
- THEN band sharing MUST be actionable, and the member-role controls MUST be actionable once the composition has a band

#### Scenario: Assign a role to a band member

- GIVEN a composition shared with band G
- WHEN the owner assigns `viewer` to a member of G
- THEN the composition MUST store that member role
- AND assigning a role to a non-member of G MUST be rejected

### Requirement: The dashboard MUST list compositions shared with the user's bands

The dashboard MUST include compositions whose `band_id` belongs to a band the user is a member of,
alongside owned and invited ones, marking the band-derived ones.

#### Scenario: Band composition listed

- GIVEN a member of band G and a composition shared with G
- WHEN the dashboard loads
- THEN the composition MUST be listed

#### Scenario: After leaving

- GIVEN the user left G
- WHEN the dashboard loads
- THEN G's compositions MUST NOT be listed unless otherwise accessible

### Requirement: A read-only banner MUST explain inactive bands

When the current composition is read-only because its band is inactive, the UI MUST show a banner
saying so (Spanish copy) and MUST disable editing controls for affected roles.

#### Scenario: Banner shown

- GIVEN an inactive band and a member viewing a band composition
- WHEN the page renders
- THEN the banner MUST be visible and edit controls MUST be disabled

## MODIFIED Requirements

### Requirement: Only invited editor-role users MUST be able to edit a public composition

Editing a public composition MUST be restricted to its owner, users invited to it with the editor
role, and members of its band when `band_editable` is true. A user invited with the viewer-only role
("solo ver"), a band member with `band_editable` false, and any other user MUST be able to view the
composition per the public-visibility rule but MUST NOT edit it.
(Previously: restricted to users invited with the editor role; band-derived editors did not exist.)

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

#### Scenario: An editable band member edits a public composition

- GIVEN a public composition shared with band G with `band_editable` true and a member of G
- WHEN that member submits an edit request and the band is active
- THEN the backend MUST allow the modification

#### Scenario: A non-editable band member cannot edit

- GIVEN the same composition with `band_editable` false
- WHEN a member of G submits an edit request
- THEN the backend MUST reject it with 403 and modify nothing

### Requirement: A private composition MUST be visible only to invited users

A composition marked private MUST NOT be viewable or editable by anyone except its owner, users
explicitly invited to it, and members of the band it is shared with — the share link alone MUST NOT
grant access.
(Previously: visible only to invited users; band members did not exist.)

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

#### Scenario: A band member views a private composition shared with their band

- GIVEN a private composition shared with band G and a member of G
- WHEN that member requests it
- THEN the backend MUST return the data

### Requirement: An invite MUST support an editor role and a viewer-only role

Composition-level member roles MUST be `editor` or `viewer` (displayed as "solo ver") and MUST be
assigned only to members of the composition's band, from the sharing modal. Band invitations
themselves carry no role. A viewer role MUST grant view and MUST NOT grant edit access.
(Previously: composition invitations by link carried the role; invitations now target bands and
carry no role, so roles are assigned to existing band members.)

#### Scenario: Creating a viewer-only role succeeds

- GIVEN an authorized owner and a band member of the composition's band
- WHEN they submit `role: "viewer"`
- THEN the backend MUST accept the request and store the viewer role
- AND MUST reject any `role` value other than `editor` or `viewer`

#### Scenario: A viewer role grants view but not edit access

- GIVEN a user with the viewer member role on a composition
- WHEN that user requests the composition
- THEN the backend MUST allow the view request
- AND MUST reject any edit request from that user with a 403 status code

#### Scenario: Non-band-member cannot receive a role

- GIVEN a user who is not a member of the composition's band
- WHEN the owner tries to assign them a role
- THEN the backend MUST reject the request and store nothing
