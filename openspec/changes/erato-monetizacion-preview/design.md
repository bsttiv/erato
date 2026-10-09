# Design: Erato monetization in Vercel Preview (landing, versioning, bands and plans, public footer)

Change: `erato-monetizacion-preview`. Repos: public `erato` (this repo) and private `erato-cloud`.
Inputs: `proposal.md`, the 11 specs under `specs/` (revised 2026-10-04), D1-D4, P1-P20, the Band/plans
model approval, the subscription-subject decision (Pro Banda subject = band) and the author decisions
of 2026-10-04 that resolve OD-1, OD-2, OD-3, OD-4 and OD-6 (see "Resolved decisions" at the end).

Revision note (2026-10-04): AD5, AD6, AD10, AD11 and AD12 were rewritten; AD18-AD20 are new; AD4,
the component breakdown, data flows, API contracts, testing, risks and open decisions were updated.
AD1-AD3, AD7-AD9 and AD13-AD17 are unchanged except where marked.

## Context

Grounding facts from the code (verified while writing this design):

- Backend: FastAPI app built at module level in `app/main.py`; `api/index.py` re-exports
  `app.main.app`. Layering is router -> service -> repository (`app/routers/*`, `app/services/*`,
  `app/db/repositories/*`), with a pure permission core (`app/core/permissions.py`: `Role`, `Action`,
  `can`, `resolve_role`) and request dependencies in `app/deps.py` (`composition_access` caches the
  composition on `request.state`; `require(action)` applies the 404-vs-403 rule).
- FastAPI caches a dependency's result per request by default (`use_cache=True`): every
  `Depends(get_plan_policy)` in one request (router, `require()`, sub-dependencies) receives the SAME
  object. AD19 relies on this for the request-scoped memo.
- Errors: `app/core/errors.py` `AppError` subclasses serialize as
  `{"error": <code>, "message", "detail", "details"?}`. The machine-readable code is the `error` field.
- Section writes: `PUT /api/compositions/{id}/{chords|tablature|lyrics|todos}` with the section model as
  the body (todos is a bare array), `CompositionsRepository.update_section` does an unconditional `$set`.
- Invitations: keyed by `composition_id`, `role` field, TTL index; redeem via
  `POST /api/auth/redeem-invite` -> `SharingService.redeem_invite` -> non-atomic `add_member`
  (`$pull` then `$push`). Expired redeem currently raises `UnauthorizedError` (401).
- Indexes: created by `scripts/ensure_indexes.py` (`REPOSITORIES` tuple), never at startup.
- Settings: `app/settings.py` (pydantic-settings); `app_base_url` currently defaults to
  `http://localhost:5173`.
- Frontend: Vue 3 + vue-router; `frontend/src/main.ts` creates the app with a module-level router
  singleton (`frontend/src/router/index.ts`, routes in `router/routes.ts` with English paths such as
  `/compositions/:id`, `/invite/:token`, catch-all last). There is no shared shell component: the top
  bar lives in `DashboardView.vue`. Auth token is in memory (`api/client.ts`), refreshed via the
  `/api/auth/refresh` cookie.
- Tests: backend `pytest` (`pytest.ini`: `pythonpath = .`, `asyncio_mode = auto`) against a real MongoDB
  at `localhost:27017` (`tests/conftest.py`), routers exercised with `httpx.AsyncClient(ASGITransport)`.
  Frontend `vitest run` (jsdom) and `vue-tsc`. `openspec/config.yaml` test command:
  `.venv/bin/pytest tests/ && cd frontend && npm run test:unit`. No test CI workflow exists in `erato`
  (only `.github/workflows/cla.yml`).
- `erato-cloud`: contains only `README.md` and the `erato` submodule pinned to `main`. No app code yet.
- MongoDB in local Docker and tests is a standalone server: multi-document transactions are NOT
  available, so every multi-step write in this design is ordered to be idempotent and safe to retry.

## Goals / Non-goals

Goals
- Implement every requirement of the 11 specs with the approved model (D1-D4, Band/plans model,
  subject = band, embedded `pending_transfer`) and no other schema.
- Keep the public core free of subscription, billing and quota logic; the core runs with
  `UnlimitedPlanPolicy` and every feature on, with no payment UI at all.
- Keep ALL band logic and UI in the core (creation form, `POST /api/bands`, invitations, members,
  transfer, history). `erato-cloud` adds only payment, billing and subscription UI and orchestration.
- Give `erato-cloud` stable, tested seams: `get_plan_policy`, `get_host_capabilities`, routers via
  `include_router`, the host-invocable `BandsService` operations, and a payment-only frontend
  extension point.
- Close the concurrency gaps: section overwrites (409), seat join race, `add_member` race.

Non-goals
- Payment gateway, webhooks, real charges.
- User-facing band deletion (only the host compensation operation of AD18 deletes bands).
- Real-time editing, mobile, R2, byte quotas.
- Production rollout, production migration, touching the root `vercel.json` or its test.
- CI for `erato` (none exists today; recommended in Risks, not required by the specs).

## Technical Approach

One hexagonal port (`PlanPolicy`) in the core, resolved per request through one FastAPI dependency
getter; every gate call site receives the policy through `Depends(get_plan_policy)` and passes it into
services as a constructor argument. Entitlement questions are user-scoped (the acting user only, no
composition or band context); band-scoped questions (seat limit, band active, transfer confirmation)
take the band id. Band context is resolved in `deps.py` and passed into a still-pure `resolve_role`.
Versioning uses a single conditional `find_one_and_update` with `ReturnDocument.BEFORE` so the
conflict check, revision bump and dedup comparison happen in one atomic operation.

Band creation lives in the core. Under the unlimited default `POST /api/bands` creates directly.
Under the cloud policy direct creation is always denied and the entitlements report the
`hand_off` band-creation mode; the core "Crear banda" control navigates to a payment entry the
cloud registered through the frontend extension point. The cloud checkout, once payment is confirmed,
calls the core `BandsService.create_for_user`, then activates Pro Banda for the band, and on failure
calls the core idempotent `BandsService.delete_band` as compensation.

`erato-cloud` consumes `erato` as a git submodule, adds `sys.path` entry `erato/`, imports
`app.main.app`, installs overrides and routers, and builds its own frontend entry from the core app
factory, registering only payment pages.

## Architecture Decisions

### AD1. `expected_rev` travels as a query parameter; responses carry `rev` (unchanged)

**Choice**: `PUT /api/compositions/{id}/{lyrics|chords|tablature}?expected_rev=<int>` (optional,
`ge=0`). The body stays exactly the current section model. Successful responses become the section
model plus `rev: int` (new response models `LyricsWriteResponse(LyricsSection)`,
`ChordsWriteResponse(ChordsSection)`, `TablatureWriteResponse(TablatureSection)`). Todos is untouched.
**Alternatives considered**:
- Body field (`{..section, expected_rev}` or a `{content, expected_rev}` wrapper): the field would leak
  into `model_dump()` and be stored with the content unless stripped; a wrapper breaks the current
  body contract for every client and test.
- `If-Match` header with an ETag: the HTTP-standard answer is 412, but the specs mandate 409 and a
  JSON conflict payload; custom headers also need CORS/Vercel care.
**Rationale**: additive, no body-shape change, FastAPI validates query and body before the handler so
"422 before conflict check" holds for free, and the todos bare-array contract is untouched.

### AD2. Conditional save with `ReturnDocument.BEFORE`, snapshot after, no baseline snapshot (unchanged)

**Choice**: `CompositionsRepository.update_versioned_section(oid, section, content, expected_rev)`:
filter `{_id, <rev clause>}` where the rev clause is `{"section_revs.<s>": expected_rev}` and, when
`expected_rev == 0`, `{"$or": [{"section_revs.<s>": 0}, {"section_revs.<s>": {"$exists": false}}]}`;
update `{$set: {<s>: content, updated_at}, $inc: {"section_revs.<s>": 1}}`; return the document BEFORE
the update. Without `expected_rev` the filter is `{_id}` only (last-write-wins, revision still bumps).
`new_rev = before.section_revs.<s> (default 0) + 1`. If `before.<s> != content` the service inserts a
snapshot `{composition_id, section, rev: new_rev, content, author_id, created_at}` and prunes
`rev <= new_rev - 50`; any exception there is logged and swallowed. On a `None` result the service
re-reads the composition: missing -> 404, present -> 409 `section_conflict`.
No baseline snapshot of pre-existing content is recorded.
**Alternatives considered**: read-then-write (race window); baseline snapshot of legacy content on the
first save (needs an author id that does not exist; would fabricate attribution); `ReturnDocument.AFTER`
plus a separate read for dedup (extra round trip, not atomic with the comparison).
**Rationale**: one atomic operation decides conflict, bump and dedup. The preview DB starts empty (P5)
so there is no legacy content to baseline; production promotion is out of scope (see Risks).

### AD3. Conflict payload and author resolution (unchanged)

