# Proposal: Erato monetization in Vercel Preview (landing, versioning, bands and plans, public footer)

## Intent

Erato today is a single-tier app: any user can invite anyone to a composition, there is no band entity, no plans, no version history, and concurrent saves silently overwrite each other. Steps 1-4 of `pasos.md` turn it into a product that can be offered: a landing that leads to registration, version history with conflict detection, plans (Gratis / Pro Individual / Pro Banda) backed by a Band entity, and a "Guardado en Erato" footer on public links.

Why now: the author wants the whole monetization surface usable end to end before integrating a payment gateway. Everything runs in a Vercel **Preview** environment; production stays as it is. Pro is free for now and self-activated, behind a billing port that the gateway will replace later.

**Two repositories (revised 2026-10-03, P4 changed by the author).** Subscription and billing logic must not be exposed in the public repo, so the work is split:
- **Public `erato` (this repo)**: landing (`landing/`), "Guardado en Erato" footer, versioning (revisions + conflict detection), Bands (membership, invitations, ownership transfer, `resolve_role` with band context, `compositions.band_id`/`band_editable`), the `PlanPolicy` port with an unlimited default (self-hosters get everything), and the extension points the private repo needs.
- **Private `erato-cloud` (new)**: `subscriptions` collection and repository, `SubscriptionPlanPolicy` (seat limit 8 + `extra_seats`, plan quotas, read-only when unpaid, creating a band requires Pro Banda), the billing/grant port and the `provider: "free"` implementation behind `FREE_PRO_ENABLED`, the plan page and activation endpoints/UI; later the gateway (Flow / Mercado Pago) and webhooks.

The OpenSpec artifacts for this change stay in THIS repo; cloud-side work is tagged `repo: erato-cloud` in specs and tasks.

## Scope

### In Scope — public `erato`
- **Landing** in `landing/` (Vue 3 + Vite + TS + Vitest, own Vercel project deployed from `erato`), reimplemented from `erato-design-system/erato-landing/`, reusing `frontend/src/design-system` via a Vite alias. No waitlist; CTAs go to the app's register/login. Fix the known gaps: CTA targets, keyboard slide navigation, `prefers-reduced-motion`. The privacy and terms footer links stay as placeholders (`#privacidad`, `#terminos`) until the author supplies texts (P18); no legal text is written by the agent; real pages are required before any public launch.
- **Versioning**: per-section snapshots for lyrics, chords and tablature; per-section revision counter; conflict detection (409) on save; history view and restore in the UI. History gating goes through `PlanPolicy` (unlimited default = history for everyone).
- **Bands (core)**: `bands` collection and repository, `band_id`/`band_editable` on compositions, band-targeted invitations, new role resolution order, read-only enforcement in `require()` driven by a `PlanPolicy` answer (unlimited default = always writable), atomic seat join with the limit supplied by `PlanPolicy` (unlimited default = no limit), ownership transfer (14-day lazy expiry), leaving a band, migration script that empties `members`.
- **`PlanPolicy` port and extension seams**: the port, `UnlimitedPlanPolicy` as the default, a FastAPI dependency getter the private repo overrides, hooks for band creation, ownership transfer and seat limit, a plan/entitlements read endpoint the UI uses for gating, and a frontend extension point for cloud pages (mechanism is a design decision, see Approach 7).
- **Frontend (core)**: band management screen, `SharingModal.vue` rework, dashboard changes, read-only banner, history panel, conflict dialog, routes; gating driven by the entitlements endpoint, never by plan names hard-coded in the core.
- **Footer** "Guardado en Erato" with a register link on anonymous views of public shared compositions.
- **Preview integration branch** `preview` in `erato` (long-lived) and the landing's Vercel project config.

