# Plans and Subscriptions Specification

Repo: `erato-cloud` (private). The `subscriptions` collection, indexes and values are as approved in
D4; `erato-cloud` includes `erato` as a git submodule and extends it only through the documented
seams (`include_router`, `dependency_overrides`, the frontend extension point). Nothing in this
capability may be implemented in the public `erato` repo.

Boundary (OD-2, OD-3, approved 2026-10-04): `erato-cloud` extends the `erato` frontend ONLY for
payment, billing and subscription UI (checkout, plan management, seat purchase). All other UI
(bands, band creation form, invitations, members, history, entitlements-driven gating) lives in the
public `erato` repo, so a self-hosted `erato` never deals with payments. Band creation logic lives
in the `erato` core; `erato-cloud` only orchestrates payment around it.

## Purpose

Defines the plan catalogue, the subscription store, the policy that answers the core's questions,
the billing port with the free provider (preview only), the subscription lifecycle and the plan
page. The payment gateway is out of scope.

## Requirements

### Requirement: Three plans MUST exist with fixed entitlements

The catalogue MUST contain Gratis, Pro Individual and Pro Banda. Gratis: no sharing with people,
public read-only link allowed, no history, 1 demo per composition. Pro Individual: history, up to 20
demos per composition, no sharing with people, no bands. Pro Banda: everything Pro Individual has,
plus sharing with people, 8 seats including the owner plus `extra_seats`; contracting Pro Banda is
the only way to create a band (see the band creation flow requirement). Quotas MUST be constants of
the policy, not stored fields. A user with no active subscription of their own and no membership in
an active band is on Gratis.
(Previously: Pro Banda listed band creation as an entitlement checked at direct creation.)

#### Scenario: Default plan

- GIVEN a user with no subscription and no membership in an active band
- WHEN entitlements are resolved
- THEN sharing, direct band creation and history MUST be denied and the demo limit MUST be 1

#### Scenario: Pro Individual

- GIVEN an active Pro Individual subscription
- WHEN entitlements are resolved
- THEN history MUST be allowed, the demo limit MUST be 20, sharing with people and direct band creation MUST be denied

#### Scenario: Pro Banda

- GIVEN a user who is a member of a band with an active Pro Banda subscription
- WHEN entitlements are resolved for that user
- THEN history and sharing with people MUST be allowed and the demo limit MUST be 20

#### Scenario: Direct band creation is denied for everyone

- GIVEN a user on any plan, including an owner of an active Pro Banda band
- WHEN the direct band-creation gate is asked
- THEN it MUST be denied, and the entitlements MUST report the band-creation mode as hand-off to the payment flow

### Requirement: The subscriptions store MUST enforce one active subscription per subject

A Pro Individual subscription has subject type `user` (the user id); a Pro Banda subscription has
subject type `band` (the band id), never the owner user. The repository MUST store provider, provider subscription id (null for free), current period end
(null for free), status, `cancel_at_period_end`, `payer_id`, `extra_seats` and timestamps. A partial unique
index MUST prevent a subject having more than one subscription with status `active` and
`cancel_at_period_end` false. The index MUST be created by the cloud index bootstrap.

#### Scenario: Double activation

- GIVEN a subject with an active subscription
- WHEN a second active subscription is inserted for the same subject
- THEN the store MUST reject it

#### Scenario: Band subscription subject

- GIVEN a user activates Pro Banda for band G
- WHEN the subscription is stored
- THEN its subject MUST be type `band` with id G, not the user

#### Scenario: Canceled does not block

- GIVEN a subject whose subscription is canceled
- WHEN a new active subscription is created
- THEN it MUST succeed

#### Scenario: Bootstrap idempotent

- GIVEN the index bootstrap already ran
- WHEN it runs again against the same database
- THEN it MUST succeed without error or change

### Requirement: SubscriptionPlanPolicy MUST answer the core's questions from subscriptions

`SubscriptionPlanPolicy` MUST implement the port from the catalogue rules and the `subscriptions`
data, and MUST be installed with `app.dependency_overrides` in the cloud app. Seat limit MUST be
`8 + extra_seats` from the band's active subscription (subject type `band`, D2: not stored on the
band). A band with no
active subscription MUST be reported as not active (read-only). The direct band-creation gate
(`POST /api/bands`) MUST always be denied under this policy: a band is created only through the
band creation flow, which contracts Pro Banda for it.
(Previously: creating a band required activating Pro Banda in the same flow, implemented as a
cloud-side creation endpoint; creation now stays in the core.)

#### Scenario: Seat limit

- GIVEN a Pro Banda subscription with `extra_seats` 2
- WHEN the seat limit is asked
- THEN it MUST be 10