**Choice**: `SectionConflictError(AppError)` with status 409, code `section_conflict`, whose `to_dict()`
adds top-level `section`, `current_rev`, `content`, `author` (`{id, display_name}` or `null`) and
`updated_at`. `author`/`updated_at` come from the newest snapshot with `rev <= current_rev` for that
section; when none exists, `author = null` and `updated_at = composition.updated_at`.
**Alternatives considered**: nesting under `details` (spec asks the body to contain the fields; top level
is simpler for the client); storing a per-section last-author field on `compositions` (schema change,
not approved).
**Rationale**: no schema change. Known gap: an identical-content save bumps the revision without a
snapshot, so the author shown is that of the last content change. Listed as OD-5 (optional).

### AD4. Error and status mapping (updated)

All refusals use the existing `AppError` envelope; the code is in `error`.

| Situation | Status | `error` code | Notes |
| --- | --- | --- | --- |
| Policy denies sharing with people (member roles, band attach) | 403 | `plan_gate_sharing` | `PlanGateError(ForbiddenError)`; detach is never gated |
| Policy denies direct band creation | 403 | `plan_gate_band_creation` | always under the cloud policy |
| Policy denies history | 403 | `plan_gate_history` | after authorization |
| Demo count limit reached | 403 | `plan_gate_demo_limit` | after authorization |
| Write/sharing change on an inactive band | 403 | `band_inactive` | owner content edits exempt |
| Stale `expected_rev` | 409 | `section_conflict` | AD3 payload |
| Band full on join | 409 | `band_full` | |
| Owner tries to leave | 409 | `owner_must_transfer` | |
| A non-expired transfer is already pending | 409 | `transfer_pending` | existing `pending_transfer` unchanged |
| Transfer target / role target not in the band | 409 | `not_a_band_member` | state-dependent, not schema |
| Policy refuses the subscription step of a transfer | 409 | `transfer_not_confirmed` | unless the host raised its own `AppError` (for example `billing_unavailable`), which propagates unchanged |
| Lowering seats below members (cloud) | 409 | `seats_below_members` | |
| Second active subscription (cloud) | 409 | `subscription_already_active` | unique index DuplicateKeyError mapped |
| Transfer expired on accept | 410 | `transfer_expired` | |
| No pending transfer on accept/cancel/reject | 404 | `transfer_not_found` | |
| Band invitation expired | 410 | `invitation_expired` | |
| Legacy invitation (no `target`) | 410 | `invitation_legacy` | after migration they are deleted -> 404 |
| Unknown invitation token | 404 | `not_found` | existing |
| Non-member reads a band | 404 | `not_found` | same anti-probing rule as compositions |
| Non-owner manages a band / wrong accepter or rejecter | 403 | `forbidden` | |
| Free Pro disabled or production guard (cloud) | 403 | `billing_unavailable` | checkout, activation, transfer step |
| Body/query schema invalid (name length, `extra_seats` 0-12, role value) | 422 | `validation_error` | existing handler; also raised by `BandsService.create_for_user` for an invalid name |

**Alternatives considered**: 409 for expired transfers (spec allowed 410 or 409); 401 for expired
invitations (current behavior in `InvitationsRepository.redeem_invitation`); 403 for a refused transfer
step (it is a state outcome, not a permission).
**Rationale**: 410 says "this existed and is no longer usable". 401 is wrong for expired invitations
because `api/client.ts` treats any 401 as an expired access token and triggers a refresh-and-replay.
409 is reserved for "valid request, current state forbids it"; 422 stays for schema validation. 403
with distinct codes keeps plan gates machine readable (spec `plan-policy-port`).

### AD5. The `PlanPolicy` port: async Protocol, user-scoped entitlements (rewritten, OD-4)

**Choice**: `app/core/plan_policy.py`:

```python
class PlanPolicy(Protocol):
    # User-scoped entitlement questions: the acting user only, no composition or band context.
    async def can_share_with_people(self, user_id: str) -> bool: ...
    async def can_create_band(self, user_id: str) -> bool: ...        # direct creation via POST /api/bands
    async def can_view_history(self, user_id: str) -> bool: ...
    async def demo_limit(self, user_id: str) -> Optional[int]: ...    # per-composition count, None = no quota
    # Band-scoped questions.
    async def seat_limit(self, band_id: str) -> Optional[int]: ...
    async def is_band_active(self, band_id: str) -> bool: ...
    # Transfer hook: called on accept BEFORE the core swaps owner and roles.
    async def confirm_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> bool: ...
    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None: ...

class UnlimitedPlanPolicy:  # True, True, True, None, None, True, True
```

`get_plan_policy() -> PlanPolicy` lives in `app/deps.py` and returns `UnlimitedPlanPolicy()`.
The user whose entitlements are asked is always the authenticated acting user of the request (the
uploader for demo limits, the requester for history, the composition owner acting in the sharing
modal). Under the cloud this is exact: an editor of someone else's composition is necessarily a member
of an active band (band-derived role) or the band is inactive and writes are blocked anyway, so the
acting user's entitlement and the composition owner's coincide in every reachable case.
`confirm_band_transfer` returns `True` to confirm; `False` (or raising an `AppError`) refuses, and the
core then leaves owner, roles and `pending_transfer` untouched.
**Alternatives considered**:
- Keep the composition parameter on history and demo limit (previous AD5): contradicts the revised
  spec ("the policy MUST receive the user and no composition or band context") and OD-4.
- Post-swap notification hook `on_band_transferred` (previous AD5): cannot refuse, so a failed
  subscription step would leave a new owner with no paying subscription; the revised spec requires
  confirm-before-swap.
- One `entitlements(user)` method returning a dataclass: smaller surface, but the spec fixes a closed
  set of questions and the contract test asserts them one by one.
- An ABC base class: Protocol needs no import-time inheritance from the cloud and is checked by tests.
**Rationale**: matches the closed set in the spec, keeps plan names out of the core, and makes the
user-scoped OD-4 rule the only shape the port can express.

### AD6. Policy injection, host capabilities and the entitlements endpoint (rewritten)

**Choice**:
- Every gated router declares `policy: PlanPolicy = Depends(get_plan_policy)` and passes it to the
  service constructor (`BandsService(policy=...)`, `VersioningService(policy=...)`,
  `DemoService(policy=...)`, `SharingService(policy=...)`). `require()` also depends on
  `get_plan_policy`. FastAPI's per-request dependency cache makes all of them share one instance.
- `get_host_capabilities() -> HostCapabilities(extensions_available=False)` in `app/deps.py` feeds the
  entitlements indicator; the cloud overrides it to `True`. No other host flag is added.
- Band-creation mode is derived, not announced by a new seam:
  `band_creation_mode = "direct" if await policy.can_create_band(user) else "hand_off"`.
  The hand-off TARGET is announced by the host on the frontend (the payment entry registered through
  AD12). If the mode is `hand_off` and no entry is registered, the frontend renders the control as not
  actionable (spec "Hand-off without a registered entry").
- Gate call sites (core):
  | Call site | Question |
  | --- | --- |
  | `POST /api/bands` (router -> `BandsService.create`) | `can_create_band(user)` |
  | `PATCH /api/compositions/{id}/band` with a non-null `band_id` | `can_share_with_people(user)` then `is_band_active(band_id)` |
  | `PUT /api/compositions/{id}/members/{uid}` | `can_share_with_people(user)` then `is_band_active` of the composition's band |
  | history list/get/restore | `can_view_history(user)` after `require(EDIT)` |
  | demo upload signature and confirm | `demo_limit(user)` after `require(EDIT)` |
  | band invite redeem | `is_band_active(band_id)`, `seat_limit(band_id)` |
  | transfer accept | `confirm_band_transfer(band_id, A, B)` |
  | `require(action)` for non-VIEW, non-owner on a band composition | `is_band_active(band_id)` |
  | `GET /api/me/entitlements` | all four user-scoped questions + host capabilities |
**Alternatives considered**: a `band_creation_mode()` port method or a `band_creation_handoff` host
flag (extra seam surface; the spec's closed question set excludes the former, and the latter carries
no information the frontend registration does not already carry); module-level policy singleton
(forbidden by spec); an env var in the core (the core would then know about the cloud).
**Rationale**: `app.dependency_overrides` replaces both getters with zero core edits; the mode is a
pure function of an existing gate, so a self-hosted install is always `direct` and the cloud is always
`hand_off` without any new contract.

### AD7. Band context and role resolution (unchanged)

**Choice**: `composition_access` stays a cached loader. A new dependency
`band_context(request, user, access_record) -> Optional[BandContext]` loads, only when `band_id` is set
and a user is present, the band with projection `{owner_id, members.user_id}` and returns
`BandContext(band_id, is_member)`. `resolve_role(user_id, access_record, band: Optional[BandContext] = None)`
stays pure:
1. owner -> `OWNER`;
2. composition `members` role -> honored when `band_id` is null (legacy behavior unchanged) or when
   `band.is_member` is true;
