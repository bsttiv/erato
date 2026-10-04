# Plan Policy Port Specification

Repo: `erato`. The cloud implementation lives in `erato-cloud` (see `plans-and-subscriptions`).

## Purpose

Defines the contract through which the public core asks "what is allowed" without containing any
subscription, billing or quota logic. The default implementation allows everything, so self-hosters
get every feature. The private repo replaces it via documented seams.

## Requirements

### Requirement: The core MUST define a PlanPolicy port with a closed set of questions

`PlanPolicy` MUST answer: whether the user may share a composition with people, whether the user may
create a band directly (through `POST /api/bands`), whether history is available to the user, the
demo count limit for a composition (or none), the seat limit for a band (or none), whether a band
is active, and a transfer hook invoked
on transfer acceptance before the core completes the owner and role swap: the policy MUST confirm
or refuse the subscription step, and the core MUST complete the swap only on confirmation (a refusal
leaves owner and roles unchanged). The questions about sharing with people, history, the demo limit
and direct band creation are scoped to the user: the host policy evaluates the user, whose
entitlements may come from the user's own subscription OR from membership in any active band
(OD-4); the core passes no composition or band context for these questions. The port MUST NOT
reference plan names, prices or provider names.
(Previously: the band-creation question was not qualified as direct creation.)

#### Scenario: Contract surface

- GIVEN the port definition
- WHEN its methods are inspected
- THEN it MUST expose exactly the questions and hook above
- AND no plan name, price or billing-provider identifier MUST appear in the core

#### Scenario: Questions are user-scoped

- GIVEN a stand-in policy that records its inputs
- WHEN the history, sharing and demo-limit questions are asked
- THEN the policy MUST receive the user and no composition or band context

### Requirement: UnlimitedPlanPolicy MUST be the default and MUST allow everything

`UnlimitedPlanPolicy` MUST allow sharing with people, direct band creation and history; MUST report
no demo limit and no seat limit; MUST report every band as active; and MUST implement the transfer
hook as an immediate confirmation. The public app MUST use it when nothing overrides it. A
self-hosted `erato` therefore has no payment surface at all: any registered user can create bands
and every feature is free and unlimited.

#### Scenario: Defaults

- GIVEN the public app without overrides
- WHEN the policy is resolved
- THEN it MUST be `UnlimitedPlanPolicy` and every gate MUST allow

#### Scenario: Self-hosted has no payment UI

- GIVEN the public app without overrides and no registered extension
- WHEN an authenticated user uses bands, sharing and history
- THEN no checkout, plan, subscription or seat-purchase control MUST be rendered

#### Scenario: No subscription logic in the core

- GIVEN the public `erato` repository
- WHEN searched for subscription, billing or quota code
- THEN none MUST be found beyond the port and the unlimited default

#### Scenario: Core suite stands alone

- GIVEN only the `erato` repository
- WHEN its test suite runs
- THEN it MUST pass with all features available

### Requirement: The policy MUST be obtained through an overridable dependency getter

The core MUST resolve the policy per request through a single getter (`get_plan_policy`) that a host
application can replace with `app.dependency_overrides`. No code path MAY instantiate a policy
bypassing the getter.

#### Scenario: Override takes effect

- GIVEN a test policy that denies band creation installed via the override
- WHEN a user creates a band
- THEN the backend MUST respond 403

#### Scenario: Override contract test

- GIVEN the core test suite
- WHEN it runs a stand-in policy mimicking the cloud (denies, limits, inactive band)
- THEN every gate call site MUST honor the stand-in answers

### Requirement: Plan-gate refusals MUST be machine readable

Whenever the core refuses an action because the policy denied it, the response MUST be 403 and MUST
contain a stable code identifying the gate (sharing, band creation, history, demo limit, band
inactive) so the UI can react without parsing text. Seat-full refusals use 409 per
`bands-and-membership`.

#### Scenario: Coded refusal

- GIVEN the policy denies history
- WHEN history is requested
- THEN the body MUST carry the history gate code

### Requirement: An entitlements endpoint MUST report gate outcomes to the UI

