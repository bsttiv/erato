# Bands and Membership Specification

Repo: `erato`. Schema as approved: `bands` (name 1-80 chars, owner, members, timestamps),
`compositions.band_id` / `band_editable`, invitation `target`, indexes per D4/D3. Each entry of
`bands.members` has the shape `{user_id, role}` with `role` one of `owner` or `member`. A pending
ownership transfer is stored embedded in the band as `bands.pending_transfer` =
`{to_user_id, requested_by, requested_at, expires_at}`, or `null` when none (OD-1, approved
2026-10-04). Plan-dependent limits come from `PlanPolicy` (see `plan-policy-port`); under the default
policy there are no limits.

All band logic and all band UI (creation form, invitations, members, transfer, history of band
content) live in this public repo (OD-2, OD-3). `erato-cloud` only adds payment, billing and
subscription UI and orchestration; it never reimplements band logic.

## Purpose

Defines the band entity: lifecycle, membership, band-targeted invitations, the seat limit supplied
by the policy, leaving a band, ownership transfer with expiry, and sharing compositions with a band.

## Requirements

### Requirement: A user MAY create a band when the policy allows it

Creating a band through `POST /api/bands` MUST require an authenticated user and MUST consult
`PlanPolicy`'s band-creation gate. On success the band MUST have a required `name` of 1-80
characters, the creator as owner and as its first member (`{user_id, role: owner}`), a null
`pending_transfer`, and `created_at`/`updated_at`. When the gate denies, the backend MUST respond
403 with a machine-readable plan-gate code and create nothing. The creation endpoint, the creation
logic and the creation UI MUST live in the public `erato` core; they MUST NOT depend on any
subscription or billing concept.
(Previously: same gate, but no statement about where the logic and UI live or about the
first-member shape.)

#### Scenario: Create a band

- GIVEN an authenticated user and a policy allowing band creation
- WHEN they create a band named "Los Faroles"
- THEN the band MUST exist with that user as owner and sole member

#### Scenario: Invalid name

- GIVEN an empty name or a name longer than 80 characters
- WHEN the user creates a band
- THEN the backend MUST respond 422 and create nothing

#### Scenario: Creation denied by policy

- GIVEN a policy that denies band creation for the user
- WHEN they create a band
- THEN the backend MUST respond 403 with the plan-gate code

#### Scenario: Unlimited default

- GIVEN `UnlimitedPlanPolicy`
- WHEN any authenticated user creates a band
- THEN it MUST succeed

#### Scenario: Direct creation refused under a restrictive host policy

- GIVEN a host policy whose band-creation gate denies direct creation (as the cloud policy does)
- WHEN an authenticated user sends `POST /api/bands`
- THEN the backend MUST respond 403 with the band-creation plan-gate code and create nothing

### Requirement: The core MUST expose band creation and removal as a service operation for a host

The core band service MUST expose an operation to create a band for an explicit user and an
operation to delete a band by id, both invocable by a host application (such as `erato-cloud`)
without going through the HTTP band-creation gate. Creating through the service MUST yield the same
band shape as `POST /api/bands`. Deleting a band through the service MUST remove the band and MUST
detach any composition that references it (`band_id` null, `band_editable` false). This exists so a
host can create a band after its own payment confirmation and compensate if a later step fails. The
mechanism (service signature, module) is left to design.

#### Scenario: Host creates a band for a user

- GIVEN a host and a user id, with the HTTP gate denying direct creation
- WHEN the host invokes the creation service operation with a valid name
- THEN the band MUST exist with that user as owner and sole member and a null `pending_transfer`

#### Scenario: Host creation validates the name

- GIVEN a host invoking the creation operation with an empty name or a name over 80 characters
- WHEN the operation runs
- THEN it MUST fail with a validation error and create nothing

#### Scenario: Host removes a band as compensation

- GIVEN a band created through the service and a composition referencing it
- WHEN the host invokes the deletion operation for that band
- THEN the band MUST no longer exist
- AND the composition MUST have `band_id` null and `band_editable` false

#### Scenario: Deleting an unknown band

- GIVEN a band id that does not exist
- WHEN the host invokes the deletion operation
- THEN the operation MUST complete without error and change nothing (idempotent)

### Requirement: Band data MUST be visible only to members

Reading a band and its member list MUST be limited to its members; any other requester MUST receive
403 or 404 with no band data. Only the owner MUST be able to rename the band, create invitations,
remove members and start a transfer.

#### Scenario: Member reads band

- GIVEN a band member
- WHEN they request the band
- THEN the response MUST include name, owner and a resolved member projection

#### Scenario: Non-member

- GIVEN a user outside the band
- WHEN they request it
- THEN the backend MUST respond 403 or 404 with no band data

