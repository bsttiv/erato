# Design: Initial Architecture for Erato

> **Scope note.** This document designs the *shape* of the system: module boundaries, request
> lifecycle, permission enforcement points, connection management, and the structure of the Vue port.
> It contains **no application code**. The MongoDB schema was deferred during initial design per
> `AGENTS.md` rule 1, and has since been presented to and **explicitly approved by the author**; see
> `## Approved Data Model` below. `db/repositories/` may now be implemented against that schema.

Upstream artifact: `openspec/changes/erato-arquitectura-inicial/proposal.md` (Engram
`sdd/erato-arquitectura-inicial/proposal`). Decisions 1–4 confirmed by the author
(Engram `erato/constraints/architecture-confirmed`); decision 5 locked earlier
(Engram `erato/constraints/design-system-integration`).

---

## Technical Approach

Erato is a **single-origin web application**: one Vercel project serves the Vue 3 SPA as static
assets and a single Python ASGI function under `/api/*`. One origin removes CORS entirely, lets the
refresh-token cookie be `SameSite=Lax`, and — more importantly for the free tier — concentrates all
backend traffic into **one** function, so there is one cold start to amortize and one MongoDB client
per warm instance instead of one per endpoint.

The backend is layered so the parts most likely to change are the parts most isolated:

```
  routers/      HTTP shape only — parse, delegate, serialize
  deps.py       identity + authorization resolution (the security boundary)
  services/     business rules, framework-agnostic
  db/repositories/  the only code that knows Mongo exists
  db/client.py  one lazily-created, loop-guarded AsyncMongoClient per warm instance
```

That layering directly serves the proposal's rollback plan: swapping FastAPI for Flask touches
`routers/`, `deps.py`, and `main.py`; swapping Cloudinary touches one module; and the still-unapproved
schema is confined entirely behind `db/repositories/`.

Authorization is **not** middleware. It is a FastAPI dependency chain parameterised by the action
being attempted, mounted on every route that touches a composition. Because all composition content
(chords, tabs, lyrics, demos, comments, tasks) lives under `/api/compositions/{composition_id}/...`,
a single dependency enforces `AGENTS.md`'s "los permisos se validan en el backend en cada petición"
for every child resource without per-endpoint re-implementation.

The frontend reimplements the design system in Vue 3 while **reusing `tokens.css` and
`components/bundle.css` byte-for-byte**. The Vue components emit the same `er-*` class names and the
same DOM structure as the React originals, so the stylesheet is the shared contract and visual drift
becomes a testable property rather than a judgement call.

Every free-tier limit named in the proposal is treated as a design input, not a footnote. Each
decision below states which limit it interacts with.

---

## Architecture Decisions

### Decision: One ASGI function for the whole API

**Choice**: A single Vercel Python function at `api/index.py` that re-exports the FastAPI app
(`from app.main import app`), with `vercel.json` rewriting `/api/(.*)` to it and everything else to
the SPA's `index.html`.

**Alternatives considered**: One Python file per endpoint or per resource (Vercel's file-based
convention); a separate Vercel project for the backend.

**Rationale**: Each distinct function is an independently cold-starting instance with its own
process, which means its own MongoDB client and its own pool. Atlas M0 caps at **500 connections**;
multiplying functions multiplies pools against that cap for no benefit at a band's traffic level.
One function also keeps the **50MB compressed bundle** accounting simple (one dependency set, not N)
and preserves single-origin, which the cookie strategy below depends on. A separate backend project
would reintroduce CORS and cross-site cookies for nothing.

### Decision: Authorization as a parameterised dependency, not middleware

**Choice**: `deps.py` exposes `require(action)` — a dependency factory returning a dependency that
(1) resolves optional identity from the `Authorization` header, (2) loads the target composition's
access record once and caches it on `request.state`, (3) computes the caller's effective role, and
(4) authorizes or rejects. Routes declare their requirement:
`Depends(require(Action.EDIT))`. Nested routes inherit it from the `/compositions/{composition_id}`
router prefix.

**Alternatives considered**: ASGI middleware doing path-pattern matching; an explicit
`check_permission(...)` call at the top of every handler.

**Rationale**: Middleware runs before routing, so it would have to re-parse paths to learn which
composition is targeted — a parallel, drift-prone router. Per-handler calls are the status quo that
`AGENTS.md` warns about: the one handler someone forgets is the vulnerability. A dependency declared
on the router prefix is enforced by FastAPI's own resolution, is visible in the OpenAPI output, and
is the single place a test can target. Dependency resolution also costs one Mongo read per request,
which matters against the **10s execution cap** and M0's ~100 ops/sec.

### Decision: `404` for unauthorized access to private compositions, `403` for insufficient rights

**Choice**: If the caller cannot *view* a composition, the API returns `404 Not Found`. If the caller
can view but not perform the requested action, it returns `403 Forbidden`.

**Alternatives considered**: Always `403`; always `404`.

**Rationale**: `AGENTS.md` states a private composition's link "no da acceso a nadie más". A `403`
confirms the composition exists, turning the share URL into an existence oracle that leaks the
band's private catalogue to anyone probing identifiers. `404` for the no-view case closes that.
`403` remains correct and more useful for the public-but-not-invited case, where existence is
already public by design.

### Decision: Composition share URLs use an unguessable slug, not the Mongo identifier

**Choice**: The user-facing share URL is keyed by a random 128-bit URL-safe slug, decoupled from the
internal document identifier. Internal API paths may use either; the slug is what is pasted into a
chat.

**Alternatives considered**: Exposing the Mongo `ObjectId` directly in share links.

**Rationale**: `ObjectId` embeds a timestamp and a monotonic counter, so it is partially predictable
and enumerable. For public compositions the content is meant to be readable by anyone *with the
link*, not crawlable by anyone who can increment a counter. A random slug preserves "unlisted but
shareable" semantics. (The storage of this slug is a schema concern and is routed to the schema
approval gate; this design only fixes that it must be random, not derived.)

### Decision: MongoDB access via `pymongo.AsyncMongoClient`, not Motor

**Choice**: Use PyMongo's native async API (`AsyncMongoClient`, PyMongo ≥ 4.9).