An authenticated endpoint MUST return, for the current user, whether sharing with people, direct
band creation and history are allowed, the demo limit per composition (null when none), an
indicator of whether cloud pages are available, and a band-creation mode telling the frontend how
the "Crear banda" action behaves: either direct (show the core creation form) or handed off to a
host-provided flow (do not show the direct form; send the user to the host's payment flow). The
values are user-scoped: they reflect the host policy's evaluation of the user (own subscription OR
membership in any active band) and do not vary per composition. The frontend MUST gate controls
from this response and MUST NOT hard-code plan names. How the policy or host announces the
hand-off mode and its target is left to design.
(Previously: no band-creation mode.)

#### Scenario: Unlimited entitlements

- GIVEN `UnlimitedPlanPolicy`
- WHEN the endpoint is called
- THEN sharing, band creation and history MUST be true, the demo limit null and the band-creation mode MUST be direct

#### Scenario: Hand-off mode

- GIVEN a host policy that denies direct creation and announces a host creation flow
- WHEN the endpoint is called
- THEN direct band creation MUST be false and the band-creation mode MUST be hand-off

#### Scenario: Entitlements are user-scoped

- GIVEN a policy that grants history to members of an active band
- WHEN a member of such a band calls the endpoint
- THEN history MUST be true for that user regardless of any composition

#### Scenario: Restricted entitlements

- GIVEN a policy denying sharing
- WHEN the endpoint is called
- THEN the sharing entitlement MUST be false

#### Scenario: Unauthenticated

- GIVEN no JWT
- WHEN the endpoint is called
- THEN the backend MUST respond 401

### Requirement: The core MUST accept external routers and keep a stable app entry

The core app MUST remain importable as `app.main.app` and MUST allow a host to add routers with
`include_router` and to install dependency overrides after import. The seam contract (getter name,
port methods, entitlements shape, entry point) MUST be documented in the repository.

#### Scenario: Host adds a router

- GIVEN a host importing `app.main.app`
- WHEN it includes an extra router
- THEN the new route MUST be served alongside the core routes

#### Scenario: Entry point stable

- GIVEN the existing `api/index.py`
- WHEN it imports the app
- THEN it MUST still resolve `app.main.app`

### Requirement: The frontend MUST expose an extension point for cloud pages

The core frontend MUST expose a minimal, tested extension point through which the private repo
registers extra routes and navigation entries (mechanism chosen in design). When no extension is
registered, no cloud route or entry MUST appear.

#### Scenario: No extension

- GIVEN the core frontend alone
- WHEN the shell renders
- THEN no plan or billing route or link MUST be present

#### Scenario: Extension registered

- GIVEN a host registering one route and one nav entry
- WHEN the shell renders
- THEN the entry MUST be visible and its route MUST resolve inside the same shell with shared auth state

### Requirement: The core band-creation action MUST adapt to the entitlements mode

The core "Crear banda" control MUST be driven by the band-creation mode. In direct mode it MUST
open the core creation form, which calls `POST /api/bands`. In hand-off mode it MUST NOT show the
direct form and MUST instead navigate the user to the host-registered payment entry (registered
through the frontend extension point). If hand-off mode is reported but no host entry is
registered, the control MUST NOT be actionable. The control and the direct form live in the core;
only the hand-off target lives in the host.

#### Scenario: Direct mode

- GIVEN entitlements report direct band creation
- WHEN the user activates "Crear banda"
- THEN the core creation form MUST open and submitting it MUST call `POST /api/bands`

#### Scenario: Hand-off mode

- GIVEN entitlements report hand-off with a registered host payment entry
- WHEN the user activates "Crear banda"
- THEN the user MUST be navigated to that host entry and the direct form MUST NOT be shown

#### Scenario: Hand-off without a registered entry

- GIVEN entitlements report hand-off but no host entry is registered
- WHEN the band screen renders
- THEN the create control MUST NOT be actionable and no direct form MUST be offered

### Requirement: Policy-gated behavior MUST degrade without data loss

When a policy denies an action, existing data MUST remain intact and readable according to role.

#### Scenario: Denied history keeps snapshots

- GIVEN history was previously available and is now denied
- WHEN the policy later allows it again
- THEN previously recorded snapshots MUST still be listed