#### Scenario: Non-owner cannot manage

- GIVEN a non-owner member
- WHEN they create an invitation, remove a member or start a transfer
- THEN the backend MUST respond 403 and change nothing

### Requirement: Invitations MUST target a band and carry no role

A band invitation MUST be created by the owner and identified by a share link. It MUST NOT accept a
per-composition `role`. Redeeming it MUST make the user a band member with band role `member`
(stored as `{user_id, role: "member"}`). A band invitation link is multi-use (OD-6): redeeming it
MUST NOT consume it, and any number of different users MAY redeem the same link until it expires
(subject to the seat limit). Link expiry MUST reuse the existing invitations expiry (TTL)
behavior; this change introduces no new expiry value. Redeeming an expired invitation MUST be refused with 410. Pending
invitations created before the band model (keyed by composition) MUST NOT be redeemable.
(Previously: no statement about reuse or expiry of band invitation links.)

#### Scenario: Redeem

- GIVEN a valid band invitation link
- WHEN an authenticated user redeems it
- THEN they MUST become a band member with role `member`

#### Scenario: Role is not accepted

- GIVEN the owner creates a band invitation with `role: "editor"`
- WHEN the request is validated
- THEN the role MUST be rejected or ignored and the redeemed role MUST still be `member`

#### Scenario: Already a member

- GIVEN a user already in the band
- WHEN they redeem an invitation
- THEN membership MUST NOT be duplicated and the response MUST indicate they already belong

#### Scenario: Legacy invitation

- GIVEN an invitation without a band target
- WHEN a user redeems it
- THEN the backend MUST refuse with 404 or 410

#### Scenario: Link reused by several users

- GIVEN a valid, unexpired band invitation link and free seats
- WHEN user X redeems it and then user Y redeems the same link
- THEN both MUST become band members with role `member`

#### Scenario: Expired link

- GIVEN a band invitation past its expiry
- WHEN a user redeems it
- THEN the backend MUST respond 410 and the member list MUST be unchanged

### Requirement: Joining MUST honor the policy seat limit atomically

The join MUST be a single conditional update that succeeds only if the user is not already a member
and the member count is below the limit returned by `PlanPolicy`. When the policy returns no limit,
no size condition applies. When the band is full the backend MUST respond 409 with a code that
identifies a full band and MUST NOT add the member.

#### Scenario: Join with a free seat

- GIVEN a band with 7 members and limit 8
- WHEN a user redeems a valid invitation
- THEN they MUST be added

#### Scenario: Band full

- GIVEN a band with 8 members and limit 8
- WHEN a user redeems a valid invitation
- THEN the backend MUST respond 409 (band full) and the member list MUST be unchanged

#### Scenario: Concurrent joins at the last seat

- GIVEN a band with 7 members and limit 8
- WHEN two different users redeem concurrently
- THEN exactly one MUST be added and the other MUST receive 409

#### Scenario: No limit

- GIVEN a policy with no seat limit
- WHEN many users join
- THEN none MUST be rejected for size

### Requirement: Members MUST be able to leave, detaching their compositions

A non-owner member MAY leave. Leaving MUST remove them from the band and, for compositions they own
that belong to the band, set `band_id` to null, `band_editable` to false and empty `members`. The
owner MUST NOT be able to leave until ownership is transferred; the backend MUST respond 409.

#### Scenario: Member leaves

- GIVEN member M owns compositions shared with the band
- WHEN M leaves
- THEN M MUST no longer be a member
- AND each of M's band compositions MUST have `band_id` null, `band_editable` false and empty `members`

#### Scenario: Owner cannot leave

- GIVEN the band owner
- WHEN they try to leave
- THEN the backend MUST respond 409 and nothing MUST change

#### Scenario: Compositions of others stay

- GIVEN member M leaves
- WHEN other members' band compositions are inspected
- THEN they MUST be unchanged

### Requirement: Ownership transfer MUST be a request that expires after 14 days

The owner MAY request a transfer to another band member. The request MUST carry `expires_at` =
now + 14 days; the core owns this pending transfer and MUST store it embedded in the band as
`pending_transfer` = `{to_user_id, requested_by, requested_at, expires_at}` (null when none; no
separate collection). Expiry MUST be evaluated lazily on read and on accept (no scheduled job).
Nothing changes until the target accepts; an expired or rejected request MUST be removed (the field
reset to null). Only the target MUST be able to
accept. On accept the core MUST ask `PlanPolicy` to confirm the subscription step of the transfer;
only after the policy confirms MUST the core move ownership and swap the roles (the previous owner
becomes `member`, the target becomes `owner`) and remove the pending transfer. If the policy
refuses or fails, ownership and roles MUST remain unchanged. `UnlimitedPlanPolicy` confirms
immediately. Only one pending transfer per band MAY exist. An
expired request MUST NOT be acceptable.