#### Scenario: Band without subscription

- GIVEN a band with no active subscription
- WHEN band-active is asked
- THEN it MUST be false

#### Scenario: Override installed

- GIVEN the cloud app
- WHEN `get_plan_policy` is resolved
- THEN it MUST return `SubscriptionPlanPolicy`

#### Scenario: Direct creation refused in the cloud app

- GIVEN the cloud app and an authenticated user
- WHEN they send `POST /api/bands` directly
- THEN the backend MUST respond 403 with the band-creation plan-gate code and create no band

### Requirement: A band MUST be created only through a payment flow that calls the core

Under `erato-cloud`, the "Crear banda" action in the core UI MUST lead to the cloud checkout (via
the hand-off mode of the entitlements). When the payment is confirmed (with the free provider: the
user confirms the one-click checkout while the provider is enabled), the cloud MUST, in this order:
(1) invoke the core band service to create the band for the paying user, (2) activate a Pro Banda
subscription whose subject is type `band` with that band's id and whose payer is the user. If step
(2) fails, the cloud MUST delete the band through the core service (compensation) so that neither a
band nor a subscription remains. If step (1) fails, no subscription MUST be created. When payment
is not confirmed or is refused, no band and no subscription MUST be created. No data-model change
is introduced by this flow.

#### Scenario: Successful creation

- GIVEN an authenticated user, the provider enabled and a valid band name
- WHEN they confirm the checkout
- THEN a band MUST exist with the user as owner and sole member
- AND an active Pro Banda subscription MUST exist with subject type `band`, that band's id and payer the user

#### Scenario: Subscription activation fails

- GIVEN the core band service created the band but the subscription activation fails
- WHEN the flow handles the failure
- THEN the band MUST be deleted through the core service
- AND no subscription MUST exist for it and the user MUST receive an error

#### Scenario: Band creation fails

- GIVEN the core band service refuses or fails to create the band (for example an invalid name)
- WHEN the flow handles the failure
- THEN no subscription MUST be created and no band MUST exist

#### Scenario: Payment not confirmed or provider unavailable

- GIVEN `FREE_PRO_ENABLED` unset, or the user abandons the checkout
- WHEN the flow ends
- THEN no band and no subscription MUST exist

#### Scenario: Unauthenticated

- GIVEN no JWT
- WHEN the checkout confirmation is requested
- THEN the backend MUST respond 401 and create nothing

### Requirement: Members of an active band MUST have Pro features across their whole account

While a user is a member of at least one band with an active subscription, the policy MUST grant
that user the Pro entitlements (individual and group: history, the Pro demo limit of 20, sharing
with people including attaching their compositions to a band and assigning per-member roles) across
their whole account, on every composition they can act on and not only on that band's compositions
(OD-4, revised 2026-10-04). Entitlements are user-scoped: the policy evaluates the user's own
subscription OR membership in any active band. The inheritance MUST end when the user leaves the
band or the band stops being active, unless the user has their own subscription or belongs to
another active band. Direct band creation stays denied (see the band creation flow requirement);
inheritance does not allow creating a band without payment.

#### Scenario: Free member of an active band

- GIVEN a Gratis user who is a member of a band with an active Pro Banda subscription
- WHEN entitlements are resolved for that user
- THEN history and sharing with people MUST be allowed and the demo limit MUST be 20

#### Scenario: Whole account, composition outside the band

- GIVEN the same user and a composition they own that is not shared with any band
- WHEN they request its history or upload demos beyond 1
- THEN the Pro entitlements MUST apply (history allowed, demo limit 20)

#### Scenario: Attach a composition to a band

- GIVEN the same user, a member of active band G, with a composition they own
- WHEN they share that composition with G
- THEN the attach MUST be allowed by their inherited entitlement

#### Scenario: Band becomes inactive

- GIVEN a Gratis member of a band whose subscription ends
- WHEN entitlements are resolved for that user
- THEN the Gratis entitlements MUST apply

#### Scenario: Left the band

- GIVEN a Gratis user who left an active Pro Banda band
- WHEN entitlements are resolved
- THEN no Pro entitlement MUST be granted by that band

#### Scenario: Own subscription or another active band keeps Pro

- GIVEN a user who leaves active band G but has their own Pro Individual subscription, or belongs to another active band H
- WHEN entitlements are resolved
- THEN Pro entitlements MUST remain from the own subscription or from H

#### Scenario: Inheritance does not allow direct creation

- GIVEN a Gratis member of an active Pro Banda band
- WHEN the direct band-creation gate is asked
- THEN it MUST be denied and the mode MUST be hand-off to the payment flow