**Alternatives considered**: Motor; synchronous `MongoClient` behind FastAPI's threadpool.

**Rationale**: Motor is deprecated in favour of PyMongo's built-in async driver and is in sunset,
so adopting it now would plan a migration into a project that has not shipped yet. Synchronous
PyMongo would work but pushes every query onto FastAPI's threadpool, adding threads to a function
whose whole workload is I/O waiting — exactly the shape async suits, and the shape the **10s cap**
rewards. Driver choice is confined to `db/client.py` and `db/repositories/` either way.

### Decision: Module-level lazy client singleton with an event-loop guard

**Choice**: `db/client.py` holds a module-global client created on first use, never closed by a
request handler, and guarded by a check that the currently running event loop is the one the client
was created on; if the loop identity changed, the stale client is discarded and a new one is built.

**Alternatives considered**: Creating a client per request and closing it in a `finally`; creating
the client eagerly at import time; FastAPI `lifespan` startup/shutdown hooks only.

**Rationale**: Per-request clients are the classic serverless failure mode — every invocation opens
a new pool and M0's **500-connection cap** is reached by a handful of concurrent instances. Eager
creation at import adds connection setup to every cold start even for requests that never touch the
database (health checks, token refresh on a cached key). `lifespan` alone is insufficient because a
serverless instance can be frozen and thawed without re-running startup. The loop guard addresses a
real async-driver hazard: an async client binds to the loop it was created on, and a runtime that
creates a fresh loop per invocation would otherwise leave the singleton bound to a dead loop and
every query would hang until the 10s cap killed it.

**Pool parameters and the limits they respect:**

| Setting | Value | Limit it protects |
|---|---|---|
| `maxPoolSize` | 5 | Atlas M0 **500 connections**: 500 ÷ 5 ≈ 100 concurrent warm instances before exhaustion |
| `minPoolSize` | 0 | Avoids holding sockets open on an instance that is idle but not yet recycled |
| `maxIdleTimeMS` | 30000 | Reclaims sockets a thawed instance would otherwise find dead |
| `serverSelectionTimeoutMS` | 3000 | Fails fast with a clean `503` well inside the **10s execution cap** instead of being killed by Vercel |
| `connectTimeoutMS` / `socketTimeoutMS` | 3000 / 5000 | Same: bounded failure inside the wall clock |
| `retryWrites` | true (Atlas default) | Survives M0 primary step-downs without surfacing an error |

### Decision: Argon2id for password hashing, via `argon2-cffi`

**Choice**: Argon2id with explicitly pinned parameters sized to a predictable latency budget
(time cost 2, memory 19 MiB, parallelism 1 — the OWASP minimum configuration), through
`argon2-cffi`'s `PasswordHasher`, including its `check_needs_rehash` upgrade path. No `passlib`.

**Alternatives considered**: bcrypt at cost 12; `passlib` as an abstraction over either; PBKDF2 from
the standard library.

**Rationale**: Argon2id is the current first-choice recommendation for new applications, is
memory-hard (bcrypt is not), and avoids bcrypt's silent truncation of passwords past 72 bytes — a
footgun in a self-rolled auth system the author owns end to end. Its cost is *explicitly tunable*,
which matters here more than usual: login must complete a hash **plus** a Mongo round trip inside
the **10s cap**, and the 19 MiB memory cost is trivial against the function's memory allocation.
PBKDF2 is the weakest of the three against GPU attack. `passlib` is in low maintenance and has a
known incompatibility with modern `bcrypt` releases; depending on it adds a layer and a bug class
for no benefit when both candidate libraries expose a two-function API.

*Fallback if Argon2 wheels prove unavailable for Vercel's Python runtime at implementation time*:
`bcrypt` 4.x at cost 12, with explicit length validation to neutralise the 72-byte truncation. This
is a build-environment contingency, not an open design question.

### Decision: Short-lived stateless access token + rotating opaque refresh token

**Choice**:

| Token | Form | Lifetime | Transport | Storage |
|---|---|---|---|---|
| Access | JWT, HS256, signed with `JWT_SECRET` | 15 minutes | `Authorization: Bearer` | Client memory only (never `localStorage`) |
| Refresh | Opaque 256-bit random, URL-safe | 30 days, rotated on every use | `HttpOnly; Secure; SameSite=Lax` cookie scoped to `/api/auth` | Server stores only a SHA-256 digest |

Access-token claims: subject (user id), issued-at, expiry, a token version for global revocation,
and nothing else — no roles, no composition permissions. Refresh rotation is single-use: redeeming a
refresh token issues a new one and invalidates the old; presenting an already-redeemed token
invalidates the whole token family, which is the standard reuse-detection response to a stolen
cookie.

**Alternatives considered**: Long-lived access tokens with no refresh; server-side sessions; storing
tokens in `localStorage`; RS256.

**Rationale**: Stateless HS256 verification needs no database round trip, so the overwhelmingly
common case — an authenticated read — costs zero extra Atlas operations against M0's ~100 ops/sec
and nothing against the **10s cap**. HS256 avoids pulling the `cryptography` package in, keeping the
**50MB bundle** lean; asymmetric signing buys nothing when one service both issues and verifies.
Server-side sessions would add a database read to *every* request, the opposite trade. Keeping the
access token in memory and the refresh token in an `HttpOnly` cookie means an XSS payload cannot
exfiltrate a long-lived credential; the 15-minute window bounds the damage of the short-lived one.
Single-origin deployment is what makes `SameSite=Lax` sufficient — no cross-site cookie, no
`SameSite=None`.

**Critically — permissions are never carried in the token.** Roles are resolved per request from
stored state (see the permission model), so revoking an invitation takes effect immediately rather
than at the next token expiry.

**Persistence requirement routed to the schema gate**: refresh-token digests must be storable with
an expiry, a family identifier, and a revoked flag, and must support TTL-based expiry so dead
records do not accumulate against the **512MB storage cap**. The document shape is not designed here.

### Decision: Invite tokens are single-use, expiring, and bind an account — not a capability URL

**Choice**: An invite is an opaque 256-bit random token, stored as a SHA-256 digest with an expiry
(default 14 days) and the composition and inviter it belongs to. Redeeming it **requires an
authenticated account**: an unauthenticated visitor following an invite link is sent to
register/login first and the token is replayed afterwards. Redemption grants the `editor` role on
exactly one composition and consumes the token.