3. `band.is_member` and `band_editable` -> `EDITOR`; `band.is_member` -> `VIEWER`;
4. public -> `VIEWER`; else `None` (404).
`require(action)` then, for `action != VIEW`, role != `OWNER` and `band_id` set, calls
`policy.is_band_active(band_id)` and raises `band_inactive` when false.
`by-slug` and `GET /{id}` reuse the same path so `user_role` includes band roles.
**Alternatives considered**: mutating composition `members` when someone leaves or is removed from a
band (spec "compositions of others stay unchanged" forbids it); loading band context for every
composition (extra read on every request).
**Rationale**: honoring member roles only while the user is in the band makes leave/remove correct
without touching other members' compositions, and compositions without `band_id` resolve exactly as
before. Because rule 2 honors member roles when `band_id` is null, every path that nulls `band_id`
(leave, remove, detach, AD18 deletion) MUST also empty `members`.

### AD8. Atomic seat join and atomic `add_member` (unchanged)

**Choice**: `BandsRepository.add_member_if_seat(band_id, user_id, limit)`:
`update_one({_id, "members.user_id": {$ne: uid}, **({"$expr": {"$lt": [{"$size": "$members"}, limit]}} if limit is not None else {})}, {$push: {members: {user_id: uid, role: "member"}}, $set: {updated_at}})`.
`matched == 0` -> re-read: already a member -> `already_member`; else `band_full`. The limit comes from
`policy.seat_limit(band_id)` (D2). `CompositionsRepository.set_member_role` replaces the `$pull`+`$push`
pair: first `update_one({_id, "members.user_id": uid}, {$set: {"members.$.role": role}})`, and if
nothing matched `update_one({_id, "members.user_id": {$ne: uid}}, {$push: ...})`; both are
single-document atomic and the second cannot duplicate.
**Alternatives considered**: denormalized `seat_limit` (rejected by D2); count-then-push (race).
**Rationale**: closes the "concurrent joins at the last seat" race without transactions.

### AD9. Leave and remove are ordered for idempotency (updated: pending transfer cleanup)

**Choice**: leave = (1) refuse if owner (`owner_must_transfer`); (2) detach the leaver's own band
compositions: `update_many({owner_id: uid, band_id: band}, {$set: {band_id: null, band_editable: false, members: [], updated_at}})`;
(3) `$pull` the leaver from `bands.members` with filter `{_id, owner_id: {$ne: uid}}`, and in the same
update `$set pending_transfer: null` when `pending_transfer.to_user_id == uid` (done as a second
conditional `update_one` on `{_id, "pending_transfer.to_user_id": uid}`, idempotent). Owner removal of a
member runs the same steps 2-3 for the removed user. Detach by the composition owner
(`PATCH .../band` with `band_id: null`) also empties `members` and sets `band_editable: false`.
**Alternatives considered**: pull first, detach second (a failure between steps leaves band
compositions attached to a band the owner no longer belongs to); transactions (unavailable locally).
**Rationale**: if step 3 fails, retrying `leave` is harmless; clearing a transfer aimed at a departed
member keeps "only a member can be the target" true without relying on lazy checks alone.

### AD10. Ownership transfer: embedded `pending_transfer`, confirm-before-swap (rewritten; storage UNBLOCKED by OD-1)

**Choice**: storage is `bands.pending_transfer: {to_user_id, requested_by, requested_at, expires_at} | null`
(approved 2026-10-04), with `bands.members` entries `{user_id, role: "owner" | "member"}`. New bands are
created with `pending_transfer: null`.
- **Request** (`POST /api/bands/{id}/transfer {to_user_id}`, owner): one conditional update
  `{_id, owner_id: A, "members.user_id": B, $or: [{pending_transfer: null}, {"pending_transfer.expires_at": {$lte: now}}]}`
  -> `$set pending_transfer: {to_user_id: B, requested_by: A, requested_at: now, expires_at: now + 14 d}`.
  No match -> re-read to classify: B not a member -> 409 `not_a_band_member`; non-expired pending ->
  409 `transfer_pending` (existing value unchanged). A transfer to the owner themself is refused by
  the service before the update with 422 `validation_error`.
- **Cancel** (owner) and **reject** (target): `DELETE /api/bands/{id}/transfer` sets
  `pending_transfer: null` with filter `{_id, pending_transfer: {$ne: null}, $or: [{owner_id: uid}, {"pending_transfer.to_user_id": uid}]}`.
  Expired or absent -> 404 `transfer_not_found`; caller neither owner nor target -> 403.
- **Accept** (`POST /api/bands/{id}/transfer/accept`, target B):
  1. Read the band; validate `pending_transfer.to_user_id == B`, `expires_at > now`, B still a member.
     Expired -> lazily clear it (`$set null` conditional on the same `expires_at`) and 410
     `transfer_expired`; absent -> 404; other target -> 403.
  2. `confirmed = await policy.confirm_band_transfer(band_id, A, B)`. `False` -> 409
     `transfer_not_confirmed`; an `AppError` raised by the policy propagates. Nothing is written.
  3. One conditional update `{_id, owner_id: A, "pending_transfer.to_user_id": B, "pending_transfer.expires_at": {$gt: now}}`
     -> `$set owner_id: B, "members.$[old].role": "member", "members.$[new].role": "owner", pending_transfer: null, updated_at`
     with `arrayFilters [{"old.user_id": A}, {"new.user_id": B}]`.
  4. If step 3 matches nothing (the owner canceled in the window between 1 and 3), the core logs a
     `transfer_swap_lost` warning and calls `abort_band_transfer(band_id, A, B)` once so the host
     can compensate its subscription step. Exceptions are logged as `transfer_abort_failed` and
     do not change the 404 `transfer_not_found` response. A process that dies between confirm
     and swap is not compensated; see Risks.
- **Lazy expiry on read**: `GET /api/bands/{id}` reports an expired request as `pending_transfer: null`
  without writing (the next request/accept overwrites or clears it).
**Alternatives considered**: separate `band_transfers` collection (rejected by OD-1); swap first and
notify the policy after (cannot honor "refusal leaves owner unchanged"); a lock field to make
confirm + swap atomic (schema change, not approved).
**Rationale**: embedded storage makes "one pending per band" structural and the swap a single
atomic update; asking the policy before writing is the only order that satisfies the refusal rule
without transactions.

### AD11. Band creation lives in the core; the cloud wraps it in a checkout (rewritten, OD-3 option 1)

**Choice**:
- Core: `POST /api/bands {name}` -> `BandsService.create(user, name)` -> `policy.can_create_band(user)`
  (403 `plan_gate_band_creation` when false) -> `BandsService.create_for_user(user_id, name)` (AD18).
  Under `UnlimitedPlanPolicy` every authenticated user creates directly; any number of bands.
- Cloud: `SubscriptionPlanPolicy.can_create_band` always returns `False`, so the entitlements report
  `band_creation_mode: "hand_off"` and `POST /api/bands` answers 403 for everyone, including owners of
  active bands and inherited-Pro members (OD-4 does not unlock creation).
- Cloud checkout: `POST /api/plan/checkout/band {name}` (authenticated):
  1. Validate the name with the core `BandCreate` schema (422 before any payment step).
  2. `provider.checkout_band(user)` -> `CheckoutResult(status="confirmed")` for the free provider when
     `FREE_PRO_ENABLED` is true and `VERCEL_ENV != "production"`; otherwise 403
     `billing_unavailable` and nothing is created. The free provider's one-click confirmation counts
     as payment confirmed in preview (accepted spec assumption).
  3. `band = await BandsService(policy=<request policy>).create_for_user(user_id, name)`. Failure ->
     re-raise; no subscription exists.
  4. `subscription = await provider.activate(subject={type: "band", id: band.id}, payer_id=user_id, extra_seats=0)`.
  5. Activation failure -> `await BandsService(...).delete_band(band.id)` (AD18, idempotent), then
     re-raise the activation error. A failure of the compensation itself is logged with the band id
     (the band stays inactive, i.e. read-only, and is visible to its owner; see Risks).
  6. 201 `{band, subscription}`.
- Each new band requires its own checkout and its own Pro Banda subscription (author decision,
  multiple bands per owner). The old `POST /api/plan/bands {name}` contract is removed.
- The gateway later replaces step 2 with a pending checkout (`status="pending", redirect_url`) whose
  confirmation (webhook) runs steps 3-6; persisting the requested name across that redirect is a
  gateway concern and out of scope (Open decisions, G-1).
**Alternatives considered**:
- Creation endpoint in the cloud with an allow-all policy instance (previous AD11): duplicated the
  core creation path in the private repo, contradicting OD-3.
- Cloud `can_create_band = provider available` and create through the core endpoint: creates bands
  before payment (inactive bands), which P11 rejected.
- A core "on band created" hook on the port: widens the closed question set.
**Rationale**: one creation implementation (core) used by both the HTTP gate and the host; the cloud
only orders payment, creation, activation and compensation.

### AD12. Frontend extension point: build-time app factory restricted to payment pages (rewritten, OD-2)

**Choice**: new `frontend/src/app.ts`:

```ts
export const EXTENSION_ROUTE_PREFIX = '/plan'

export interface PaymentNavItem { label: string; to: RouteLocationRaw }
export interface PaymentExtension {
  /** Payment, billing and subscription pages only. Every path MUST start with EXTENSION_ROUTE_PREFIX. */
  routes: RouteRecordRaw[]
  /** Nav entries rendered in the top bar for authenticated users only. */
  navItems?: PaymentNavItem[]
  /** Target of the core "Crear banda" control in hand_off mode. Must resolve to one of `routes`. */
  bandCreationEntry?: RouteLocationRaw
}
export interface EratoAppOptions { payments?: PaymentExtension }

export function createEratoRouter(payments?: PaymentExtension): Router  // inserts before catch-all
export function createEratoApp(options?: EratoAppOptions): App          // provides PAYMENT_EXTENSION_KEY
```

- The factory throws at startup when a route path does not start with `/plan`, when a route has no
  `meta.requiresAuth`, or when `bandCreationEntry` does not resolve to a registered extension route.
  This makes "the extension point exists only for payment pages" a mechanical guard; the cloud keeps
  its own test that every registration is a payment page.
- `main.ts` becomes `ensureAuthReady(); createEratoApp().mount('#app')` (no payments: self-hosted
  has no payment UI at all). `router/index.ts` keeps exporting `scrollBehavior`,
  `setupNavigationGuard` and `routes`; the default singleton export is kept for existing imports but
  built by `createEratoRouter()`.
- `shared/AppNavExtras.vue` renders injected nav items (authenticated only) in the dashboard and band
  screen top bars using existing `er-btn` classes.
- `features/bands/useBandCreation.ts` combines `useEntitlements().band_creation_mode` with the injected
  `bandCreationEntry`: `direct` -> open the core form; `hand_off` + entry -> `router.push(entry)`;
  `hand_off` without entry -> control rendered disabled with an explanation, no form.
- `erato-cloud/web/` has its own `vite.config.ts` (aliases `@` -> `../erato/frontend/src`,
  `@design-system` -> `../erato/erato-design-system`, `resolve.dedupe: ['vue', 'vue-router']`), its own
  `index.html` and `src/main.ts` calling
  `createEratoApp({ payments: { routes: [planRoute, bandCheckoutRoute], navItems: [planNav], bandCreationEntry: { name: 'band-checkout' } } })`.
**Alternatives considered**:
- Generic `{ extraRoutes, navItems }` (previous AD12): admits any page, contradicting OD-2.
- A2. Alias-swapped extension module: smaller core diff, but an implicit contract and a copied Vite
  config.
- B. Separate cloud SPA under `/plan/*` via rewrites: violates "resolve inside the same shell with
  shared auth state" (the in-memory token is lost on full-page navigation).
**Rationale**: one SPA, one router and auth state, typed and unit-testable seam, and a structural
boundary that keeps band, invitation, member and history UI in the core. Cost: FX refactor of
`main.ts`/router (about 200 lines with tests) and a cloud build coupled to core source paths.

### AD13. Cloud backend composition (updated wiring)

**Choice**: `erato-cloud/api/index.py` inserts `<repo>/erato` at the front of `sys.path`, imports
`app.main.app`, then `erato_cloud.wiring.install(app)`, which sets
`app.dependency_overrides[get_plan_policy] = get_subscription_plan_policy`,
`app.dependency_overrides[get_host_capabilities] = lambda: HostCapabilities(extensions_available=True)`
and `app.include_router(plan_router)`. The cloud package is named `erato_cloud` (never `app`), and
all core imports use `app.*` so override keys are the same function objects. `pytest.ini` uses
`pythonpath = . erato`. The checkout router imports `app.services.bands_service.BandsService` and
`app.schemas.bands.BandCreate` directly (documented in `docs/seams.md`).
**Alternatives considered**: packaging the core (`pyproject.toml`) - out of scope per proposal;
importing the core as `erato.app.*` (creates a second module object; overrides would silently miss).
**Rationale**: zero core edits beyond the seams; one module identity.

### AD14. Migration and index changes (unchanged)

**Choice**: `scripts/migrate_bands.py` (core):
- Default dry-run; `--apply` additionally requires `--confirm-db <name>` equal to `MONGODB_DB`.
- Legacy selection (idempotent by construction): compositions with `band_id` null/absent and non-empty
  `members`; invitations with `composition_id` present and `target` absent.
- Before mutating, writes `backups/migrate_bands-<UTC timestamp>.json` (bson `json_util` canonical
  extended JSON: `{compositions: [{_id, members}], invitations: [<full docs>]}`), flushed and fsynced;
  aborts if the write fails.
- Applies: `$set members: []` per backed-up id; `delete_many` by backed-up invitation ids; drops
  `idx_invitations_composition_id` if present; creates `idx_invitations_target`.
- Second run finds nothing and prints "nada que migrar"; exit 0.
`scripts/restore_bands_migration.py --backup <file> --confirm-db <name>`: `$set members` per id;
`insert_one` invitations by original `_id` ignoring `DuplicateKeyError`; recreates the legacy index.
`scripts/ensure_indexes.py` gains `BandsRepository` and `SectionRevisionsRepository` in
`REPOSITORIES`, `idx_compositions_band_id` in `CompositionsRepository.ensure_indexes`,
`idx_invitations_target` replacing `idx_invitations_composition_id` in
`InvitationsRepository.ensure_indexes`, and a `--rollback` flag driven by a `ROLLBACK_INDEXES` mapping
(names added by this change only). `pending_transfer` needs no index (read by `_id`).
**Alternatives considered**: running the migration at startup (serverless cold starts; prohibited by
the existing convention); selecting by a migration marker field (schema change).
**Rationale**: selection by shape is both the idempotency guard and the safety net, without new fields.

### AD15. Demo quota is checked at credential issue and enforced atomically at confirm (updated signature)

**Choice**: `POST .../demos/upload-signature` (after `require(EDIT)`): `limit = policy.demo_limit(user)`;
if `limit is not None and len(demos) >= limit` -> 403 `plan_gate_demo_limit`. `confirm_demo` pushes
with filter `{_id, f"demos.{limit-1}": {"$exists": False}}` when a limit exists; no match -> the same
403 (the orphaned Cloudinary asset is removed by the existing orphan sweep). The limit is a count per
composition evaluated for the acting user (AD5).
**Alternatives considered**: credential check only (two parallel uploads exceed the quota).
**Rationale**: spec requires the credential check; the confirm guard makes the quota exact at no cost.

### AD16. `APP_BASE_URL` fails closed (unchanged)

**Choice**: `app_base_url: Optional[str] = None`; a helper `build_app_url(path)` raises
`ConfigurationError` (500, code `config_missing`, message naming `APP_BASE_URL`) when unset. Never
derived from the request host. `docker-compose.yml` already sets it; `tests/conftest.py` sets it.
**Rationale**: spec `backend-platform` "Link base missing"; P7 rejects host-derived URLs.

### AD17. Noindex without touching the root `vercel.json` (unchanged)

**Choice**: the landing and the cloud web Vite configs inject `<meta name="robots" content="noindex">`
through a `transformIndexHtml` plugin when `process.env.VERCEL_ENV !== 'production'` (Vercel exposes
it at build time). The cloud project additionally sets `X-Robots-Tag: noindex` on API responses via
a small middleware enabled when `VERCEL_ENV == "preview"`.
**Rationale**: spec requires `noindex` on preview; root `vercel.json` and its test must not change.

### AD18. Host-invocable band service operations (new)

**Choice**: `app/services/bands_service.py` exposes, besides the HTTP-facing methods:

```python
class BandsService:
    def __init__(self, policy: PlanPolicy, db: Optional[AsyncIOMotorDatabase] = None): ...
    async def create(self, user: Mapping[str, Any], name: str) -> BandDocument:           # HTTP path: gate + create_for_user
    async def create_for_user(self, user_id: str, name: str) -> BandDocument:             # host path: NO gate
    async def delete_band(self, band_id: str) -> None:                                    # host compensation, idempotent
```

- `create_for_user` validates the name through `BandCreate` (1-80 chars after strip) and raises the
  existing 422 `validation_error` on failure; it inserts
  `{name, owner_id, members: [{user_id, role: "owner"}], pending_transfer: null, created_at, updated_at}`.
- `delete_band` order (idempotent, no transaction needed): (1) detach every composition with that
  `band_id`: `$set band_id: null, band_editable: false, members: [], updated_at` (members are emptied
  because AD7 honors member roles on band-less compositions); (2) delete band-targeted invitations;
  (3) `delete_one({_id})`. Unknown or malformed id -> returns without error.
- `delete_band` is not exposed over HTTP in this change (user-facing band deletion is a non-goal).
**Alternatives considered**: the cloud building an allow-all policy and calling `create` (previous
AD11; couples the cloud to policy internals and bypasses the gate by trickery); exposing an internal
HTTP endpoint (needs auth between apps in the same process for no gain); deleting only the band doc
(spec requires detachment; stale invitations would 404 later but could confuse redeem).
**Rationale**: an explicit, documented, gate-free host API keeps one creation implementation and makes
the compensation safe to retry.

### AD19. Cloud entitlement resolution: own subscription OR any active band, memoized per request (new, OD-4)