### Requirement: Unpaid bands MUST be read-only for band-derived and invited roles

When a band is not active, band-derived and invited roles on compositions with that `band_id` MUST
NOT be able to write, and no invitation or member-role change MUST be allowed. The composition owner
MUST keep full edit of their own content and MAY detach it. This is enforced by the core's
`require()` from the policy answer.

#### Scenario: Member write blocked

- GIVEN an inactive band and a band member with editor-derived access
- WHEN they save a section of a band composition
- THEN the backend MUST respond 403 with the band-inactive code

#### Scenario: Owner still edits

- GIVEN the same inactive band
- WHEN the composition owner saves a section
- THEN it MUST succeed

#### Scenario: Reads still work

- GIVEN the inactive band
- WHEN a member views the composition
- THEN the view MUST succeed

#### Scenario: Reactivation

- GIVEN the band later gets an active subscription
- WHEN the member saves
- THEN the write MUST succeed

### Requirement: The billing port MUST isolate providers from policy and UI

A `BillingProvider` port MUST create, cancel and adjust seats of subscriptions. `FreeBillingProvider`
MUST create and cancel subscriptions with provider `free`, no external id and no period. The port
MUST support the `cancel_at_period_end` path so a gateway adapter can replace the free provider
without changing policy, permissions or API contracts.

#### Scenario: Free activation

- GIVEN the free provider is enabled
- WHEN a user activates Pro Individual
- THEN an active subscription with provider `free`, null provider id and null period end MUST exist

#### Scenario: Free cancel is immediate

- GIVEN an active free subscription
- WHEN it is canceled
- THEN it MUST no longer be active immediately

### Requirement: Free Pro MUST fail closed behind FREE_PRO_ENABLED

Activation MUST be refused unless `FREE_PRO_ENABLED` is explicitly true. When unset or false,
existing `provider: "free"` subscriptions MUST NOT be honored by the policy (kill switch). The free
provider MUST also refuse to run when `VERCEL_ENV=production`, even if the flag is true. Any
registered user MAY self-activate; no admin or allowlist.

#### Scenario: Flag unset

- GIVEN `FREE_PRO_ENABLED` is unset
- WHEN a user activates
- THEN the backend MUST refuse and create nothing

#### Scenario: Kill switch

- GIVEN an active free subscription and the flag turned off
- WHEN entitlements are resolved
- THEN the user MUST be treated as having no subscription

#### Scenario: Production guard

- GIVEN `FREE_PRO_ENABLED=true` and `VERCEL_ENV=production`
- WHEN a user activates
- THEN the backend MUST refuse

#### Scenario: Open to any user

- GIVEN the flag is true in preview
- WHEN any authenticated user activates
- THEN it MUST succeed with no allowlist check

#### Scenario: Unauthenticated

- GIVEN no JWT
- WHEN activation is requested
- THEN the backend MUST respond 401

### Requirement: Subscription lifecycle endpoints MUST be mounted by the cloud app