**Alternatives considered**: Bearer-style capability links that grant edit rights to whoever holds
them, with no account; multi-use invite links; signed JWT invites with no server record.

**Rationale**: `AGENTS.md` is specific: edit rights belong to *invited users*, and a public link is
view-only "incluso sin cuenta". A capability link that grants editing to anyone holding it would
collapse those two cases — forwarding the link would silently grant write access, and there would be
no identity to attribute an edit to, which a collaborative songwriting tool needs. A stateless signed
JWT invite cannot be revoked before expiry and cannot be made single-use. Hashing the token at rest
means a database leak does not yield usable invites.

**Persistence requirement routed to the schema gate**: invite digests and composition membership
(which account holds which role on which composition) must be storable and queryable by composition.
Shape deferred.

### Decision: Direct-to-Cloudinary signed upload, with server-side verification of the result

**Choice**: The browser uploads the audio file straight to Cloudinary using an upload signature
minted by the backend; the backend never touches the file bytes. The browser then reports the
Cloudinary result back to the backend, which **verifies Cloudinary's response signature** and the
`public_id` prefix before recording the reference.

**Alternatives considered**: Proxying the upload through a Vercel function; an unsigned upload preset;
trusting the client-reported URL without verification.

**Rationale**: Proxying is excluded by the **10s execution cap** — a multi-megabyte demo over a slow
connection will not reliably complete inside it, and the bytes would also consume Vercel bandwidth
for no benefit. An unsigned preset would let anyone on the internet upload into the band's
Cloudinary account and burn the **25 monthly credits**. Trusting the client-reported URL is the
subtle one: without verification, an attacker with edit rights (or a tampered client) could register
*any* URL as a demo, turning the composition into an arbitrary-content host. Cloudinary returns a
signature over the upload result; re-computing it server-side with the API secret proves the asset
was really created by this account under the folder the backend authorised.

### Decision: Private compositions use authenticated Cloudinary delivery, not public URLs

**Choice**: Audio uploaded for a composition is stored with authenticated delivery. The backend mints
a short-lived signed delivery URL only after passing the same `require(Action.VIEW)` check used for
the rest of the composition.

**Alternatives considered**: Public delivery URLs for everything, relying on the slug being
unguessable.

**Rationale**: Without this, a private composition's audio would be reachable by anyone holding the
raw Cloudinary URL, bypassing the backend entirely — a direct contradiction of `AGENTS.md`'s
requirement that permissions are validated in the backend on every request, since the backend is not
in the request path at all. Signed delivery URLs cost no extra credits (bandwidth is charged either
way). **Open question**: the exact availability and naming of authenticated delivery on Cloudinary's
current free plan must be verified at implementation time; see Open Questions.

### Decision: No Cloudinary transformations; the waveform is synthetic

**Choice**: Store and serve the original audio with no eager and no on-the-fly transformations.
The `DemoPlayer` waveform is generated client-side from a deterministic seeded PRNG keyed on the
take's identifier.

**Alternatives considered**: Cloudinary audio transcoding to a uniform format; server-side or
Cloudinary-side waveform extraction.

**Rationale**: Cloudinary's free plan pools storage, bandwidth, and transformations into the same
**25 credits/month** (≈1 credit per GB stored, per GB delivered, or per 1,000 transformations), so
transformations spend the storage budget. Reading the reference implementation settled the waveform
question outright: `peaks()` in `erato-design-system/components/bundle.js:343-347` is a seeded
linear-congruential generator shaped by a sine envelope — it is **not** derived from the audio at
all. The visual the design system specifies therefore needs no audio analysis, no transformation
credits, and no work inside the 10s cap. Porting it faithfully means porting the PRNG, including its
exact constants, or the bars change shape.

### Decision: Reuse the design system's CSS unchanged; port only behavior to Vue

**Choice**: The Vue app loads `erato-design-system/tokens.css` and
`erato-design-system/components/bundle.css` unmodified (via a Vite path alias, not a copy), and every
ported component emits the same `er-*` class names and the same DOM structure as its React
counterpart. `bundle.js` is not shipped and React is not a dependency.

**Alternatives considered**: Re-authoring the styles as scoped Vue SFC `<style>` blocks; copying the
CSS into the frontend tree; CSS Modules.

**Rationale**: Verified by reading the files: `bundle.css` is plain CSS keyed entirely on `er-*`
classes and CSS custom properties, with one Google Fonts `@import`, and `tokens.css` switches themes
via `[data-theme="matine"]` on an ancestor element. Nothing in either file knows React exists, so
both are directly reusable. Re-authoring styles would duplicate every token, guarantee drift from the
reference, and violate `AGENTS.md`'s prohibition on inventing colours, radii, and type. Keeping the
CSS as the shared contract turns "does the Vue port match the design system" into a mechanical
check — same classes, same structure, same stylesheet — instead of a visual judgement. Aliasing
rather than copying means the design system stays the single source of truth and an update to it is
not a manual sync.

### Decision: Vue components adopt `v-model`, not React's `default*` + `onChange` shape

**Choice**: Where `index.d.ts` declares an uncontrolled React prop pair (`defaultFrets` + `onChange`,
`defaultItems` + `onChange`, `defaultValue` + `onChange`), the Vue component exposes
`v-model`-compatible props and emits. Prop *names* are otherwise preserved for traceability back to
the reference.

**Alternatives considered**: Mirroring the React prop API exactly in Vue.

**Rationale**: The locked decision is to reimplement, and `AGENTS.md`'s requirement is that the
components match "exactamente su aspecto y comportamiento" — appearance and behavior, not prop
signatures. Transplanting React's uncontrolled/controlled duality into Vue produces components that
fight the framework every consumer in the app expects. Keeping names otherwise aligned preserves the
mapping back to `index.d.ts` for review.

### Decision: One ASGI application object for both local Docker and Vercel

**Choice**: `app/main.py` defines the FastAPI instance. Locally, `uvicorn app.main:app --reload` runs
it in a container; on Vercel, `api/index.py` imports the same object. The only environment-dependent
value is `MONGODB_URI` (plus secrets), read through `pydantic-settings`.