#### Scenario: Request stores the embedded transfer

- GIVEN owner A and member B
- WHEN A requests a transfer to B
- THEN the band's `pending_transfer` MUST hold `to_user_id` B, `requested_by` A, `requested_at`
  and `expires_at` = `requested_at` + 14 days

#### Scenario: Request and accept

- GIVEN owner A and member B
- WHEN A requests a transfer to B and B accepts before expiry
- THEN the policy confirmation MUST have been requested once, B MUST be owner with role `owner`
  and A MUST have role `member`
- AND the pending transfer MUST be removed (`pending_transfer` null)

#### Scenario: Policy refuses the subscription step

- GIVEN a pending transfer to B and a policy that refuses the subscription step
- WHEN B accepts
- THEN A MUST remain owner, B MUST remain `member` and the pending transfer MUST remain until it expires or is rejected

#### Scenario: Rejection

- GIVEN a pending transfer to B
- WHEN B rejects it
- THEN the pending transfer MUST be removed and nothing else MUST change

#### Scenario: Expired request

- GIVEN a request older than 14 days
- WHEN B tries to accept
- THEN the backend MUST respond 410 (or 409) and the owner MUST be unchanged
- AND reading the band MUST NOT show the request as pending

#### Scenario: Target must be a member

- GIVEN a user outside the band
- WHEN A requests a transfer to them
- THEN the backend MUST respond 422 or 409 and create no request

#### Scenario: Wrong accepter

- GIVEN a pending transfer to B
- WHEN member C tries to accept
- THEN the backend MUST respond 403

#### Scenario: Cancel

- GIVEN a pending transfer
- WHEN the owner cancels it
- THEN no pending transfer MUST remain

#### Scenario: Second request while one is pending

- GIVEN a band with a non-expired pending transfer
- WHEN the owner requests another transfer
- THEN the backend MUST respond 409 and the existing `pending_transfer` MUST be unchanged

### Requirement: Compositions MUST be shareable with a band

The composition owner, who MUST be a member of the target band, MAY set `band_id` and
`band_editable`. Setting or changing the band association MUST NOT be allowed while the band is not
active per `PlanPolicy`. The owner MAY detach the composition at any time. A user MUST NOT attach a
composition to a band they do not belong to.

#### Scenario: Share with band

- GIVEN owner O in band G with an active band
- WHEN O sets `band_id = G` and `band_editable = true`
- THEN the composition MUST store both values

#### Scenario: Not a member

- GIVEN a user who is not in band G
- WHEN they set `band_id = G`
- THEN the backend MUST respond 403 or 404 and change nothing

#### Scenario: Detach

- GIVEN a composition shared with a band
- WHEN the owner sets `band_id` to null
- THEN `band_editable` MUST be false and band members MUST lose band-derived access

#### Scenario: Inactive band blocks new sharing

- GIVEN a band the policy reports as not active
- WHEN the owner tries to share another composition with it
- THEN the backend MUST respond 403 with the plan-gate code

### Requirement: The migration MUST be idempotent, safe by default and reversible

The migration script MUST be dry-run by default and print affected ids, MUST write a JSON backup of
every `members` array and every deleted invitation before mutating, MUST empty composition
`members`, MUST delete pending legacy invitations keyed by `composition_id`, MUST replace the
legacy composition-id invitation index with an index on the invitation target, and MUST be safe to
run twice. A restore script MUST re-apply the backup. In this change it MUST only be run against the
preview database.

#### Scenario: Dry run

- GIVEN legacy data
- WHEN the script runs without the apply flag
- THEN it MUST report affected ids and change no document

#### Scenario: Apply with backup

- GIVEN legacy data
- WHEN the script runs with the apply flag
- THEN a backup file MUST be written first, `members` MUST be empty and legacy invitations deleted

#### Scenario: Idempotent

- GIVEN the script was already applied
- WHEN it runs again
- THEN it MUST report nothing to do and change no data

#### Scenario: Restore

- GIVEN a backup from an apply run
- WHEN the restore script runs
- THEN the original `members` arrays and invitations MUST be restored

### Requirement: Role-derived access MUST be enforced on the backend for every band request

Every band endpoint and every band-derived composition access MUST be authorized on the backend. No
authorization MAY depend on client-supplied role or plan data.

#### Scenario: Direct request

- GIVEN a non-member sending a request directly to a band endpoint
- WHEN the backend processes it
- THEN it MUST respond 403 or 404 regardless of any client state