**Choice**: `SubscriptionPlanPolicy` is constructed per request by `get_subscription_plan_policy()` (a
FastAPI dependency, so the per-request cache shares it across the router, services and `require()`).
It memoizes in instance dicts:
- `_tier(user_id) -> Tier` (`gratis` | `pro`; band creation is always denied, so no band-plan tier is
  needed). Resolution, at most three queries:
  1. `subscriptions.find_one({"subject.type": "user", "subject.id": uid, **EFFECTIVE})` - Pro
     Individual. Hit -> `pro`.
  2. `band_ids = bands.distinct("_id", {"members.user_id": uid})` (uses `idx_bands_members_user_id`);
     if non-empty, `subscriptions.find_one({"subject.type": "band", "subject.id": {$in: band_ids}, **EFFECTIVE}, {_id: 1})`
     (uses `idx_subscriptions_subject`). Hit -> `pro`. Else `gratis`.
- `_band_effective(band_id) -> list[Subscription]` for `is_band_active` and `seat_limit`.
- `EFFECTIVE = {status: "active", $or: [{cancel_at_period_end: false}, {current_period_end: {$gt: now}}]}`
  plus, when `FREE_PRO_ENABLED` is not true, `provider: {$ne: "free"}` (P14 kill switch, which also
  removes inheritance from free band subscriptions).
- Answers: `can_share_with_people`, `can_view_history` = tier is `pro`; `demo_limit` = 20 for `pro`,
  1 for `gratis`; `can_create_band` = `False` always; `is_band_active` = effective list non-empty;
  `seat_limit` = `8 + max(extra_seats)` over the effective list (see AD20), `None` never returned for an
  existing band (an inactive band answers 8 so joins are bounded, though redeem refuses inactive bands
  first).
- No cross-request cache (serverless instances, and leaving a band or canceling must take effect on
  the next request).
**Alternatives considered**: denormalizing a `users.plan` field (schema change, two sources of truth);
a process-level TTL cache (stale entitlements after leave/cancel, inconsistent across serverless
instances); a single aggregation with `$lookup` from `bands` to `subscriptions` (one round trip but
harder to test and to index-verify on M0).
**Rationale**: worst case three small indexed reads per request that asks an entitlement question
(own sub, band ids, band subs), once per request thanks to the memo; most requests ask at most one
question. The rule matches OD-4 literally: user-scoped, account-wide, ending on leave or inactivity.

### AD20. Cloud subscription step of a transfer and the effective subscription (new)

**Choice**: `SubscriptionPlanPolicy.confirm_band_transfer(band_id, A, B)`:
1. `effective = _band_effective(band_id)`. Empty -> return `True` (no subscription created or changed;
   the band stays inactive).
2. Provider unavailable (flag off or production guard) -> raise `billing_unavailable` (refusal; nothing
   changed).
3. Let `prev` be the effective subscription with `cancel_at_period_end: false`. Flag it first:
   - `current_period_end` not null (gateway) -> `$set cancel_at_period_end: true`;
   - null (free provider) -> `$set status: "canceled", canceled_at` (superseded immediately, P12).
   This frees the partial unique index slot before the insert.
4. Insert the new subscription via `provider.activate(subject={type: "band", id: band_id}, payer_id=B, extra_seats=prev.extra_seats)`.
   Copying `extra_seats` keeps the seat count continuous, including the free-provider case where
   `prev` stops being effective immediately.
5. Insert failure -> revert step 3 on `prev` (conditional on the values just written), then return
   `False`.