**Alternatives considered**: A separate local entrypoint with its own wiring; emulating Vercel
locally via `vercel dev`.

**Rationale**: `AGENTS.md` requires `docker compose up` to be sufficient for local work, and the
cheapest way to make local behaviour predict production behaviour is for there to be exactly one
application object and exactly one place where the environment differs. `vercel dev` would couple
local development to a vendor CLI and still would not give the Mongo container the compose file
provides. The risk this accepts — that Vercel's handler wrapper behaves differently from uvicorn in
some edge case — is bounded to the cold-start/loop concern already handled by the client loop guard.

---

## Permission Model

Three roles, resolved per request against stored state (never read from a token claim):

| Role | How it is obtained |
|---|---|
| `owner` | Created the composition |
| `editor` | Redeemed an invite for this composition |
| `viewer` | Anonymous or authenticated caller, **only** when the composition's visibility is `public` |

| Action | `owner` | `editor` | `viewer` | no access |
|---|---|---|---|---|
| `view` (composition + all sections, demos, comments) | yes | yes | yes | `404` |
| `edit` (sections, demos, tasks, comments) | yes | yes | `403` | `404` |
| `manage_sharing` (visibility, invites, revoke) | yes | `403` | `403` | `404` |
| `delete` composition | yes | `403` | `403` | `404` |

Two rules make this enforceable rather than aspirational:

1. **Every content route is nested under `/api/compositions/{composition_id}`.** A demo comment is
   `POST /api/compositions/{id}/demos/{demo_id}/comments`, not `POST /api/comments`. There is no
   route that touches composition content without a composition identifier in its path, so there is
   no route the dependency cannot cover.
2. **The access record is loaded once per request** and cached on `request.state`, so nesting does
   not multiply Atlas operations.

---

## Data Flow

### Authenticated request with permission resolution

```
  Vue SPA                  Vercel /api/*              deps.py               Atlas M0
     │                           │                       │                      │
     │ GET /compositions/{id}    │                       │                      │
     │ Authorization: Bearer ──► │                       │                      │
     │                           │ ── resolve identity ─►│                      │
     │                           │                       │ verify JWT (no I/O)  │
     │                           │                       │ ── load access ─────►│
     │                           │                       │ ◄─── visibility, ────┤
     │                           │                       │      members         │
     │                           │                       │ compute role         │
     │                           │                       │ authorize(VIEW)      │
     │                           │ ◄── request.state ────┤                      │
     │                           │ ── router/service ───────── repositories ───►│
     │ ◄──── 200 / 403 / 404 ────┤                       │                      │
```

### Public link, no account

```
  Visitor ── GET /c/{slug} ──► SPA ── GET /api/compositions/by-slug/{slug} ──► deps.py
                                                                                 │
                                        no Authorization header → identity=None  │
                                        load access by slug ────────────────────►│ Atlas
                                        visibility == public → role = viewer     │
                                        authorize(VIEW) → ok                     │
                                        any write attempt → 403                  │
                                        visibility == private → 404              │
```

### Invite redemption

```
  Owner                    Backend                      Invitee
    │ POST /compositions/{id}/invites                      │
    │   (require manage_sharing) ──►│                      │
    │                               │ mint 256-bit token   │
    │                               │ store SHA-256 digest │
    │ ◄── invite URL (token once) ──┤                      │
    │ ─────────── sends link out of band ─────────────────►│
    │                               │ ◄── GET /invite/{t} ─┤
    │                               │  not authenticated?  │
    │                               │  → register / login, │
    │                               │    then replay       │
    │                               │ ◄─ POST redeem ──────┤
    │                               │ hash, look up, check │
    │                               │ expiry + unconsumed  │
    │                               │ grant editor role    │
    │                               │ consume token        │
    │                               │ ──── 200 ───────────►│
```

### Audio upload — direct to Cloudinary

```
  Vue             Backend (/api)                 Cloudinary
   │ 1. POST /compositions/{id}/demos/upload-signature
   │    { filename, contentType, bytes }  ──►│
   │                                         │ require(EDIT)
   │                                         │ reject oversize / wrong type
   │                                         │ build params: timestamp,
   │                                         │   folder=erato/compositions/{id},
   │                                         │   resource_type=video,
   │                                         │   tag=pending, authenticated type
   │                                         │ sign with API_SECRET  ← never leaves server
   │ ◄── { signature, timestamp, api_key, cloud_name, folder, public_id } ─┤
   │                                                                        │
   │ 2. POST file + signed params directly ───────────────────────────────►│
   │    (bypasses Vercel entirely — no 10s cap, no Vercel bandwidth)       │
   │ ◄── { public_id, version, secure_url, duration, bytes, signature } ───┤
   │                                         │                              │
   │ 3. POST /compositions/{id}/demos  ─────►│                              │
   │    { cloudinary result }                │ require(EDIT)                │
   │                                         │ recompute response signature │
   │                                         │   with API_SECRET → must match
   │                                         │ assert public_id starts with │
   │                                         │   the folder it signed       │
   │                                         │ remove 'pending' tag  ──────►│
   │                                         │ store reference (shape TBD)  │
   │ ◄──────────── 201 demo ─────────────────┤                              │
   │                                                                        │
   │ 4. Playback: GET /compositions/{id}/demos/{demo}/url                   │
   │    → require(VIEW) → mint short-lived signed delivery URL ────────────►│
```

**Orphan handling.** If step 3 never happens (tab closed, network drop), the asset sits in Cloudinary
consuming credits. Every upload is therefore tagged `pending` at signature time and untagged on
confirmation; a Vercel Cron job sweeps `pending` assets older than 24 hours. Vercel's Hobby plan
permits a small number of cron jobs at daily granularity, which is sufficient for a 24-hour sweep —
this is the only scheduled job in the system.

---

## File Changes

