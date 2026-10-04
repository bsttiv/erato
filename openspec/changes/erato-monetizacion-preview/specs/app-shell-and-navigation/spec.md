# Delta for App Shell and Navigation

Repo: `erato` (core frontend). Cloud pages are added by `erato-cloud` through the extension point
(see `plan-policy-port` and `plans-and-subscriptions`).

## ADDED Requirements

### Requirement: The app MUST provide a band management screen with its own route

The app MUST provide a band management route reachable from the dashboard top bar for
authenticated users. It MUST let members see the band name and members, let the owner create an
invitation link, see seats used (and the limit when the policy supplies one), remove members,
start, cancel and see a pending ownership transfer, and let non-owner members leave. The band
creation form and the "Crear banda" control live in this screen in the core. Creation MUST follow
the entitlements band-creation mode: in direct mode the control opens the core form; in hand-off
mode it leads to the host payment entry instead (see `plan-policy-port`). Unauthenticated access
MUST redirect to login.
(Previously: creation offered only when entitlements allowed it, with no hand-off mode.)
Copy MUST be Spanish, informal "tu" address, no exclamation marks, no emoji, built from
design-system primitives and tokens.

#### Scenario: Owner sees management controls

- GIVEN the band owner opens the screen
- WHEN it renders
- THEN invitation, remove-member and transfer controls MUST be present

#### Scenario: Member sees leave only

- GIVEN a non-owner member opens the screen
- WHEN it renders
- THEN a leave control MUST be present and owner-only controls MUST NOT be

#### Scenario: Band full feedback

- GIVEN the backend answers 409 (band full) to a join
- WHEN the joining user sees the result
- THEN a clear Spanish message MUST explain the band has no free seats

#### Scenario: Direct creation form

- GIVEN entitlements report direct band creation
- WHEN the user with no band activates the create control and submits a valid name
- THEN the core form MUST call the band creation endpoint and the new band MUST appear

#### Scenario: Hand-off to payments

- GIVEN entitlements deny direct creation and report hand-off, with a host payment entry registered
- WHEN the user activates the create control
- THEN they MUST be taken to the host payment entry and no core creation form MUST be shown

#### Scenario: Creation not actionable

- GIVEN entitlements deny direct creation and no host payment entry is registered
- WHEN the user opens the screen with no band
- THEN no create control MUST be actionable

#### Scenario: Self-hosted creation

- GIVEN a self-hosted app (unlimited policy, no host extension)
- WHEN any registered user opens the screen
- THEN the direct creation form MUST be available and no payment control MUST be present

#### Scenario: Redirect when logged out

- GIVEN an unauthenticated visitor
- WHEN they open the band route
- THEN they MUST be redirected to login

### Requirement: The composition page MUST host the history panel and a conflict dialog

The composition page MUST provide the history panel entry per versioned section and a conflict
dialog opened per conflicting section on save, both as real overlays following the existing modal
rules (backdrop, centered, Escape and backdrop dismissal, focus return). Dismissing the conflict
dialog MUST NOT discard the user's local edit.

#### Scenario: Dialog dismissal keeps the edit

- GIVEN a conflict dialog for lyrics
- WHEN the user presses Escape
- THEN the dialog MUST close and the local lyrics edit MUST remain in the editor

#### Scenario: Dialog overlay rules

- GIVEN the conflict dialog is open
- WHEN it renders
- THEN it MUST show a backdrop above page content and be centered

### Requirement: The shell MUST expose an extension point for host pages

The shell MUST allow a host to register extra routes and navigation entries (mechanism fixed in
design). Registered entries MUST appear in the existing navigation only for authenticated users and
resolve within the same shell and auth state. With none registered, the shell MUST be unchanged. The
extension point exists only for payment, billing and subscription pages (OD-2); band, invitation,
member and history UI MUST NOT be provided through it. A host MUST also be able to register the
payment entry that the core "Crear banda" control hands off to.

#### Scenario: Registered entry appears

- GIVEN a host registers a route and a nav entry
- WHEN an authenticated user views the dashboard
- THEN the entry MUST be visible and activating it MUST render the host page in the shell

#### Scenario: Not registered

- GIVEN no host registration
- WHEN the shell renders
- THEN no extra entries MUST appear

### Requirement: Editing controls MUST reflect read-only state

When the effective role is `viewer`, or the band is inactive for the user's derived role, the page
MUST render editing controls disabled or absent (matching the existing status-control rule) and MUST
show the read-only banner defined in `sharing-and-visibility` where applicable.

#### Scenario: Viewer

- GIVEN a viewer role
- WHEN the composition page renders
- THEN section editors MUST be read-only

## MODIFIED Requirements

### Requirement: No deferred PDF affordance without backing behavior MUST be rendered

Per decision D11, affordances shown in the PDF with no corresponding backend behavior (an OAuth
"Continuar con Google" control, a password-reset link, dashboard search, and terms/privacy links
inside the app) MUST NOT be rendered, whether functional or as a disabled/dead control. The band
entity is no longer deferred: it is implemented by this change and its controls MUST be rendered
according to `bands-and-membership`. The landing's placeholder privacy/terms footer links belong to
the landing capability and do not apply to the app shell.
(Previously: the band entity was also a deferred affordance that MUST NOT be rendered.)

#### Scenario: The login page has no Google sign-in control

- GIVEN the login page renders
- WHEN its controls are inspected
- THEN there MUST NOT be a "Continuar con Google" button or any other unimplemented OAuth control

#### Scenario: No deferred affordance appears in a disabled state as a placeholder

- GIVEN any of the still-deferred affordances (Google sign-in, password reset, dashboard search,
  terms/privacy links inside the app)
- WHEN the relevant page renders
- THEN none of these affordances MUST appear in the DOM, including in a disabled or placeholder
  form

#### Scenario: Band controls are rendered where backed

- GIVEN the band feature is implemented
- WHEN the dashboard top bar renders for an authenticated user
- THEN a link to the band screen MUST be present and MUST NOT be a disabled placeholder