Activate, cancel and set-extra-seats endpoints MUST be added with `include_router`. Extra seats MUST
be bounded to 0-12 (20 seats total). Seat changes and cancellation of a band subscription MUST be
limited to the band owner (the payer of the band's currently effective subscription).
Lowering seats below the current member count MUST be refused.

#### Scenario: Seats bound

- GIVEN a Pro Banda owner
- WHEN they set `extra_seats` to 13
- THEN the backend MUST respond 422 and change nothing

#### Scenario: Seats below members

- GIVEN 10 members and `extra_seats` 2
- WHEN the owner sets `extra_seats` to 0
- THEN the backend MUST refuse

#### Scenario: Not the payer

- GIVEN a band member who is not the owner
- WHEN they cancel the band subscription
- THEN the backend MUST respond 403

### Requirement: Ownership transfer MUST move the band's subscription to the new owner as payer

Subscriptions carry a payer (`payer_id`). A Pro Banda subscription always has subject type `band`
(the band id); the payer is the user who pays for it. When the core asks the policy to confirm a
transfer, `SubscriptionPlanPolicy` MUST run the subscription step: the accepting member activates
Pro for the same band with the free provider (immediate, no payment method), creating a new
subscription whose subject is the band and whose payer is the new owner. When that activation
succeeds the step is confirmed, and the previous subscription MUST be marked
`cancel_at_period_end = true`: it is not renewed, and the band MUST stay active until the previous
paid period ends. The previous subscription MUST be flagged before the new one is inserted, so the
one-active-subscription-per-subject rule is never violated. If the previous subscription has no
period end (free provider), it is superseded immediately by the new one with no gap in activity.
If the band has no active subscription, the step MUST be confirmed without creating or changing any
subscription. If the activation fails or is refused (flag off, production guard), the step MUST be
refused, the transfer MUST NOT complete, the band owner MUST be unchanged and the previous
subscription MUST be untouched.

The seat limit MUST always be computed from the band's currently effective subscription, so it
stays continuous across the overlap: no member is removed and no join is wrongly refused because of
the transfer.

Out of scope: gateway-only details (first charge at the end of the paid period, webhooks, real
payment methods). They are deferred until the payment gateway exists.

#### Scenario: Happy path

- GIVEN a band with an active Pro Banda subscription paid by A, and member B with a pending transfer from A
- WHEN B accepts and activates Pro for the band with the free provider
- THEN a new active subscription with subject band and payer B MUST exist
- AND A's subscription MUST have `cancel_at_period_end = true`
- AND B MUST be owner and the band MUST remain active

#### Scenario: Request expires or is rejected

- GIVEN a pending transfer that expires or is rejected by B
- WHEN the outcome is evaluated
- THEN the pending transfer MUST be removed and no subscription MUST be created or changed
- AND A MUST remain owner

#### Scenario: Activation fails

- GIVEN `FREE_PRO_ENABLED` is unset (or the activation otherwise fails)
- WHEN B accepts the transfer
- THEN the transfer MUST NOT complete, A MUST remain owner and A's subscription MUST be unchanged

#### Scenario: Band with no active subscription

- GIVEN an inactive band (no active subscription) and a valid pending transfer
- WHEN B accepts
- THEN the transfer MUST complete with B as owner
- AND no subscription MUST be created or modified, and the band MUST remain inactive

#### Scenario: Seat limit during the overlap

- GIVEN A's previous subscription (`extra_seats` 2, flagged `cancel_at_period_end`, period not ended) and B's new subscription (`extra_seats` 0)
- WHEN the seat limit is computed
- THEN it MUST come from the currently effective subscription of the band
- AND the band MUST NOT lose seats or members merely because of the transfer

#### Scenario: Previous period ends

- GIVEN a previous subscription flagged `cancel_at_period_end` whose period has ended and a new active subscription
- WHEN band-active and the seat limit are resolved
- THEN they MUST come from the new subscription only

### Requirement: Sharing with people and demo quotas MUST be gated by plan

Users with no own Pro Banda subscription and no membership in an active band MUST NOT share with
people (members of an active band are entitled, per the inheritance requirement); the public
read-only link MUST work on every plan. Demo uploads beyond the effective limit MUST be refused.
(Previously: Free and Pro Individual could not share, with no band-membership exception.)

#### Scenario: Free cannot invite

- GIVEN a Gratis user
- WHEN they try to share a composition with a person
- THEN the backend MUST respond 403 with the sharing code

#### Scenario: Public link on Gratis

- GIVEN a Gratis user's public composition
- WHEN an anonymous visitor opens it
- THEN it MUST be viewable

#### Scenario: Demo limit

- GIVEN a Gratis composition with 1 demo
- WHEN the user requests an upload credential for a second
- THEN the backend MUST respond 403 with the demo-limit code

### Requirement: A plan page MUST allow activation, cancel and seats

The cloud frontend MUST add, through the core extension point, only payment, billing and
subscription UI: the plan page (current plan, activation of Pro Individual or Pro Banda, cancel, and
extra seats (0-12) when applicable) and the band checkout that the core "Crear banda" action hands
off to. It MUST NOT add band, invitation, member, history or entitlement-display screens, which
live in the core. Controls
MUST be hidden or disabled with an explanation when the provider is unavailable. Copy MUST be
Spanish, informal "tu" address, no exclamation marks or emoji, using design-system primitives.

#### Scenario: Activate

- GIVEN a Gratis user on the plan page with the provider enabled
- WHEN they choose Pro Individual
- THEN their plan MUST update and history MUST become available

#### Scenario: Provider unavailable

- GIVEN `FREE_PRO_ENABLED` unset
- WHEN the page renders
- THEN activation MUST NOT be offered and an explanation MUST be shown

#### Scenario: Entry point

- GIVEN the cloud app
- WHEN the shell renders for an authenticated user
- THEN a navigation entry to the plan page MUST be present

#### Scenario: Create band button leads to checkout

- GIVEN the cloud app and a user on the core band screen
- WHEN they activate "Crear banda"
- THEN they MUST land on the cloud band checkout and the core direct creation form MUST NOT be shown

#### Scenario: Cloud adds no non-payment UI

- GIVEN the cloud frontend registrations
- WHEN its routes and navigation entries are listed
- THEN every one MUST be a payment, billing or subscription page