These are the structures the *implementation* changes will create. This change creates only its own
OpenSpec artifacts and the `openspec/config.yaml` update; no application code, no dependency
installation, no infrastructure config (per the proposal's Out of Scope).

### Backend

| File | Action | Description |
|---|---|---|
| `api/index.py` | Create | Vercel entrypoint; re-exports the FastAPI app. No logic. |
| `vercel.json` | Create | Rewrites `/api/(.*)` → `api/index.py`, all else → SPA; cron entry for the orphan sweep |
| `requirements.txt` | Create | `fastapi`, `pymongo[srv]`, `pydantic-settings`, `pyjwt`, `argon2-cffi`, `cloudinary`; kept minimal against the 50MB bundle cap |
| `app/main.py` | Create | FastAPI instance, router registration, exception handlers mapping domain errors to HTTP |
| `app/settings.py` | Create | `pydantic-settings` config; every secret from env, none defaulted in code (`AGENTS.md` rule 4) |
| `app/deps.py` | Create | `current_user_optional`, `current_user_required`, `composition_access`, `require(action)` |
| `app/core/permissions.py` | Create | `Role`, `Action`, `resolve_role()`, `can()` — pure, no FastAPI import, directly unit-testable |
| `app/core/errors.py` | Create | Domain error types and their HTTP mapping, including the 404-vs-403 rule |
| `app/core/security/passwords.py` | Create | Argon2id hash / verify / `needs_rehash`, parameters pinned in one place |
| `app/core/security/tokens.py` | Create | Access-JWT mint/verify; opaque refresh and invite token mint, digest, and verify |
| `app/core/security/cloudinary_sign.py` | Create | Upload-parameter signing, upload-response verification, signed delivery URL minting |
| `app/db/client.py` | Create | Lazy `AsyncMongoClient` singleton, loop guard, pool parameters |
| `app/db/repositories/*.py` | Create | `users`, `compositions`, `sections`, `demos`, `sharing` — **interfaces only until the schema is approved** |
| `app/services/*.py` | Create | Business rules, framework-agnostic, so a framework rollback stays confined |
| `app/schemas/*.py` | Create | Pydantic request/response models. These are the **API contract**, explicitly not the Mongo schema |
| `app/routers/health.py` | Create | `GET /api/health` — liveness without a database round trip |
| `app/routers/auth.py` | Create | register, login, refresh, logout, redeem-invite |
| `app/routers/compositions.py` | Create | Composition CRUD and `by-slug` lookup |
| `app/routers/sections.py` | Create | chords, tabs, lyrics, todos — all nested under a composition |
| `app/routers/demos.py` | Create | upload-signature, demo CRUD, timestamped comments, signed playback URL |
| `app/routers/sharing.py` | Create | visibility toggle, invite issue/list/revoke |
| `tests/` | Create | pytest suite; permissions and visibility are mandatory coverage per `AGENTS.md` |

### Frontend

| File | Action | Description |
|---|---|---|
| `frontend/index.html` | Create | Loads `tokens.css` then `bundle.css`, in that order; sets `data-theme` |
| `frontend/vite.config.ts` | Create | Alias to `erato-design-system/`; dev proxy `/api` → backend container |
| `frontend/src/design-system/core/*.ts` | Create | Ported pure logic — see the port table below |
| `frontend/src/design-system/composables/*.ts` | Create | Re-authored stateful behavior (tab keyboard, autoscroll, playback) |
| `frontend/src/design-system/components/Er*.vue` | Create | 1:1 with `erato-design-system/components/`, emitting identical `er-*` markup |
| `frontend/src/features/{auth,compositions,demos,sharing}/` | Create | Application features; design-system components stay presentational |
| `frontend/src/api/` | Create | Typed HTTP client; access token in memory, transparent refresh on 401 |
| `frontend/tests/` | Create | Vitest; chord detection and tab editing are mandatory coverage per `AGENTS.md` |

### Repository root

| File | Action | Description |
|---|---|---|
| `docker-compose.yml` | Create | mongo + backend + frontend (see below) |
| `backend/Dockerfile`, `frontend/Dockerfile` | Create | Local development images only; Vercel builds production itself |
| `.env.example` | Create | Documented, never populated (`AGENTS.md` rule 4) |
| `erato-design-system/**` | Read-only | Reference and runtime CSS source. Not modified. |
| `openspec/config.yaml` | Modify | Resolve `pending_decisions` 1, 3, 4, 5; fill test/build commands once runners exist |

---

## Design-System Port: Investigation Findings

The proposal flagged as pending verification whether `detectChord()` and `tabToText()` are separable
from the React shells. **They are.** Read directly from
`erato-design-system/components/bundle.js`:

| Finding | Evidence |
|---|---|
| `detectChord(notes)` is a **pure function** | `bundle.js:47-67`. Takes an array of numbers, returns a plain object. Calls no React API, touches no DOM, holds no state. |
| Its only dependencies are two constants and one helper | `NOTE` (`:35`), `QUAL` (`:36-43`), `key()` (`:44`) — all plain data and array sorting. |
| It already handles the hard cases `AGENTS.md` requires | `QUAL` covers `maj7`, `m7b5`, `9`, `13`, `6/9`, `7b9`, `7#9`, `maj7#11`, `aug7`; slash chords are produced at `:65` when the detected root differs from the bass; `:56` adds fifth-less variants of every four-note quality. |
| `tabToText(cols, names)` is a **pure function** | `bundle.js:222-231`. String and array manipulation only. No React, no DOM. |
| Neither is importable as a module | Both live inside an IIFE (`:2-437`) and are published only by assignment to `window.Erato` at `:433-436`. There is no `export`, no `module.exports`, no ESM build. |

**What this means concretely.** The algorithms do **not** need to be re-derived — that risk is
retired. But "reuse" here means **transcribing the source into a TypeScript module on the Vue side**,
not importing a package: reaching the existing function would require shipping the entire React
bundle and reading a global, which the locked decision rules out. Transcription of ~35 lines of
side-effect-free arithmetic is a mechanical task with an exact reference and exact expected outputs,
which is a different class of work from reimplementing chord recognition.

**Additional pure helpers found, also directly portable:**

| Helper | Location | Purpose |
|---|---|---|
| `TUNING`, `STR`, `fretsToMidi`, `autoBase` | `:115-117` | Guitar tuning, fret→MIDI conversion, base-fret auto-positioning |
| `WHITE`, `BLACK_AFTER` | `:152` | Piano keyboard layout |
| `EMPTY`, `blankTab`, `TECH` | `:219-220`, `:232` | Empty tab column, blank grid, the technique character set `hpbrs/\~xv` |
| `parseLine` | `:290-295` | Splits `[Am7]Bajo el farol…` into chord/syllable segments |
| `peaks` | `:343-347` | Deterministic seeded waveform. **Not derived from audio** — see the transformations decision |
| `fmt`, `pad2` | `:342`, `:95` | `mm:ss` formatting |
| `cx`, `PATHS` | `:10`, `:13-26` | Class joining; the 12 icon path definitions |

**What is genuinely entangled with React and must be re-authored:**

| Component | Entangled part | Why it cannot be copied |
|---|---|---|
| `TabEditor` | `onKey` (`:246-267`) | The keyboard state machine reads and writes `useState` tuples (`cols`, `sel`) and a `useRef` grid handle inline. The *rules* are clear and portable; the *plumbing* is hooks. Becomes `useTabKeyboard()`. |
| `ChordEditor` | `setInst` (`:194-201`) | Guitar→piano octave folding mutates two separate `useState` slots. Logic is ten lines; state wiring is React's. |
| `LyricsViewer` | `:301-318` | `requestAnimationFrame` autoscroll loop and Escape handler built on `useEffect` cleanup semantics. Becomes `useAutoScroll()` with `onScopeDispose`. |
| `DemoPlayer` | `:355-368` | Three interacting `useEffect`s coordinating an `<audio>` element, a fallback interval timer, and seek. Becomes `useTakePlayback()`. |
| `TodoList`, `SideNav`, `Segmented` | throughout | Thin; controlled/uncontrolled duality is the only React-specific part. |

**Styling is not entangled at all.** `bundle.css` is plain CSS keyed on `er-*` classes with one
Google Fonts `@import`; `tokens.css` defines custom properties under `:root, [data-theme="noche"]`
and `[data-theme="matine"]`. Both are consumed unchanged.

### Proposed Vue port structure

```
frontend/src/design-system/
├── core/                      # pure, framework-free, directly unit-testable
│   ├── chords.ts              # NOTE, QUAL, detectChord()        ← bundle.js:35-67
│   ├── guitar.ts              # TUNING, STR, fretsToMidi, autoBase ← :115-117
│   ├── piano.ts               # WHITE, BLACK_AFTER                ← :152
│   ├── tab.ts                 # EMPTY, blankTab, TECH, tabToText  ← :219-232
│   ├── lyrics.ts              # parseLine                         ← :290-295
│   ├── waveform.ts            # peaks (seeded PRNG, exact constants) ← :343-347
│   └── format.ts              # pad2, fmt, cx                     ← :95, :342, :10
├── composables/               # re-authored stateful behavior
│   ├── useTabKeyboard.ts      # ← onKey :246-267
│   ├── useAutoScroll.ts       # ← :301-318
│   └── useTakePlayback.ts     # ← :355-368
└── components/                # 1:1 with erato-design-system/components/
    ├── ErIcon.vue             ← Icon :27-32
    ├── ErButton.vue  ErTag.vue  ErSegmented.vue  ErSideNav.vue
    ├── ErChordEditor.vue      ← :182-216
    │   ├── ErFretboard.vue    ← Fretboard :119-150   (internal)
    │   ├── ErPiano.vue        ← Piano :153-173       (internal)
    │   └── ErChordName.vue    ← ChordName :175-180   (internal)
    ├── ErTabEditor.vue  ErLyricsViewer.vue  ErDemoPlayer.vue  ErTodoList.vue
    └── index.ts               # barrel; the app imports only from here
```

Three rules keep this honest:

1. **`core/` imports nothing from Vue.** It is the transcribed reference logic, and its tests compare
   against outputs taken from the original functions.
2. **`components/` define no colours, sizes, radii, or fonts.** They emit `er-*` classes and let
   `bundle.css` style them. Any CSS written in a Vue SFC is a design-system gap to be proposed to
   the author, per `AGENTS.md` rule 2.
3. **The DOM structure matches the reference.** `erato-design-system/components/*/preview.html` is
   the fixture for structural parity tests.

---

## Interfaces / Contracts

Conceptual shapes, in prose and signature form. No implementation.

**Permission core** (`app/core/permissions.py`) — pure, no framework import:
`Role` ∈ {`owner`, `editor`, `viewer`}; `Action` ∈ {`view`, `edit`, `manage_sharing`, `delete`};
`resolve_role(user_id | None, access_record) -> Role | None`;
`can(role | None, action) -> bool`.

**Request dependency** (`app/deps.py`): `require(action)` returns a dependency yielding an
authorization context (the caller's identity or `None`, the resolved role, and the cached access
record). It raises the domain errors that `app/core/errors.py` maps to `404`/`403` per the rule above.

**Mongo client** (`app/db/client.py`): `get_db()` returns the shared database handle, creating the
client on first use and rebuilding it if the running event loop has changed. No caller ever closes it.

**Repositories** (`app/db/repositories/*.py`): async functions taking and returning domain objects,
not raw documents. **Their signatures depend on the approved schema and are therefore not fixed
here** — only the boundary is: no module outside this package imports PyMongo.

**Cloudinary signing** (`app/core/security/cloudinary_sign.py`): one function to produce signed
upload parameters for a given composition and content type; one to verify a Cloudinary upload
response against the API secret and the authorised folder prefix; one to mint a short-lived signed
delivery URL.

**Token module** (`app/core/security/tokens.py`): access-token mint/verify (JWT, HS256); opaque
token mint returning the plaintext once and its digest for storage; digest comparison for refresh and
invite redemption.

**Frontend API client** (`frontend/src/api/`): holds the access token in a module-scoped variable,
attaches it as a bearer header, and on a `401` performs exactly one refresh attempt against
`/api/auth/refresh` (cookie-carried) before replaying the original request; a failed refresh clears
state and routes to login.

---

## Testing Strategy

Strict TDD is currently `false` (Engram `sdd/erato/testing-capabilities`) because no code and no test
runner exist. It becomes applicable once the runners below are configured, which is the first
implementation task.

| Layer | What to test | Approach |
|---|---|---|
| Unit (backend) | `resolve_role` / `can` over the full role × action × visibility matrix, including anonymous | pytest, pure functions, no I/O |
| Unit (backend) | Argon2id hash/verify round trip; `needs_rehash` on a parameter change; rejection of a tampered hash | pytest |
| Unit (backend) | Access-token expiry, tampered signature, wrong algorithm (`alg: none` rejection), token-version revocation | pytest |
| Unit (backend) | Invite token: expiry, single use, redemption by a second account fails, revoked token fails | pytest |
| Unit (backend) | Cloudinary response verification rejects a forged signature and a `public_id` outside the authorised folder | pytest with fixed fixtures |
| Integration (backend) | Every content route under `/api/compositions/{id}` returns `404` for a private composition to a non-member, `403` for a public composition's write attempt by a non-member, `200` for an editor | `httpx.ASGITransport` against the app, `mongodb-memory`-style local Mongo or the compose container |
| Integration (backend) | Refresh rotation: a reused refresh token invalidates the family | same |
| Integration (backend) | Mongo client is reused across sequential requests (one client instance, pool not re-created) | assert on the module singleton's identity |
| Unit (frontend) | `detectChord` against a table of expected outputs including `D/F#`, `Cmaj7`, `F#m7b5`, `D9`, fifth-less voicings, and the single-note case | Vitest, table-driven, outputs taken from the reference implementation |
| Unit (frontend) | `tabToText` column padding, bar lines, multi-character frets | Vitest, golden strings from the reference |
| Unit (frontend) | `useTabKeyboard`: arrow movement, `space` extends at the end, two-digit fret entry (`1`→`12`), technique characters, `|` inserts a bar, backspace/delete on a bar line | Vitest |
| Unit (frontend) | `parseLine` chord-over-syllable segmentation; `peaks` determinism for a given seed | Vitest |
| Component (frontend) | Each `Er*.vue` emits the same `er-*` classes and DOM structure as the matching `preview.html` | Vue Test Utils structural assertions against the design-system fixtures |
| Visual (frontend) | Each component renders correctly under both `data-theme="noche"` and `data-theme="matine"`; focus ring visible on every control; 4.5:1 text contrast | Manual checklist initially; automated contrast assertions where cheap |
| E2E (deferred) | Public link view without an account; invite redemption; upload a demo and play it back | Deferred to a later change — needs a deployed environment and real Cloudinary credentials |

---

## Threat Matrix

**N/A** — this design introduces no shell commands, no subprocesses, no version-control or PR
automation, no executable-file classification, and no process integration. The "routing" it defines
is HTTP request routing inside a single ASGI application, not command or repository-selector routing,
and its adversarial surface (authorization, token handling, upload verification) is covered
explicitly by the permission model, the auth decisions, and the integration tests above rather than
by this matrix.

---

## Local Development and Deployment Shape

### `docker compose up`

```
  ┌─ mongo ──────────────┐   mongo:7
  │  27017               │   named volume erato-mongo-data
  │  healthcheck: ping   │   local-only credentials from .env
  └──────────┬───────────┘
             │ depends_on: service_healthy
  ┌──────────▼───────────┐   python:3.12-slim
  │  backend             │   uvicorn app.main:app --reload --host 0.0.0.0
  │  8000                │   MONGODB_URI=mongodb://mongo:27017/erato
  │  volume: ./ (live)   │
  └──────────┬───────────┘
             │
  ┌──────────▼───────────┐   node:22-alpine
  │  frontend            │   vite dev --host
  │  5173  ← browser     │   proxy /api → http://backend:8000
  │  volume: ./frontend  │
  └──────────────────────┘
```

Four properties this shape is chosen for:

1. **The Vite proxy reproduces single-origin locally.** The browser sees one origin at
   `localhost:5173`, so the `SameSite=Lax` refresh cookie behaves exactly as it will on Vercel. A
   local setup with two origins would pass tests that production fails.
2. **Only `MONGODB_URI` differs between local and production.** Local points at the compose
   container; production points at the Atlas M0 SRV string. No other code path branches on
   environment. The same `app.main:app` object runs in both.
3. **Production does not use these containers.** Vercel builds the SPA and the Python function from
   the repository directly; the Dockerfiles exist for local reproducibility and portability, which
   is what `AGENTS.md` asks of them.
4. **Cloudinary is not containerized.** Local development uses the same free Cloudinary account with
   a `dev/` folder prefix rather than a mock, because the signed-upload handshake and the response
   verification are precisely the parts most likely to break and least useful to fake. Dev uploads
   share the production **25-credit** pool, so the folder prefix exists to make a dev sweep possible
   and the credit impact of a handful of test files is negligible.

### `.env.example` (documented, never populated)

`MONGODB_URI`, `MONGODB_DB`, `JWT_SECRET`, `ACCESS_TOKEN_TTL_MINUTES`, `REFRESH_TOKEN_TTL_DAYS`,
`INVITE_TOKEN_TTL_DAYS`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`,
`CLOUDINARY_FOLDER_PREFIX`, `APP_BASE_URL`. Per `AGENTS.md` rule 4, none of these is ever committed
with a value and none is defaulted in code.

---

## Free-Tier Interaction Summary

Every row is a limit a design choice above deliberately interacts with.

| Limit | Design choices that interact with it |
|---|---|
| Vercel Hobby **10s execution** | Single ASGI function (one cold start); direct-to-Cloudinary upload (bytes never traverse a function); `serverSelectionTimeoutMS=3000` (clean `503` before the cap); Argon2 parameters tuned to a bounded hash latency; stateless access tokens (no database round trip on the common path) |
| Vercel Hobby **50MB compressed bundle** | HS256 instead of RS256 (no `cryptography` dependency); no `passlib`; minimal `requirements.txt` |
| Vercel Hobby **cron frequency** | The orphan-asset sweep is daily, which a 24-hour `pending` window accommodates |
| Atlas M0 **500 connections** | One function instead of many; module-level client singleton; `maxPoolSize=5`; `minPoolSize=0`; `maxIdleTimeMS=30000`; handlers never close the client |
| Atlas M0 **512MB storage** | Audio never enters MongoDB; refresh-token and invite records require TTL expiry so dead auth state does not accumulate |
| Atlas M0 **~100 ops/sec** | One access-record read per request, cached on `request.state` for nested routes; no database read to verify an access token |
| Cloudinary **25 credits/month** | No eager or on-the-fly transformations; the waveform is a client-side seeded PRNG, not audio analysis; signed uploads prevent third-party uploads into the account; `pending`-tag sweep reclaims orphans; `dev/` folder prefix isolates local development |

---

## Approved Data Model

**Status: approved by the author on 2026-10-01**, per `AGENTS.md` rule 1. This section is the schema
`db/repositories/*.py` implements; it supersedes every "shape deferred" / "routed to the schema gate"
note elsewhere in this document.

**Modeling decision that shapes everything below**: the author expects **few demos per composition
(5–10)** but **potentially many comments per demo**. Demos are therefore embedded in the composition
document (small, bounded, rarely exceeds a few KB); comments are their own collection (unbounded
growth must never resize the composition document or risk the 16MB per-document limit).

### `users`

```json
{
  "_id": ObjectId,
  "email": "banda@ejemplo.com",
  "password_hash": "argon2id$...",
  "display_name": "Juani",
  "created_at": ISODate
}
```

Indexes: `email` unique.

### `compositions`

Central document. Optional sections (chords, tablature, lyrics, todos) are embedded — each is
single and bounded per composition. Demos are embedded for the same reason (capped at 5–10 per the
author's own estimate). Comments are **not** embedded here; see `composition_comments`.

```json
{
  "_id": ObjectId,
  "owner_id": ObjectId,
  "title": "Noche de jazz",
  "visibility": "public" | "private",
  "share_slug": "a1b2c3...9f",
  "chords": { "instrument": "guitar", "entries": [ { "bar": 1, "notes": [0, 4, 7], "name": "C" } ] },
  "tablature": { "strings": 6, "content": "..." },
  "lyrics": { "content": "[Am7]Bajo el farol...\n# Coro\n..." },
  "todos": [ { "text": "Grabar segunda voz", "done": false } ],
  "demos": [
    {
      "demo_id": "d1",
      "cloudinary_public_id": "erato/compositions/<id>/xyz",
      "title": "Toma 1",
      "duration_s": 182,
      "uploaded_by": ObjectId,
      "uploaded_at": ISODate
    }
  ],
  "members": [ { "user_id": ObjectId, "role": "editor" } ],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

Indexes: `owner_id`; `members.user_id`; `share_slug` unique, sparse (present only when
`visibility: "public"`).

This satisfies the permission model's access-record read in one query: `owner_id`, `members`, and
`visibility` are all on the document `deps.py` already loads once per request.

### `composition_comments`

Separate collection — this is where the author expects volume. Keeps unbounded comment growth off
the composition document entirely.

```json
{
  "_id": ObjectId,
  "composition_id": ObjectId,
  "demo_id": "d1",
  "author_id": ObjectId,
  "timestamp_s": 47.5,
  "text": "Acá entra la voz",
  "created_at": ISODate
}
```

Index: compound `{ composition_id: 1, demo_id: 1, created_at: 1 }` — lists a demo's comments in
order without loading the composition.

### `invitations`

```json
{
  "_id": ObjectId,
  "composition_id": ObjectId,
  "token_hash": "sha256:...",
  "invited_email": "amigo@ejemplo.com",
  "role": "editor",
  "expires_at": ISODate,
  "used_at": null,
  "created_by": ObjectId
}
```

Indexes: `token_hash` unique; `expires_at` as a **TTL index** — Mongo removes expired invitations on
its own, which is also what retires the "refresh-token digests must expire without accumulating"
requirement from the auth decision above: the same TTL-index pattern applies to the refresh-token
collection (`refresh_tokens`, same shape: `token_hash` unique, `family_id`, `revoked: bool`,
`expires_at` TTL).

### How this resolves prior open items

- `db/repositories/*.py` signatures are now fixed by the shapes above; the "interfaces only" note in
  `## File Changes` no longer applies — full implementations are in scope for `sdd-tasks`.
- The public share slug lives on `compositions.share_slug`, satisfying the "share URLs use an
  unguessable slug" decision's deferred storage shape.
- Invite and refresh-token persistence (deferred under "Invite tokens are single-use…" and "Short-lived
  stateless access token…") are resolved by `invitations` and the sibling `refresh_tokens` collection
  above, both TTL-indexed against the 512MB cap.

---

## Migration / Rollout

No migration. Nothing is deployed and no data exists. Rollout is the ordinary first-implementation
sequence, and the proposal's per-decision rollback plan remains valid unchanged — this design
strengthens two of its entries by confining the relevant code: business rules live in `services/`
(framework rollback), and Mongo access lives behind `db/repositories/` (schema and driver changes).

The schema approval gate that previously blocked `db/repositories/` is now cleared — see
`## Approved Data Model`. `sdd-tasks` may plan full repository implementations, not interfaces-only.

---

## Open Questions

- [ ] **Cloudinary authenticated delivery on the free plan.** The private-composition audio decision
      assumes signed/authenticated delivery URLs are available on the current free tier. Verify
      against Cloudinary's live documentation at implementation time. If unavailable, the fallback is
      an unguessable `public_id` plus accepting that a leaked direct URL bypasses the backend — which
      would need the author's explicit acceptance, since it weakens `AGENTS.md`'s backend-validation
      requirement.
- [ ] **Vercel Hobby cron allowance.** Confirm the current Hobby plan still permits at least one
      daily cron job for the orphan sweep. If not, the fallback is sweeping opportunistically on an
      authenticated request, which is less predictable but costs nothing.
- [ ] **Design-system consumption mechanism.** This design proposes a Vite path alias to
      `../erato-design-system/`. If the design system is later extracted to its own repository or
      package, that alias becomes a dependency. Confirm the monorepo layout is intended to persist.
- [ ] **Google Fonts dependency.** `bundle.css` imports three families from Google Fonts over the
      network. Acceptable for production; worth confirming whether offline local development matters
      enough to self-host them. Self-hosting would require modifying the design system, which needs
      the author's approval under `AGENTS.md` rule 2.
- [x] **Schema approval.** Resolved — see `## Approved Data Model`. Approved by the author on
      2026-10-01.