`seat_limit` uses `8 + max(extra_seats)` over all effective subscriptions, so during a gateway overlap
the band never loses seats; once `prev.current_period_end` passes, only the new one remains.
**Alternatives considered**: transfer leaves the subscription untouched (previous design; contradicts
the revised spec, which moves the payer); insert first then flag (violates the partial unique index);
new subscription with `extra_seats: 0` (drops seats with the free provider, violating "no join wrongly
refused because of the transfer").
**Rationale**: satisfies every transfer scenario in `plans-and-subscriptions` without transactions;
the only non-atomic window (step 3 -> 4) is compensated in step 5.

## Component Breakdown

### Public `erato` - backend

| File | Action | Description |
| --- | --- | --- |
| `app/core/plan_policy.py` | Create | `PlanPolicy` Protocol (AD5), `UnlimitedPlanPolicy`, `HostCapabilities` |
| `app/core/errors.py` | Modify | `PlanGateError(code)`, `SectionConflictError`, `ConfigurationError`, `GoneError(410)` |
| `app/core/permissions.py` | Modify | `BandContext`; `resolve_role(..., band=None)` order per AD7 |
| `app/deps.py` | Modify | `get_plan_policy`, `get_host_capabilities`, `band_context`, band-inactive check in `require()` |
| `app/db/repositories/bands.py` | Create | insert, get, list by member, rename, `add_member_if_seat`, `remove_member`, `request_transfer`, `clear_transfer`, `swap_owner`, `delete`; indexes `idx_bands_owner_id`, `idx_bands_members_user_id` |
| `app/db/repositories/section_revisions.py` | Create | insert, prune, list page, get by rev, newest-at-or-below, delete by composition; index `uq_section_revisions_comp_section_rev` |
| `app/db/repositories/compositions.py` | Modify | `update_versioned_section`, `set_member_role`, `set_band`, `detach_owner_band_compositions`, `detach_all_band_compositions`, `list_by_user(user_id, band_ids)`, `add_demo_if_below(limit)`, `idx_compositions_band_id` |
| `app/db/repositories/invitations.py` | Modify | `target` support, `create_band_invitation`, `list_by_band`, `delete_by_band`; multi-use redeem (no `used_at` for band targets); index swap per AD14; expired -> 410 |
| `app/services/versioning_service.py` | Create | save with conflict, snapshot + prune + swallow, history list/get/restore with gate |
| `app/services/bands_service.py` | Create | `create`, `create_for_user`, `delete_band` (AD18), read (member-only), rename, invites, redeem/join, remove, leave, transfer request/cancel/reject/accept (AD10) |
| `app/services/sharing_service.py` | Modify | band attach/detach (`PATCH .../band`, attach gated per AD6), member roles restricted to band members, band-active gate; composition invitation creation removed |
| `app/services/composition_service.py` | Modify | cascade delete of `section_revisions`; `list_for_user` with band ids |
| `app/services/demo_service.py` | Modify | demo limit at credential and confirm (AD15) |
| `app/routers/sections.py` | Modify | `expected_rev` query, write responses with `rev` |
| `app/routers/history.py` | Create | history list/get/restore |
| `app/routers/bands.py` | Create | band endpoints |
| `app/routers/entitlements.py` | Create | `GET /api/me/entitlements` incl. `band_creation_mode` |
| `app/routers/sharing.py` | Modify | remove `/invites` endpoints, add `/band`, `/members/{user_id}` PUT/DELETE |
| `app/routers/auth.py` | Modify | `redeem-invite` returns band join result |
| `app/routers/compositions.py` | Modify | response adds `section_revs`, `band_id`, `band_editable`, `band_active`; list adds `band_id`, `via_band` |
| `app/schemas/compositions.py`, `app/schemas/bands.py`, `app/schemas/history.py`, `app/schemas/entitlements.py` | Modify/Create | request/response models; `BandCreate` reused by the cloud checkout |
| `app/settings.py` | Modify | `app_base_url` optional (AD16) |
| `app/main.py` | Modify | include `bands`, `history`, `entitlements` routers; no other change |
| `scripts/ensure_indexes.py` | Modify | new repositories, `--rollback` |
| `scripts/migrate_bands.py`, `scripts/restore_bands_migration.py` | Create | AD14 |
| `docs/seams.md` | Create | seam contract: getters, port methods, entitlements shape, `BandsService.create_for_user`/`delete_band`, `createEratoApp` payments option, entry point |
| `docs/runbook-preview.md` | Create | core part of the runbook (landing project, index bootstrap, migration on preview only) |
| `.env.example` | Create/Modify | every setting, owning repo noted, no values |

### Public `erato` - frontend and landing

| File | Action | Description |
| --- | --- | --- |
| `frontend/src/app.ts` | Create | `createEratoApp`, `createEratoRouter`, `PAYMENT_EXTENSION_KEY`, prefix guard (AD12) |
| `frontend/src/main.ts`, `frontend/src/router/index.ts` | Modify | use the factory |
| `frontend/src/shared/AppNavExtras.vue` | Create | renders injected payment nav items |
| `frontend/src/api/entitlements.ts`, `frontend/src/features/plan/useEntitlements.ts` | Create | cached entitlements, refreshed on login/logout, band join/leave and after returning from a payment page |
| `frontend/src/features/bands/useBandCreation.ts` | Create | mode + injected entry -> form / navigate / disabled |
| `frontend/src/api/bands.ts`, `frontend/src/api/history.ts` | Create | API clients |
| `frontend/src/api/compositions.ts`, `frontend/src/api/sharing.ts` | Modify | `expected_rev`, `rev`, band sharing, member roles; typed error with `error` code |
| `frontend/src/features/compositions/useSectionSave.ts` | Create | dirty tracking, `Promise.allSettled`, rev updates, conflict queue |
| `frontend/src/features/compositions/SectionConflictDialog.vue` | Create | `AppModal`-based; "Cargar la versión guardada" / "Sobrescribir con la mía" |
| `frontend/src/features/compositions/SectionHistoryPanel.vue` | Create | list, preview, restore; hidden/notice when not entitled |
| `frontend/src/features/compositions/ReadOnlyBanner.vue` | Create | inactive band banner |
| `frontend/src/features/compositions/SavedInEratoFooter.vue` | Create | anonymous public footer |
| `frontend/src/features/compositions/CompositionDetailView.vue` | Modify | replace `saveAll()` with `useSectionSave`; host dialog, panel, banner, footer |
| `frontend/src/features/compositions/DashboardView.vue` | Modify | band link, nav extras, band-derived marker |
| `frontend/src/features/bands/BandView.vue`, `BandCreateForm.vue` (+ small subcomponents) | Create | band management and the core creation form (direct mode) |
| `frontend/src/features/sharing/SharingModal.vue`, `InviteAcceptView.vue` | Modify | band control separate from visibility; member roles for band members; redeem -> band |
| `frontend/src/router/routes.ts` | Modify | `/bands`, `/bands/:id` (auth required) |
| `landing/**` | Create | Vue 3 + Vite + TS + Vitest; `useSlideNav.ts`; one component per slide; `landing/vercel.json`; aliases `@ds-vue` -> `../frontend/src/design-system`, `@design-system` -> `../erato-design-system`; `server.fs.allow: ['..']` |

### Private `erato-cloud`

| File | Action | Description |
| --- | --- | --- |
| `.gitmodules` | Modify | `erato` over HTTPS, `branch = preview` |
| `api/index.py` | Create | AD13 entry |
| `erato_cloud/settings.py` | Create | `CloudSettings`: `free_pro_enabled: bool = False`, `vercel_env: Optional[str]` |
| `erato_cloud/subscriptions/repository.py` | Create | D4 store; `find_effective`, flag/cancel/revert; indexes `idx_subscriptions_subject` and `uq_subscriptions_subject_active` (partial unique, filter `{status: "active", cancel_at_period_end: false}`) |
| `erato_cloud/policy.py` | Create | `SubscriptionPlanPolicy` (AD19, AD20), catalogue constants, `get_subscription_plan_policy` |
| `erato_cloud/billing/port.py`, `erato_cloud/billing/free.py` | Create | `BillingProvider` (`checkout_band`, `activate`, `cancel`, `set_extra_seats`), `FreeBillingProvider` with flag + `VERCEL_ENV` guard |
| `erato_cloud/checkout/band.py` | Create | `BandCheckout.run(user, name)`: steps of AD11 incl. compensation |
| `erato_cloud/routers/plan.py` | Create | `/api/plan/*` endpoints incl. `/api/plan/checkout/band` |
| `erato_cloud/wiring.py` | Create | `install(app)` |
| `scripts/ensure_cloud_indexes.py` | Create | idempotent cloud bootstrap |
| `web/` (`vite.config.ts`, `index.html`, `src/main.ts`, `src/PlanView.vue`, `src/BandCheckoutView.vue`, `src/api/plan.ts`) | Create | plan page and band checkout through `createEratoApp({ payments })`; nothing else |
| `vercel.json` | Create | build `web`, function `api/index.py` with `includeFiles: "erato/app/**"`, rewrites like core |
| `requirements.txt` | Create | `-r erato/requirements.txt` |
| `pytest.ini`, `tests/conftest.py` | Create | `pythonpath = . erato`, reuse core env fixture shape |
| `.github/workflows/ci.yml` | Create | recursive submodule checkout, Mongo service, pytest, web vitest + build |
| `.env.example`, `docs/runbook-preview.md` | Create | variable ownership table, pointer check, promotion order, rollback |

## Data Flow

### Section save with conflict (versioning, unchanged)

```
Client A (rev 7)         API sections router        VersioningService            Mongo
   | PUT lyrics?expected_rev=7 |                          |                          |
   |-------------------------->| require(EDIT) (+band active if band_id, non-owner)  |
   |                           |---- save(lyrics,7) ----->| findOneAndUpdate         |
   |                           |                          | {_id, section_revs.lyrics:7}
   |                           |                          | $set + $inc, BEFORE ---->|
   |                           |                          |<--- before doc (rev 7) --|
   |                           |                          | content changed? insert snapshot rev 8,
   |                           |                          | prune rev <= 8-50 (errors swallowed)
   |<-- 200 {content, rev: 8} -|<-------------------------|                          |
Client B (rev 7)                                          |                          |
   | PUT lyrics?expected_rev=7 |------------------------->| findOneAndUpdate -> null |
   |                           |                          | re-read comp + newest snapshot
   |<-- 409 section_conflict {current_rev: 8, content, author, updated_at}            |
```

Frontend: `useSectionSave` sends only sections whose serialized value differs from the last saved
baseline, settles all with `Promise.allSettled`, updates `section_revs[s]` and the baseline on 200,
queues one `SectionConflictDialog` per 409. "Sobrescribir" resends with `expected_rev = current_rev`;
"Cargar" replaces the local value and baseline with the 409 `content` and rev. Escape closes the
dialog without touching the local edit (it stays dirty).

### Band invitation redeem with seat limit (OD-6: multi-use until expiry)

```
User           /api/auth/redeem-invite     BandsService             PlanPolicy          Mongo
 |--- token ------------->|------------------>| find invitation by hash               |
 |                        |                   | no target -> 410 invitation_legacy    |
 |                        |                   | expired  -> 410 invitation_expired    |
 |                        |                   |-- is_band_active(G) -->| false -> 403 band_inactive
 |                        |                   |-- seat_limit(G) ------>| 8+extra | None
 |                        |                   | update_one {_id:G, members.user_id $ne uid,
 |                        |                   |   $expr size<limit} $push {uid, member} ------>|
 |                        |                   | matched 0: member? -> already_member : 409 band_full
 |<- 200 {band_id, status: joined|already_member} ------------------------------------------|
```

Band invitations are multi-use until expiry: redeem never sets `used_at` for band targets; the seat
limit is the only cap. Expiry reuses the existing invitations TTL value and index; the redeem path also
compares `expires_at` explicitly because the TTL monitor deletes with a delay.

### Role resolution on a band composition (unchanged)

```
require(action)
  -> composition_access (cached)
  -> band_context: only if band_id and user -> bands.find_one({_id}, {owner_id, members.user_id})
  -> resolve_role(uid, comp, band)          (pure, AD7 order)
  -> can(role, VIEW)? else 404 ; can(role, action)? else 403
  -> action != VIEW and role != OWNER and band_id -> policy.is_band_active(band_id)
       false -> 403 band_inactive
```

### Ownership transfer (AD10, AD20)

```
Owner A: POST /api/bands/G/transfer {to_user_id: B}
   -> conditional $set pending_transfer {B, A, now, now+14d}
   -> no match: B not member -> 409 not_a_band_member ; unexpired pending -> 409 transfer_pending
B: DELETE /api/bands/G/transfer            (reject; owner uses the same call to cancel)
B: POST /api/bands/G/transfer/accept
   -> read: absent 404 ; other target 403 ; expired -> clear, 410 transfer_expired
   -> policy.confirm_band_transfer(G, A, B)
        core: True
        cloud: no effective sub -> True
               provider unavailable -> raise billing_unavailable (403)
               flag prev (cancel_at_period_end | canceled) -> insert new {band G, payer B, extra_seats copied}
               insert fails -> revert prev -> False -> 409 transfer_not_confirmed
   -> conditional swap {owner A, pending.to B, unexpired}: owner_id B, roles swapped, pending null
GET /api/bands/G: expired pending reported as null (lazy)
```

### SaaS band creation hand-off (AD11, AD12)

```
Core BandView "Crear banda"
  -> useEntitlements(): band_creation_mode = hand_off (cloud) | direct (self-hosted)
     direct   -> BandCreateForm -> POST /api/bands -> 201
     hand_off -> router.push(bandCreationEntry = /plan/bands/new)   [cloud page, same SPA]
Cloud BandCheckoutView -> POST /api/plan/checkout/band {name}
  -> BandCreate validation (422)
  -> provider.checkout_band(user): free + flag + not production -> confirmed ; else 403 billing_unavailable
  -> core BandsService.create_for_user(user, name)          -> band G (failure: nothing else created)
  -> provider.activate({band, G}, payer=user, extra_seats=0) -> subscription
       failure -> core BandsService.delete_band(G) (idempotent), re-raise
  <- 201 {band, subscription} -> UI refreshes entitlements, routes to core /bands/G
```

### Entitlement resolution under the cloud (AD19)

```
request -> Depends(get_plan_policy) -> SubscriptionPlanPolicy (one instance per request)
  first user-scoped question for uid:
    subscriptions {subject user uid, EFFECTIVE}            hit -> pro
    bands.distinct _id {members.user_id: uid}              (idx_bands_members_user_id)
    subscriptions {subject band in ids, EFFECTIVE}         hit -> pro ; else gratis
  later questions in the same request -> memo
```

## API Contracts

### Core (`erato`)

```
GET  /api/me/entitlements                     auth required, no query parameters
  200 {"can_share_with_people": bool, "can_create_band": bool, "can_view_history": bool,
       "demo_limit_per_composition": int|null, "extensions_available": bool,
       "band_creation_mode": "direct"|"hand_off"}
  Values are user-scoped and never vary per composition.

PUT  /api/compositions/{id}/lyrics|chords|tablature?expected_rev=<int>
  body: section model (unchanged)
  200 {<section fields>, "rev": int}
  409 {"error": "section_conflict", "message", "detail", "section", "current_rev", "content",
       "author": {"id", "display_name"}|null, "updated_at"}

GET  /api/compositions/{id}/history/{section}?limit=20&before_rev=<int>     require(EDIT) + history gate
  200 {"items": [{"rev", "author": {...}|null, "created_at"}], "next_before_rev": int|null}
GET  /api/compositions/{id}/history/{section}/{rev}
  200 {"rev", "content", "author", "created_at"}
POST /api/compositions/{id}/history/{section}/{rev}/restore?expected_rev=<int>  (expected_rev required)
  200 same as section PUT ; 409 section_conflict

GET  /api/compositions/{id}  -> adds "section_revs": {"lyrics", "chords", "tablature"} (0 default),
     "band_id": str|null, "band_editable": bool, "band_active": bool|null
GET  /api/compositions       -> items add "band_id": str|null, "via_band": bool

PATCH  /api/compositions/{id}/band            owner; {"band_id": str|null, "band_editable": bool}
       non-null band_id: sharing gate + band active + owner is member
PUT    /api/compositions/{id}/members/{uid}   owner; {"role": "editor"|"viewer"}; uid must be in band
DELETE /api/compositions/{id}/members/{uid}   owner
(removed) POST/GET/DELETE /api/compositions/{id}/invites

POST   /api/bands                     {"name": 1..80}  -> 201 BandResponse ; 403 plan_gate_band_creation
GET    /api/bands                     -> [BandSummary]  (bands the user belongs to)
GET    /api/bands/{band_id}           member -> BandResponse ; non-member -> 404
PATCH  /api/bands/{band_id}           owner  {"name"}
POST   /api/bands/{band_id}/invites   owner  -> 201 {"id", "invite_url", "expires_at"}
GET    /api/bands/{band_id}/invites   owner
DELETE /api/bands/{band_id}/invites/{invite_id}  owner
DELETE /api/bands/{band_id}/members/{uid}        owner (cannot remove self)
POST   /api/bands/{band_id}/leave                non-owner member
POST   /api/bands/{band_id}/transfer             owner {"to_user_id"} -> 201 ; 409 transfer_pending | not_a_band_member
DELETE /api/bands/{band_id}/transfer             owner (cancel) or target (reject) -> 204
POST   /api/bands/{band_id}/transfer/accept      target -> 200 BandResponse ; 410 ; 409 transfer_not_confirmed
POST   /api/auth/redeem-invite  {"token"} -> 200 {"band_id", "status": "joined"|"already_member"}

BandResponse: {"id", "name", "owner_id", "user_role": "owner"|"member",
  "members": [{"user_id", "display_name", "initials", "role"}], "seats_used": int,
  "seat_limit": int|null, "active": bool,
  "pending_transfer": {"to_user_id", "requested_at", "expires_at"}|null, "created_at", "updated_at"}
```

The band creation request rejects unknown fields (`extra="forbid"`), and the band invitation request
has no `role` field and forbids extras, so `role: "editor"` yields 422 (spec: "rejected or ignored").

Host (Python) contract, documented in `docs/seams.md`:

```
BandsService(policy).create_for_user(user_id: str, name: str) -> BandDocument   # 422 on invalid name
BandsService(policy).delete_band(band_id: str) -> None                          # idempotent
```

### Cloud (`erato-cloud`)

```
GET    /api/plan                    -> {"plan": "gratis"|"pro", "source": "own"|"band"|"none",
                                        "own_subscription": {"kind": "individual", "active"}|null,
                                        "owned_bands": [{"band_id", "name", "active", "extra_seats"}],
                                        "provider_available": bool}
POST   /api/plan/individual         -> activate Pro Individual (subject user)
DELETE /api/plan/individual         -> cancel (immediate for free)
POST   /api/plan/checkout/band      {"name"} -> 201 {"band": BandResponse, "subscription"}   (AD11)
                                       401 | 403 billing_unavailable | 422 validation_error
POST   /api/plan/bands/{id}         -> reactivate an existing inactive band (owner)
DELETE /api/plan/bands/{id}         -> cancel (owner = payer of the effective subscription)
PUT    /api/plan/bands/{id}/seats   {"extra_seats": 0..12} (owner; 409 seats_below_members)
(removed) POST /api/plan/bands {name}
```

Cloud frontend routes (all under `/plan`, auth required): `/plan` (plan page, nav entry) and
`/plan/bands/new` (band checkout, name `band-checkout`, the `bandCreationEntry`).

## Testing Strategy

Strict TDD is active: every task writes the failing test first (RED), then code (GREEN), then refactor.

Runners (exact):
- `erato` backend: `.venv/bin/pytest tests/` from the repo root (`pytest.ini`, `asyncio_mode = auto`),
  needs MongoDB at `localhost:27017` (`docker compose up -d mongo` or `TEST_MONGODB_URI`).
- `erato` frontend: `cd frontend && npm run test:unit` (Vitest, jsdom) and `npm run build`
  (`vue-tsc && vite build`).
- `erato` landing (new): `cd landing && npm run test:unit` and `npm run build`.
- `erato-cloud` backend (new): `.venv/bin/pytest tests/` with `pytest.ini` `pythonpath = . erato`,
  same Mongo requirement; CI uses a `mongo` service container.
- `erato-cloud` web (new): `cd web && npm run test:unit` and `npm run build`.

| Layer | What to test | Approach |
| --- | --- | --- |
| Unit (pure) | `resolve_role` order incl. band member gating of member roles; `can`; `UnlimitedPlanPolicy` answers incl. `confirm_band_transfer` True | plain pytest, no DB |
| Repository | conditional save, BEFORE doc, prune at 50, cascade; `add_member_if_seat` incl. concurrent `asyncio.gather` at the last seat; `set_member_role` no duplicates; leave detach; `request_transfer` single pending; swap with `arrayFilters`; `delete_band` detaches (members emptied), deletes invitations, second call no-op | real Mongo, per-test drop like existing tests |
| Service | `create_for_user` shape (`members [{owner}]`, `pending_transfer` null) and 422; `create` gate; transfer accept: confirm before swap, refusal leaves owner/roles/pending unchanged, expired 410 clears, second request 409 unchanged; reject by target; invitation multi-use by two users | real Mongo |
| Router/integration | every status/code in AD4; 422 before 409; todos unchanged; history and demo gates after authorization; entitlements 401 / unlimited (`direct`) / denying stand-in (`hand_off`) | `httpx.AsyncClient(ASGITransport(app))` |
| Seam contract | stand-in policy via `app.dependency_overrides[get_plan_policy]` records inputs: user-scoped questions receive only the user id; deny-all hits every gate call site (incl. band attach); limit 1; inactive band; refusing transfer hook; extra router via `include_router` served; `api.index.app is app.main.app` | `tests/test_plan_policy_contract.py`, overrides cleared in a fixture |
| Scripts | `ensure_indexes` creates and `--rollback` drops new names; migration dry run, backup-first apply, idempotent, restore round-trip, `--confirm-db` mismatch | extend `tests/test_ensure_indexes_script.py`, new `tests/test_migrate_bands.py` |
| Frontend unit | `useSectionSave`; `createEratoApp` without payments (no `/plan` route, no nav extras), with payments (route resolves in shell), guard throws on non-`/plan` path or unresolved `bandCreationEntry`; `useBandCreation` three states; `BandView` self-hosted shows form and no payment control; `useEntitlements` gating and refresh; footer only for anonymous public route; `useSlideNav` | Vitest + `@vue/test-utils` |
| Landing static checks | tokens only, no `!`/emoji in copy, CTA hrefs from `VITE_APP_URL`, placeholder links | Vitest reading SFC/CSS sources |
| Cloud backend | catalogue scenarios; OD-4: Gratis member of active band is Pro on a composition outside the band, loses it on leave/inactive, keeps it via own sub or another band; memo: one resolution per request (query count spy); kill switch ignores free subs incl. band inheritance; production guard; partial unique index; checkout success, activation failure -> band deleted and no sub, creation failure -> no sub, flag off -> nothing; direct `POST /api/bands` 403; transfer step: happy path, free supersede, gateway overlap seats, no effective sub, refusal, insert-failure revert | cloud pytest with real Mongo |
| Cloud web | only `/plan*` registrations; `bandCreationEntry` resolves; checkout view handles 403/422 | Vitest |
| E2E | manual runbook checklist on the preview (anonymous link, footer, checkout creates band, seat full, read-only, transfer) | no E2E framework exists; not added |

## Threat Matrix

N/A - no routing of agent work, shell command composition, subprocess, VCS/PR automation,
executable-file classification, or process-integration boundary. (HTTP route additions are covered by
the permission tests above; the migration script performs no shell or VCS operations.)

| Boundary | Applicability |
| --- | --- |
| Documentation-like paths | N/A: no file classification or execution |
| Git repository selection | N/A: no git automation in code |
| Commit state | N/A |
| Push state | N/A |
| PR commands | N/A |

## Migration / Rollout

1. `erato` `preview` branch created from `main`; `erato-cloud` `preview` branch, submodule `branch = preview`.
2. Units merge into `erato` `preview` per the proposal slicing; each cloud unit bumps the submodule
   pointer in the same PR, after the public unit merged.
3. Preview DB `erato_preview` starts empty: run `python -m scripts.ensure_indexes` (core) and
   `python -m scripts.ensure_cloud_indexes` (cloud) with `MONGODB_DB=erato_preview`.
4. `scripts/migrate_bands.py` is exercised by tests and may be run against `erato_preview`
   (`--apply --confirm-db erato_preview`); with an empty DB it reports nothing to do.
5. Rollback: drop `erato_preview` and rerun both bootstraps; or `ensure_indexes --rollback`; unset
   `FREE_PRO_ENABLED`; revert the pointer bump; restore script for migrated data.
6. Behavior during rollout: absent `expected_rev` keeps last-write-wins; compositions without
   `band_id` resolve exactly as before; bands without a `pending_transfer` field read as null.

## Impact on proposal slicing (for sdd-tasks)

The proposal's slice table predates the 2026-10-04 decisions. Units whose content changes:

| Unit | Refresh needed |
| --- | --- |
| X1 | Port signatures per AD5 (user-scoped, `confirm_band_transfer` returning bool); entitlements adds `band_creation_mode`; contract test asserts user-only inputs |
| B3 | Gate call sites per AD6 table, including the sharing gate on band attach (`PATCH .../band`); `demo_limit(user)` without composition |
| B5 | `BandsService.create` + `create_for_user` + idempotent `delete_band` (AD18), `pending_transfer: null` on create, member shape `{user_id, role}`, multi-use band invitations (no `used_at`) |
| B6 | Unblocked (OD-1). AD10: embedded storage, 409 second request, reject by target, confirm-before-swap, `transfer_not_confirmed`, leave/remove clear a transfer aimed at the departing member |
| FX | Narrowed to the payment-only factory (AD12): `/plan` prefix guard, `bandCreationEntry`, `useBandCreation`; size likely at the low end of 150-300 |
| F2 | Band screen hosts `BandCreateForm` and the mode-driven "Crear banda" control (direct / hand-off / not actionable) |
| C2 | `SubscriptionPlanPolicy` per AD19 (user-scoped, own sub OR any active band, request memo, kill switch on inheritance, direct creation always denied) |
| C3 | Replace `POST /api/plan/bands {name}` with `POST /api/plan/checkout/band` and `BandCheckout` (create via core, activate, compensate); `BillingProvider.checkout_band` |
| C4 | No longer a no-op: AD20 subscription step (flag/supersede, insert with copied seats, revert on failure) and effective-subscription seat limit |
| C5 | Plan page plus `BandCheckoutView` registered as `bandCreationEntry`; nothing outside `/plan` |

## Risks

| Risk | Mitigation |
| --- | --- |
| Vercel must clone the public submodule in the `erato-cloud` build (HTTPS URL required; private submodules unsupported) | `.gitmodules` uses HTTPS; verify in C0 before other cloud units |
| Python function bundle must include `erato/app/**` and nested `-r erato/requirements.txt` must resolve | `includeFiles` in cloud `vercel.json`; verify in C0 with a deployed health route |
| Duplicate Vue instances when the cloud web build imports core sources | `resolve.dedupe: ['vue', 'vue-router']`; Vitest test mounts `createEratoApp` from the cloud |
| MongoDB may reject two indexes with the same key pattern (`idx_subscriptions_subject` and the partial unique) on older servers | bootstrap test against the CI Mongo version and Atlas M0 version; if rejected, author decides (D4 owns the index set) |
| No transactions: multi-step writes (leave, checkout + compensation, transfer step, snapshot) can stop midway | ordering per AD9/AD11/AD18/AD20, idempotent retries, explicit reverts, snapshot failure tolerated by spec |
| Transfer window: a lost swap race after the host subscription step (AD20) is now compensated via `abort_band_transfer`; the remaining risk is the function dying between confirm and swap | host owns compensation; abort exceptions are logged as `transfer_abort_failed` without changing the 404; revisit the process-death gap with the gateway |
| Checkout compensation fails (band created, activation failed, delete failed) | the band exists without a subscription, i.e. inactive and read-only for members; logged with band id; owner can reactivate from the plan page or it is cleaned manually (runbook) |
| Per-request cost of OD-4 resolution (up to three indexed reads) | request-scoped memo (AD19); only on requests that ask an entitlement question; projections `{_id: 1}`; indexes already approved |
| Entitlements shown in the UI go stale after joining/leaving a band or paying | `useEntitlements` refreshes after join, leave, transfer and on return from `/plan*`; backend is authoritative on every request |
| Extra reads on band compositions (band lookup, policy query) | load only when `band_id` set; projection; memo per request |
| Removing composition invitation endpoints breaks current UI flows and tests (`test_sharing_router.py`, `test_sharing_roles.py`, `SharingModal.vue`) | done in the same slice as the replacement (B7/F3); tests rewritten first |
| Legacy content on future production promotion gets no baseline snapshot | out of scope; revisit at promotion |
| Hidden coupling: cloud web build depends on core source paths; cloud backend imports `BandsService` and `BandCreate` | documented in `docs/seams.md`; core tests pin `createEratoApp` options and the two host operations |
| `erato` has no test CI; cloud CI is the only automated cross-check | recommend a core CI workflow as a follow-up (not in specs) |

## Resolved decisions (author, 2026-10-04)

| ID | Resolution | Reflected in |
| --- | --- | --- |
| OD-1 | `bands.pending_transfer {to_user_id, requested_by, requested_at, expires_at}` or null, embedded; `bands.members` entries `{user_id, role}` with role `owner` or `member` | AD10, AD18, B6 unblocked |
| OD-2 | `erato-cloud` extends the frontend ONLY for payments; all other UI lives in `erato`; self-hosted has no payment UI | AD12 |
| OD-3 | Option 1: creation logic, `POST /api/bands` and UI in the core, gated by `can_create_band`; SaaS hands off to the cloud checkout, which calls the core create, activates Pro Banda (subject = band) and compensates with the core delete | AD6, AD11, AD18 |
| OD-4 | Entitlements are user-scoped and account-wide: own active subscription OR membership in ANY active band | AD5, AD6, AD19 |
| OD-6 | Band invitation links multi-use until expiry; expiry reuses the existing invitations TTL | Data flow "Band invitation redeem", B5 |
| Multiple bands | An owner may create several bands in SaaS, each with its own paid Pro Banda; self-hosted unlimited | AD11 |
| Spec assumptions accepted | 409 for a second pending transfer; idempotent compensation delete that detaches compositions; free one-click checkout with `FREE_PRO_ENABLED` counts as payment confirmed in preview | AD4, AD10, AD11, AD18 |
| Per-composition roles | Assignable only to members of the composition's band (now explicit in `sharing-and-visibility`) | AD7, AD8 |

## Open decisions

None of these blocks the design or sdd-tasks; each has a stated default the tasks can follow.

- [x] **OD-5 (resolved 2026-10-04)**: conflict author after identical-content saves stays best effort:
  author of the newest snapshot at or below `current_rev` (AD3). No schema change for exact attribution.
- [x] **OD-7 (resolved 2026-10-04)**: the plan page presents Pro inherited from a band
  (`source: "band"` in `GET /api/plan`) as "Pro" with the band name as the reason, with no cancel
  action for it.
- [x] **OD-8 (resolved 2026-10-04)**: a user who already has Pro through a band may also activate Pro
  Individual (keeps Pro after leaving); the plan page shows it as optional.
- [x] **OD-9 (resolved 2026-10-04)**: seat limit during a transfer overlap is `8 + max(extra_seats)`
  over the band's effective subscriptions, and the new subscription copies the previous `extra_seats`
  (AD20). The new owner B pays for the inherited extra seats on top of the Pro Banda base price. With
  the free provider the amount is 0; with a real gateway, accepting a transfer charges B for base plus
  extra seats, deferred to the gateway work together with G-1.
- [ ] **G-1 (deferred to the gateway)**: with a real gateway the checkout is asynchronous, so the
  requested band name must survive the redirect/webhook (needs storage, i.e. a data-model decision
  under AGENTS.md rule 1). Not needed for the free provider in this change.