### In Scope — private `erato-cloud` (`repo: erato-cloud`)
- **Bootstrap**: repository with `erato` as a git submodule (tracking `erato`'s `preview` branch), app entry that imports `app.main.app`, `vercel.json`, CI, `.env.example`, and an index bootstrap for cloud-owned collections.
- **Subscriptions**: `subscriptions` collection, repository and indexes (approved in D4; ownership moved to `erato-cloud`).
- **`SubscriptionPlanPolicy`**: seat limit 8 + `extra_seats`, count quotas, read-only when unpaid, creating a band requires Pro Banda, gating of sharing with people and history; wired with `app.dependency_overrides`.
- **Billing/grant port** and the `provider: "free"` implementation behind `FREE_PRO_ENABLED` (fail closed; refuses when `VERCEL_ENV=production`), activate/cancel/seats endpoints added with `include_router`, subscription side of ownership transfer.
- **Plan page** and activation UI, plugged into the core frontend extension point.
- **Preview environment**: the full preview (app + API) is deployed from `erato-cloud`'s `preview` branch; Preview-scoped env vars (DB name, JWT secret, Cloudinary prefix, `APP_BASE_URL`, `FREE_PRO_ENABLED`) live in the `erato-cloud` Vercel project; runbook; index bootstrap (core + cloud) against the preview DB.

### Out of Scope
- Payment gateway (Flow / Mercado Pago), webhooks, real charges, invoicing (future `erato-cloud` work).
- Packaging the backend as an installable Python package (not needed: the submodule mechanism works with the current layout).
- Cloudflare R2 migration (audio stays on Cloudinary); byte-based storage quotas.
- Real-time editing (step 5), mobile/PWA (step 6).
- Deciding what happens to the existing Vercel project that deploys `erato` `main` (the author disconnects it or leaves it alone at promotion time).
- Production rollout and production data migration (the migration script is built and tested, but only run against the preview DB in this change).
- Legal texts (privacy policy, terms), tax obligations, custom domains (user-owned items, see the end).
- Step 4 outreach work (rehearsal rooms, studios, `TRADEMARK.md`).

## Capabilities

All specs live in THIS repo's `openspec/`. The "Repo" tag tells sdd-spec and sdd-tasks where each requirement is implemented.

### New Capabilities
- `landing-page` (repo: `erato`): public marketing site in `landing/`; slide navigation (index 0-6, counter, wheel debounce 900 ms with scroll exclusions, keyboard, reduced motion), responsive collapse at 980 px, CTAs to the app, placeholder privacy/terms links, both themes, accessibility.
- `composition-versioning` (repo: `erato`): per-section revision counter, conditional save with `expected_rev`, 409 conflict contract, snapshot recording, retention, history listing and restore, history gating through `PlanPolicy`.
- `bands-and-membership` (repo: `erato`): band lifecycle, membership, band-targeted invitations, seat join honoring the policy-supplied limit, leaving a band, ownership transfer with expiry, composition sharing with a band.
- `plan-policy-port` (repo: `erato`): `PlanPolicy` contract, `UnlimitedPlanPolicy` default (self-hosters get everything), dependency getter and hooks (band creation, transfer, seat limit, read-only, quotas, history), entitlements endpoint, backend and frontend extension seams for the private repo.
- `plans-and-subscriptions` (repo: `erato-cloud`): plan catalogue, `subscriptions` repository, `SubscriptionPlanPolicy` rules (seat limit, quotas, read-only when unpaid, band creation requires Pro Banda, sharing with people, history), billing/grant port with the free provider and its fail-closed flag, subscription lifecycle (activate, cancel, seats, transfer), plan page.
- `preview-deployment` (repo: both): `preview` branches in both repos, `erato-cloud` Vercel project for app + API (env isolation: DB, secrets, media prefix, base URL), landing Vercel project from `erato`, submodule pointer rule, index bootstrap (core + cloud), guard against free Pro in production, promotion order.

### Modified Capabilities
All modified capabilities are implemented in `erato`; the plan-dependent parts are expressed through `PlanPolicy`, with the paid rules in `plans-and-subscriptions`.
- `sharing-and-visibility`: role resolution adds band roles; invitees must be band members; invitations target bands; sharing with people is allowed only when `PlanPolicy` allows it (under the cloud policy, Free and Pro Individual cannot); public read-only link stays on all plans; band content becomes read-only when `PlanPolicy` reports the band as not active (never under the unlimited default); "Guardado en Erato" footer on anonymous public views. The "exactly two visibility options" requirement stays: band sharing is a separate control, not a third visibility value.
- `composition-content`: section write endpoints accept `expected_rev` and may return 409; composition response exposes per-section revisions.
- `app-shell-and-navigation`: new routes/screens (band management, history panel), read-only banner, conflict dialog, and the frontend extension point through which `erato-cloud` adds the plan page.
- `media-storage`: demo uploads rejected when `PlanPolicy` reports the demo count quota as reached (unlimited default: no quota; cloud values per P16).
- `backend-platform`: new environment settings documented in `.env.example`; the app object stays importable as `app.main.app` and accepts external routers and dependency overrides (seam contract for `erato-cloud`); feature flags fail closed when unset.
- `data-persistence`: none (that spec forbids defining collections; schema lives in design after approval).
- `design-system-port`: none (P19 accepted: native `<a class="er-btn">`, no `ErButton` link variant).

## Approach

### 1. Landing (`landing/`)
Vue 3 SPA with one component per slide plus a small navigation composable (index, wheel debounce, scroll exclusions, keyboard, reduced motion) tested with Vitest. Vite alias `@ds-vue` -> `../frontend/src/design-system`; styles from `../erato-design-system` as in `frontend/vite.config.ts`. CTAs are native `<a class="er-btn ...">` built from `VITE_APP_URL`. Footer privacy/terms links point to `#privacidad` and `#terminos` (placeholders, P18). Own `landing/vercel.json`; the root `vercel.json` is not touched. The landing's Vercel project deploys from `erato` (its `preview` branch for this change). Verify that the Vercel build can read files outside the Root Directory.

### 2. Preview environment (two repos)
- **Branches**: both repos get a long-lived `preview` integration branch. `erato-cloud`'s submodule pointer follows `erato`'s `preview` branch.
- **App + API**: deployed as one Vercel project from `erato-cloud`'s `preview` branch. Its Preview-scoped env vars: `MONGODB_DB=erato_preview` (same Atlas M0), its own `JWT_SECRET`, `CLOUDINARY_FOLDER_PREFIX=erato-preview`, `APP_BASE_URL` = the alias of that project's `preview` branch, `FREE_PRO_ENABLED=true`. The free provider additionally refuses when `VERCEL_ENV=production`.
- **Policy selection**: no `PLAN_POLICY` env var is needed any more. The public app always uses `UnlimitedPlanPolicy`; the `erato-cloud` app always overrides it with `SubscriptionPlanPolicy`. Self-hosters and the current `erato` `main` deployment keep today's behavior.
- **Landing**: separate Vercel project from `erato`, `VITE_APP_URL` = the `erato-cloud` preview alias.
- **Indexes**: core indexes via `erato`'s `scripts/ensure_indexes.py`; cloud-owned indexes (`subscriptions`) via `erato-cloud`'s own bootstrap, both run against the preview DB name.
- **Existing production project**: the Vercel project that deploys `erato` `main` today is not touched by this change; at promotion time the author disconnects it or leaves it alone (not decided here).
- **Promotion to production** (outside this change): promote `erato` to `main` first, then `erato-cloud` updating the submodule pointer.

### 3. Versioning
Per-section revision counter on the composition (approved, see D1). A section save is a single conditional update (`section_revs.<s> == expected_rev`); a mismatch returns 409 with the current revision, content, author and timestamp. After a successful save the backend records a full snapshot of that section and prunes beyond the retention cap. Identical content does not create a snapshot. Frontend saves only dirty sections, uses `Promise.allSettled`, updates revisions for successes and opens a conflict dialog per conflicting section. Restore = a normal save of the old content (creates a new revision).

### 4. Bands and permissions (backend, `erato`)
- Repository for `bands`; its indexes and `idx_compositions_band_id` added to `ensure_indexes.py` and its test. The `subscriptions` repository and indexes are NOT in this repo (see 4b).
- `composition_access` pre-resolves band context (membership + band active status from `PlanPolicy`) only when `band_id` is set, and passes it to a still-pure `resolve_role`. Order (approved): owner > invited member role > band member with `band_editable` -> editor > public -> viewer > none (404).
- `require()` enforces read-only when `PlanPolicy` reports the band as not active.
- `PlanPolicy` port with `UnlimitedPlanPolicy` (current behavior; always allows, no limits, bands always active) exposed through a FastAPI dependency getter (`get_plan_policy`). Gates asked of the port: sharing with people, band creation, history, demo count, seat limit, band active status, and a transfer hook so the cloud can move the subscription.
- Seat limit enforced at join with a conditional update on `bands` (`$size(members) < limit` and user not already a member, D2), where `limit` comes from `PlanPolicy` (unlimited: no size condition); `add_member` on compositions made atomic.
- Transfer: request with `expires_at` = +14 days, evaluated lazily on read/accept (no cron in preview). Accepting changes the band owner and calls the `PlanPolicy` transfer hook (no-op in the core).
- Leaving a band detaches the leaver's compositions (`band_id` null, `band_editable` false, `members` emptied). The owner must transfer first.
- Migration script (idempotent, dry-run by default, in `erato`): empties `members`, handles legacy invitations per D3.

### 4b. Plans and subscriptions (backend, `erato-cloud`)
- `subscriptions` repository and indexes (D4) plus the cloud index bootstrap.
- `SubscriptionPlanPolicy` implements the port from `subscriptions`: limit 8 + `extra_seats`, quotas (P16), read-only when unpaid (P10), band creation requires Pro Banda (P11). Installed with `app.dependency_overrides[get_plan_policy]`.
- Billing/grant port (`BillingProvider`): `FreeBillingProvider` creates/cancels `provider: "free"` subscriptions; enabled only when `FREE_PRO_ENABLED=true`, refuses when `VERCEL_ENV=production` (P14). The gateway adapter later replaces it without touching policy, permissions or UI contracts.
- Activate/cancel/seats endpoints mounted with `app.include_router`. The transfer hook creates the new owner's subscription and cancels or flags the previous one (P12).

### 5. Frontend
Core (`erato`): band management (create, members, invite link, seats, transfer, leave), `SharingModal.vue` (public link for all plans; band sharing and per-member roles only when the entitlements endpoint allows them), dashboard listing band compositions, read-only banner, history panel, conflict dialog. Cloud (`erato-cloud`): plan page (current plan, activate free Pro, cancel, seats) and the entry points to it. All UI copy in Spanish, tuteo, no exclamation marks, no emoji, composed from existing DS primitives and tokens.

### 6. Footer
Anonymous viewers of a public composition see "Guardado en Erato" with a link to register. Not shown to authenticated users.

### 7. Cross-repo mechanism (verified facts)
The backend is not an installable package: there is no `pyproject.toml`, `app/main.py` builds `app = FastAPI(...)` at module level and includes the routers, and `api/index.py` re-exports `app.main.app`. Therefore `erato-cloud` includes `erato` as a **git submodule**, imports `app.main.app`, adds its routers with `include_router` and its policy with `app.dependency_overrides`, and exposes the result from its own `api/index.py`. No packaging refactor is required. Seams the core must expose: the `get_plan_policy` dependency getter, the band creation / transfer / seat-limit / band-active hooks on the port, the entitlements endpoint, and a frontend extension point for cloud pages.

**Frontend extension point — DESIGN decision (sdd-design chooses, author confirms if it changes the core shape):**

| Option | Shape | Pros | Cons |
| --- | --- | --- | --- |
| A. Build-time composition | The core frontend exports an app factory (for example `createEratoApp({ extraRoutes, navItems })`); `erato-cloud` has its own Vite entry that imports it from the submodule and registers the plan page and nav entries | One SPA, one router, shared auth state and DS; type-checked against the core | The core's `frontend/src/main.ts` and router must be refactored into a factory; cloud build depends on core build internals (alias paths) |
| B. Separate cloud SPA under a path | `erato-cloud` builds a small Vue app served at `/plan/*` via Vercel rewrites; the core shows plan links only when the entitlements endpoint reports billing available | Core frontend almost unchanged; strong isolation | Two bundles, duplicated auth bootstrap and DS setup, full page navigation between apps |

### 8. Branch and PR strategy per repo
Stacked PRs into each repo's `preview` branch; the bands/plans series as a `feature-branch-chain` on top of `preview` in each repo. Cross-repo ordering rule: the public unit merges into `erato` `preview` first, then the cloud unit bumps the submodule pointer in `erato-cloud` `preview`.

## Decisions needing explicit approval (AGENTS.md rule 1)

Every item below was **BLOCKING for design and apply** of the units that touch it. As of 2026-10-03 D1-D4 are all approved by the author (status lines below); any new data-model question must be added here as a new blocking item.

### D1. Section-snapshot schema for versioning — APPROVED by the author on 2026-10-03: option C, as recommended (units V1-V4 unblocked)

| Option | Shape | Pros | Cons |
| --- | --- | --- | --- |
| A. Collection only | `section_revisions` docs; latest `rev` read from the collection | Composition doc unchanged | Conflict check is read-then-write (race window); two round trips per save |
| B. Embedded capped array | `compositions.history.<section>: [{rev, content, author_id, at}]` with `$push` + `$slice` | One atomic update | Every composition read carries history unless projected out; doc grows toward the 16 MB limit; history leaks into existing projections |
| **C. Counter + collection (recommended)** | `compositions.section_revs` counter + `section_revisions` snapshots | Atomic conflict check on the composition; composition stays small; history paged independently | Two writes per save; a failed snapshot insert leaves a gap in history (content itself stays correct) |

Recommended C. Example documents:

```json
// compositions (new field only)
{ "_id": "...", "section_revs": { "lyrics": 7, "chords": 3, "tablature": 2, "todos": 0 } }

// section_revisions
{
  "_id": "...",
  "composition_id": "ObjectId",
  "section": "lyrics",            // lyrics | chords | tablature
  "rev": 7,
  "content": "<full section value, same shape as the composition field>",
  "author_id": "ObjectId",
  "created_at": "ISODate"
}
```

- Indexes: unique `{composition_id: 1, section: 1, rev: -1}` (`uq_section_revisions_comp_section_rev`). Cascade delete with the composition.
- Existing compositions: missing `section_revs` is read as 0; no backfill write required. The first save of a non-empty section may record a baseline snapshot of the previous content (design decides).
- Retention cap: last 50 snapshots per section per composition, pruned after insert (`rev <= current - 50`).
- Size on M0 (512 MB shared by prod and preview): typical sizes lyrics ~3 KB, chords ~1 KB, tablature ~8 KB. A composition at the cap holds about 50 x 12 KB = 600 KB; 100 such compositions = ~60 MB. Acceptable at current scale; the cap is the lever.
- `todos` gets a counter only if the "todos versioned" default changes (see P3).

### D2. Denormalize `seat_limit` onto `bands` — APPROVED by the author on 2026-10-03: do NOT denormalize, as recommended (unit B5 unblocked)

| Option | Description |
| --- | --- |
| **No denormalization (recommended)** | Compute `limit = 8 + extra_seats` from the band's active subscription and pass it into the conditional update filter: `{_id, "members.user_id": {$ne: uid}, $expr: {$lt: [{$size: "$members"}, limit]}}`. The member-count race is closed atomically; the only remaining race is a concurrent seat change, which only the payer can trigger and is harmless. |
| Denormalize `bands.seat_limit` | Filter compares against a field on the same document. Fully self-contained, but adds a second source of truth that must be kept in sync on every subscription change (and by the future gateway webhook). |

### D3. Legacy `invitations` keyed by `composition_id` — APPROVED by the author on 2026-10-03: delete pending legacy invitations in the migration, and band invitations carry no role (redeemed band invitation always yields band role `member`), as recommended (units B1, B5 unblocked)

| Option | Description |
| --- | --- |
| **Delete pending legacy invitations in the migration (recommended)** | They grant composition membership, which the migration empties anyway; only the author's band and tests exist. Drop `idx_invitations_composition_id`, add `idx_invitations_target` on `{target.type, target.id}`. |
| Leave them to expire | Keep the field and index temporarily; redeem rejects invitations without `target`. Mixed shapes coexist until the TTL removes them. |
| Convert | Not possible: no band exists to target yet. |

Also to confirm: band invitations do not carry the composition `role` (`editor`/`viewer`); a redeemed band invitation always yields band role `member`. Per-composition roles are assigned later from the band's members in the sharing modal.

### D4. Other new fields and indexes introduced by this proposal — APPROVED by the author on 2026-10-03, as recommended in the table below (units B1, B4, B6 unblocked)

| Item | Proposal | Why |
| --- | --- | --- |
| `bands.name` (string, required, 1-80 chars) | Add | The approved model has no display name; the UI needs one |
| `bands.created_at`, `bands.updated_at`, `subscriptions.created_at`, `subscriptions.updated_at` | Add | Consistent with other collections; audit of transfers |
| `bands` indexes | `idx_bands_owner_id`, `idx_bands_members_user_id` | Membership lookups per request and on the dashboard |
| `subscriptions` indexes | `idx_subscriptions_subject` on `{subject.type, subject.id}`; partial unique so a subject has at most one subscription with `status: "active"` and `cancel_at_period_end: false` | Fast plan resolution; prevents double activation. Exact partial filter goes to design |
| `compositions` index | `idx_compositions_band_id` | `list_by_user` band clause and leave-band detachment |
| `subscriptions.provider` value `"free"`, `provider_subscription_id: null`, `current_period_end: null` | Use existing approved fields | The free provider has no external id or billing period |
| Plan quotas | No stored fields; constants inside `SubscriptionPlanPolicy`, counts computed from existing demos | Avoid schema for values that will change |
| `users` | No new field; plan is resolved from `subscriptions` | Single source of truth |
| `section_revs` and `section_revisions` | See D1 | |

### Repository ownership of the approved model (note added 2026-10-03 after the P4 change; the approved content of D1-D4 is unchanged)

| Item | Owning repo |
| --- | --- |
| `subscriptions` collection, its repository, `idx_subscriptions_subject` and the partial unique index (D4); `provider: "free"` values; plan quota constants inside `SubscriptionPlanPolicy` | `erato-cloud` |
| `bands` (incl. `bands.name`, timestamps, `idx_bands_owner_id`, `idx_bands_members_user_id`), `compositions.band_id`/`band_editable`/`section_revs`, `idx_compositions_band_id`, `section_revisions` (D1), invitation `target` and `idx_invitations_target` (D3), migration script | `erato` |
| D2 seat-limit computation (8 + `extra_seats` from the band's active subscription) | `erato-cloud` computes the limit; `erato` applies it in the conditional update |

Both apps use the same database; no field, collection or index is added by the split. The split exposed no new data-model question, so no D5 is opened.

## Product defaults (resolved by the author on 2026-10-03)

One row per question. P4 and P18 were changed by the author; every other row was accepted by the author with no changes requested. P5, P6, P7 and P20 keep their accepted intent and are adapted to the two-repo setup that follows from P4.

| # | Question | Status | Resolved default (why) | Alternatives (not chosen) |
| --- | --- | --- | --- | --- |
| P1 | Versioning for Free too? | Accepted by the author (no changes requested) | Conflict detection for every plan; history view/restore Pro only; snapshots recorded for all plans (upgrading reveals past history; cost bounded by the cap). In the core, "Pro only" is a `PlanPolicy` gate (unlimited default: history for everyone) | Record snapshots only for Pro (less storage, empty history after upgrade); history for everyone |
| P2 | Conflict UX | Accepted by the author (no changes requested) | Per-section 409; dialog per conflicting section with "Cargar la versión guardada" and "Sobrescribir con la mía"; successful sections stay saved (`allSettled`); only dirty sections are sent (avoids spurious conflicts) | Single atomic save-all endpoint (bigger API change); auto-merge (not feasible for whole-section values) |
| P3 | Which sections are versioned, retention | Accepted by the author (no changes requested) | Lyrics, chords, tablature; todos not versioned and last-write-wins as today (toggled often, low value); keep last 50 per section | Version todos too; cap 20; time-based retention (90 days) |
| P4 | Repo split | **Changed by the author** | Create the private repo `erato-cloud` NOW so subscription logic is not exposed in the public repo. Public `erato`: landing, footer, versioning, bands, `PlanPolicy` port with the unlimited default, extension seams. Private `erato-cloud`: `subscriptions`, `SubscriptionPlanPolicy`, billing/grant port and free provider, plan page and activation, later gateway and webhooks. Mechanism: git submodule + `include_router` + `app.dependency_overrides` (Approach 7) | Keep everything in this repo behind ports, selected by `PLAN_POLICY` (previous default; exposes subscription logic) |
| P5 | Preview DB and media prefix | Accepted by the author (no changes requested); adapted to two repos | `MONGODB_DB=erato_preview` on the same M0, `CLOUDINARY_FOLDER_PREFIX=erato-preview`, set as Preview env vars of the `erato-cloud` Vercel project (the one that serves app + API); preview DB starts empty (no personal data copied) | Separate free Atlas project (full isolation, another account to manage); copy prod data with `mongodump` |
| P6 | Which branch hosts the preview | Accepted by the author (no changes requested); adapted to two repos | A long-lived integration branch `preview` in EACH repo; all slices merge there. The full preview deploys from `erato-cloud` `preview` (submodule pointer following `erato` `preview`); the landing deploys from `erato` `preview`. `main` in both repos untouched until the author promotes (`erato` first, then `erato-cloud` with the submodule bump) | Merge to `main` behind flags (production carries dormant code) |
| P7 | `APP_BASE_URL` in preview | Accepted by the author (no changes requested); adapted to two repos | Fixed alias of the `erato-cloud` project's `preview` branch, set as a Preview env var of that project scoped to that branch (stable invite links) | Derive from the request origin (host-header injection risk); `VERCEL_BRANCH_URL` system variable |
| P8 | Deployment Protection | Accepted by the author (no changes requested) | Disable Vercel Authentication for the previews of the app project (now `erato-cloud`) and the landing project (anonymous public links and the landing must work); add `noindex` to the preview | Keep protection and use a bypass token (breaks anonymous links); protect only non-`preview` branches if the plan allows it |
| P9 | What a band member sees, meaning of `band_editable=false` | Accepted by the author (no changes requested) | Dashboard lists all compositions shared with the user's bands. `band_editable=true` -> editor; `band_editable=false` -> **viewer** | `band_editable=false` grants nothing (band sharing then only enables per-member invites); list only `band_editable` compositions |
| P10 | Read-only when unpaid: scope | Accepted by the author (no changes requested) | Applies to band-derived and invited roles on compositions with `band_id`; the composition owner keeps full edit of their own content and can detach it from the band; no new sharing changes (invites, member roles) while inactive; a band with no subscription at all is treated as inactive (decided by `SubscriptionPlanPolicy` in `erato-cloud`; enforced by `require()` in `erato`) | Owner also read-only; allow sharing changes |
| P11 | Can Free / Pro Individual users create a band? | Accepted by the author (no changes requested) | Creating a band requires activating Pro Banda in the same flow (with the free provider that is one click); a band without an active subscription only exists after cancel/transfer. Rule lives in `erato-cloud`; the core asks the port (unlimited: anyone can) | Anyone creates a band, read-only until paid |
| P12 | Free provider periods and transfer | Accepted by the author (no changes requested) | Free subscriptions have no period: cancel is immediate; on transfer acceptance the old subscription is canceled and the new owner's starts at once. The `cancel_at_period_end` path is implemented in the port for the gateway | Simulate 30-day periods to exercise the real flow |
| P13 | Extra seats with the free provider | Accepted by the author (no changes requested) | Editable from the plan page with an upper bound of 12 extra (20 total) to exercise the seat flow without unbounded bands | Fixed 8 seats in preview; no bound |
| P14 | Free-Pro flag semantics | Accepted by the author (no changes requested) | `FREE_PRO_ENABLED` unset -> no activation AND existing `provider: "free"` subscriptions are not honored (kill switch). Additional guard: the free provider refuses to run when `VERCEL_ENV=production` | Flag gates only new activations; no `VERCEL_ENV` guard |
| P15 | Admin concept for free Pro | Accepted by the author (no changes requested) | Not needed: self-serve for any registered user (user decision) | Allowlist of emails |
| P16 | Plan quotas in this change | Accepted by the author (no changes requested) | Count-based only: Free = 1 demo per composition; Pro = up to 20 demos per composition. Byte-based quotas ("más espacio") wait for the R2 migration, as `pasos.md` orders | Free quota per account; defer all quotas (Cloudinary exposure with open Pro) |
| P17 | Landing CTA targets and domains | Accepted by the author (no changes requested) | "Iniciar sesión" -> `${VITE_APP_URL}/login`; "Empieza gratis" and every plan CTA -> `${VITE_APP_URL}/register`; preview uses `*.vercel.app` URLs | Plan CTAs carry `?plan=` to preselect the plan after registration |
| P18 | Privacy and terms pages | **Changed by the author** | KEEP the two footer links in the landing as placeholders (`#privacidad`, `#terminos`) until the author supplies texts; no legal text is written by the agent. Real pages are needed before any public launch (registration already collects emails) | Omit the links in preview (previous default); minimal pages with author-supplied text |
| P19 | Link-styled buttons (AGENTS.md rule 2) | Accepted by the author (no changes requested) | Native `<a class="er-btn ...">`, as the reference landing does; no DS change | Add an `href`/`as` prop to `ErButton` (DS port change, needs approval) |
| P20 | Delivery and chain strategy | Accepted by the author (no changes requested); adapted to two repos | `preview` in each repo as tracker. Independent tracks (landing, versioning, footer, preview config) as stacked PRs into `erato` `preview`; the bands/plans series as a `feature-branch-chain` on top of `preview` in each repo. Cross-repo ordering: the public unit merges first, then the cloud unit bumps the submodule pointer | `stacked-to-main` (deploys to production, conflicts with P6); one feature-branch-chain for everything |

## Rollback Plan

- **Preview DB**: all schema work in this change runs against `erato_preview`. Full rollback = drop that database and re-run `erato`'s `ensure_indexes.py` and the `erato-cloud` index bootstrap. Production DB is not touched.
- **Schema and indexes**: new collections and indexes are additive; `ensure_indexes.py` gains a matching drop list for rollback. Before running the migration on any DB with real data, take a `mongoexport` of `compositions` and `invitations`.
- **Migration that empties `members`**: dry-run by default, prints affected ids; writes a JSON backup of every `members` array and deleted invitation before mutating; a restore script re-applies the backup.
- **Dropping `erato-cloud`**: the core never imports the private repo, so deleting or pausing `erato-cloud` (or its Vercel project) leaves `erato` fully working with `UnlimitedPlanPolicy` (self-hosted behavior: every feature, no limits, bands always active). The `subscriptions` collection can then be dropped from the preview DB without affecting core data.
- **Auth / role resolution**: band context is only loaded for compositions with `band_id`; compositions without it follow the current order. Reverting the B2 PR restores the old function.
- **Free Pro flag**: unset `FREE_PRO_ENABLED` in the `erato-cloud` project (Preview scope) and redeploy; per P14 existing free subscriptions stop being honored immediately.
- **Submodule pointer**: a bad core update in the preview is rolled back by reverting the pointer bump commit in `erato-cloud` `preview`.
- **Versioning**: absence of `expected_rev` keeps the old last-write-wins behavior during rollout; snapshots can be dropped with the collection without affecting content.
- **Landing**: separate Vercel project; delete or pause it without impact on the app.
- **Branch strategy**: nothing reaches `main` in either repo; abandoning the change = abandoning both `preview` branches. The existing Vercel project for `erato` `main` keeps serving production unchanged.

## Risks

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Preview and production share the Atlas M0 (512 MB, shared connections) | Med | Separate DB name; retention cap; monitor storage; connection reuse already in place |
| Free-Pro flag scoped to Production by mistake in the `erato-cloud` project | Low | Fail-closed default; `VERCEL_ENV=production` guard (P14); runbook checklist; test that unset means disabled. (The former `PLAN_POLICY` misconfiguration risk no longer applies: the variable is removed and the policy is chosen by which repo serves the app) |
| Extra reads per request for band compositions | Med | Load band + band-active status (through `PlanPolicy`) only when `band_id` is set; one query each with projections; memo per request |
| Cross-repo drift: core changes break `erato-cloud` (renamed hook, changed port signature, moved module) | Med | The port and seams are a documented contract in `plan-policy-port`; core tests include a dependency-override test that mimics the cloud; `erato-cloud` CI runs against the pinned submodule; cross-repo ordering rule (public first, then pointer bump) |
| Submodule pointer staleness: the preview runs an older core than `erato` `preview` | Med | Every cloud unit that needs a core change bumps the pointer in the same PR; the runbook includes a "pointer equals `erato` `preview` HEAD" check before testing the preview |
| Two CIs and two secret sets (GitHub Actions, Vercel env vars) to keep consistent | Med | `.env.example` in each repo lists who owns each variable; runbook table of variables per Vercel project; `erato-cloud` CI checks out submodules recursively |
| `erato-cloud` tests need MongoDB (subscriptions, conditional updates) | Med | Same approach as `erato` CI (Mongo service container); reuse core test fixtures from the submodule path where possible |
| Frontend extension seam (Approach 7, option A or B) is a new public contract that the core must keep stable | Med | Decide in sdd-design; keep the seam minimal (routes + nav entries or a link target); cover it with a core test |
| The existing Vercel project still deploys `erato` `main` to production; after promotion, `erato` `main` alone would serve the app without plans | Med | Not touched in this change; flagged for the author to disconnect or keep at promotion time; documented in the runbook |
| Private repo access for sdd-apply (folder outside this repo) | Med | Cloud units start only after the author creates the repo and authorizes the folder scope (Prerequisites) |
| Seat-limit race on concurrent joins | Med | Conditional update (D2); test with concurrent redeems |
| Crons do not run in preview | High (certain) | Lazy expiry of transfers on read/accept; no new cron |
| Cloudinary free quota exposure (anyone can self-activate Pro) | Med | Count quotas (P16), preview folder prefix, kill switch (P14), usage check in the runbook |
| Deployment Protection blocks anonymous links and the landing | Med | P8 accepted: disable Vercel Authentication on the `erato-cloud` and landing previews; runbook checklist item |
| Landing build cannot read `../frontend` or `../erato-design-system` from Vercel | Med | Verify "include source files outside Root Directory" in L1; fallback: build from repo root with `cd landing` command |
| `band_editable=false` semantics misunderstood (P9) | Low | Accepted by the author (viewer); covered by role-resolution tests |
| ~~Schema approvals (D1-D4) delay the bands and versioning tracks~~ | No longer applies | D1-D4 approved on 2026-10-03 |
| Creating `erato-cloud` now delays the plans units (was the tradeoff noted in the old P4) | Med | Public tracks (landing, versioning, footer, bands core) proceed without the private repo; only C-units wait for the prerequisites |
| Total size ~7.100 authored lines incl. tests across two repos | High | Chained slices below, each within ~400 lines |

## Slicing (PR-sized units, ~400 authored lines each, tests included)

Unit IDs B1, B5, B6 and V1-V4 keep the meaning used in the D1-D4 status lines. The former B3 (`SubscriptionPlanPolicy`), B4 (billing port + free provider) and F1 (plan page) moved to `erato-cloud` as C2, C3 and C5; the subscription-related parts of the former B1 moved to C1. The D4 status line's reference to B4 now applies to C1-C3.

### Public `erato` units (PRs into `erato` `preview`)

| Unit | Content | Est. lines | Depends on | Track |
| --- | --- | --- | --- | --- |
| PV1 | `preview` branch setup notes, core `.env.example` (Cloudinary prefix, fail-closed defaults), core part of the runbook (landing project, index bootstrap) | 100 | - | Preview config |
| L1 | Landing scaffold, Vite alias, `landing/vercel.json`, Vitest, navigation composable (wheel, keyboard, reduced motion) | 380 | - | Landing |
| L2 | Slides 1-4 (Inicio, Escribir, Leer, Escuchar) | 380 | L1 | Landing |
| L3 | Slides 5-7, footer with placeholder privacy/terms links, CTAs from `VITE_APP_URL`, responsive, a11y | 380 | L2 | Landing |
| G1 | "Guardado en Erato" footer on anonymous public views | 120 | - | Footer |
| X1 | `PlanPolicy` port + `UnlimitedPlanPolicy` + `get_plan_policy` getter + entitlements endpoint + dependency-override contract test | 220 | - | Shared seam |
| V1 | Section revision counter, conditional save, 409 contract, snapshot repo, indexes | 380 | X1 | Versioning |
| V2 | History list/get/restore endpoints, retention, history gate through the port | 250 | V1 | Versioning |
| V3 | Dirty-section saves, `expected_rev`, `allSettled`, conflict dialog | 330 | V1 | Versioning |
| V4 | History panel | 280 | V2, V3 | Versioning |
| B1 | `bands` repo, band and composition indexes, invitation `target` index, migration script with backup | 330 | X1 | Bands chain |
| B2 | Band context in `composition_access`, `resolve_role` order, read-only in `require()` via the port, `list_by_user` | 350 | B1 | Bands chain |
| B3 | Core gate call sites: sharing with people, band creation, demo count quota (through the port) | 200 | B2 | Bands chain |
| B5 | Band CRUD, band invitations, atomic seat join with policy-supplied limit, atomic `add_member` | 380 | B3 | Bands chain |
| B6 | Transfer (lazy expiry, transfer hook) and leave band | 300 | B5 | Bands chain |
| B7 | Share composition with band (`band_id`, `band_editable`, members from band) | 220 | B5 | Bands chain |
| FX | Frontend extension point for cloud pages (option A or B from Approach 7) | 150-300 | X1, design decision | Bands chain |
| F2 | Band management screen | 380 | B6 | Bands chain |
| F3 | `SharingModal.vue`, dashboard, read-only banner (gating from the entitlements endpoint) | 350 | B7 | Bands chain |

Public subtotal ~5.500 lines.

### Private `erato-cloud` units (`repo: erato-cloud`, PRs into `erato-cloud` `preview`)

| Unit | Content | Est. lines | Depends on | Track |
| --- | --- | --- | --- | --- |
| C0 | Bootstrap: `erato` as git submodule (tracking `erato` `preview`), `api/index.py` importing `app.main.app` and applying routers/overrides, `vercel.json`, CI (recursive submodule checkout, Mongo service), `.env.example` with variable ownership, preview runbook (Vercel project, env vars, Deployment Protection, pointer check), cloud `ensure_indexes` entry point | 250 | Author prerequisites; X1 merged in `erato` `preview` | Cloud bootstrap |
| C1 | `subscriptions` repository and indexes (D4), tests | 250 | C0 | Cloud plans chain |
| C2 | `SubscriptionPlanPolicy` (seats 8 + `extra_seats`, quotas, read-only when unpaid, band creation requires Pro Banda, sharing/history gates) wired via `dependency_overrides`, tests | 330 | C1, B3 | Cloud plans chain |
| C3 | Billing/grant port, free provider, `FREE_PRO_ENABLED` kill switch, `VERCEL_ENV=production` guard, activate/cancel/seats endpoints | 300 | C2 | Cloud plans chain |
| C4 | Subscription side of ownership transfer (transfer hook implementation) | 150 | C3, B6 | Cloud plans chain |
| C5 | Plan page and activation UI through the extension point | 320 | C3, FX | Cloud plans chain |

Cloud subtotal ~1.600 lines. Total ~7.100 lines (higher than the previous ~5.900 because of the seams, the cloud bootstrap and the duplicated CI/runbook).

**Dependency order and tracks**: independent tracks in `erato` are Preview config (PV1), Landing (L1-L3), Footer (G1) and Versioning (X1 -> V1-V4). The bands chain is X1 -> B1 -> B2 -> B3 -> B5 -> {B6, B7} -> {F2, F3}, with FX after X1 and the design decision. In `erato-cloud`: C0 -> C1 -> C2 -> C3 -> {C4, C5}. Cross-repo rule: each C-unit that needs a core change starts only after that `erato` unit is merged into `erato` `preview`, and bumps the submodule pointer in the same PR. All units fit the 400-line budget; FX is the one whose size depends on the design decision (option A refactors `frontend/src/main.ts` and the router into a factory).

## Dependencies

- D1-D4 approved and P1-P20 resolved (2026-10-03): no remaining approval blocks the proposal.
- Design decision on the frontend extension point (Approach 7) before FX and C5.
- Vercel: a project for `landing/` (from `erato`) and a project for app + API (from `erato-cloud`), Preview env vars scoped to each repo's `preview` branch, Deployment Protection setting (P8).
- Atlas M0 reachable from preview deployments (IP access list already covers Vercel).
- `erato-cloud` CI able to check out the public submodule (public repo, so no extra credentials expected) and to run a Mongo service.

## Prerequisites owned by the author (blocking only the C-units)

- Create the private GitHub repository `erato-cloud` and its local folder (suggested `/home/bspc/proyectos/erato-cloud`), with a `preview` branch.
- Create the Vercel project for `erato-cloud` (app + API) and set its Preview-scoped secrets and env vars (`MONGODB_URI`, `MONGODB_DB`, `JWT_SECRET`, Cloudinary credentials and prefix, `APP_BASE_URL`, `FREE_PRO_ENABLED`).
- Set the GitHub Actions secrets the `erato-cloud` CI needs, if any.
- sdd-apply for C-units needs that folder to exist and an explicit user grant of edit scope over it (it is outside this repo); public units need no extra scope.

## Open items owned by the author (not blocking this change)

- Accountant / tax obligations (SII, company or not) before the first real charge; this decides Flow vs Mercado Pago.
- Domains for the landing and the app.
- Privacy policy and terms texts (the landing links are placeholders until then; required before any public launch).
- At promotion time: disconnect or keep the existing Vercel project that deploys `erato` `main`.
- README "Mi rol en el proyecto" update after delivery (mentioning the public/private split); license and contact details.

## Success Criteria

- [ ] Landing deployed as its own Vercel preview from `erato`, all 7 slides, keyboard and wheel navigation, reduced motion respected, CTAs reach the app's register/login, privacy/terms links present as placeholders, both themes pass 4.5:1 contrast.
- [ ] The full preview (app + API) is deployed from `erato-cloud` `preview`, with the submodule pointer equal to `erato` `preview` HEAD.
- [ ] No subscription, billing or plan-quota logic exists in the public `erato` repo; `erato` alone runs with `UnlimitedPlanPolicy` and all features available (self-hosted behavior), verified by its test suite.
- [ ] Two users editing the same section: the second save gets a 409 and the conflict dialog; no silent overwrite.
- [ ] Pro users can list and restore up to the retention cap of lyrics, chords and tablature versions; Free users cannot see history.
- [ ] In preview, a registered user self-activates Pro Individual or Pro Banda; with `FREE_PRO_ENABLED` unset, activation is refused and free subscriptions are not honored.
- [ ] A Pro Banda owner creates a band, invites members up to the seat limit (the next join is rejected, including under concurrent joins), shares compositions with the band, transfers ownership (expires after 14 days) and members can leave with detachment.
- [ ] Band content becomes read-only when the band subscription is not active; all permission checks are enforced in the backend.
- [ ] Free and Pro Individual cannot share with people; the public read-only link works on every plan, anonymously, with the "Guardado en Erato" footer.
- [ ] Production deployment (the existing Vercel project for `erato` `main`) and production DB unchanged; root `vercel.json` of `erato` and its test unchanged.
- [ ] Backend and frontend test suites, `vue-tsc` and builds pass for `erato` (app and landing) and for `erato-cloud` (including its CI against the pinned submodule).
