# Tasks: Initial Architecture for Erato

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~2,600–3,400 (≈33 new modules + tests + config across backend and frontend) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 → PR 7 (see Suggested Work Units) |
| Delivery strategy | ask-on-risk |
| Chain strategy | **feature-branch-chain** — confirmed by the author on 2026-10-01 |

Decision needed before apply: Resolved
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

**Feature-branch-chain layout**: PR 1 (Backend skeleton) opens against a tracker branch
`feature/erato-arquitectura-inicial`. PRs 2–7 each target the immediately preceding PR's branch in
sequence (PR 2 → PR 1's branch, PR 3 → PR 2's branch, …, PR 7 → PR 6's branch). Only the tracker
branch merges into `main`, once all seven units have landed on it in order.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend skeleton: FastAPI app, settings, Mongo client, health endpoint, Docker Compose, test runner | PR 1 | `pytest tests/test_health.py tests/test_client.py` | `docker compose up` then `curl localhost:8000/api/health` | Revert deletes `app/`, `api/`, `vercel.json`, `requirements.txt`, `docker-compose.yml`, `backend/Dockerfile`; no other unit depends on behavior, only on the module layout existing |
| 2 | Auth: passwords, tokens, auth router, repositories for `users`/`refresh_tokens` | PR 2 | `pytest tests/test_passwords.py tests/test_tokens.py tests/test_auth_router.py` | `docker compose up` then `curl -X POST localhost:8000/api/auth/register` | Revert removes `app/core/security/*`, `app/routers/auth.py`, `app/db/repositories/users.py`, `app/db/repositories/refresh_tokens.py`; composition features (PR 3+) are not yet wired to depend on live auth state beyond the dependency interface added in PR 1 |
| 3 | Permissions + composition CRUD + sharing: `permissions.py`, `deps.py`, compositions/sections/sharing routers, `compositions`/`invitations` repositories | PR 3 | `pytest tests/test_permissions.py tests/test_compositions_router.py tests/test_sharing_router.py` | `docker compose up` then exercise `GET/POST /api/compositions` with a seeded user | Revert removes `app/core/permissions.py`, `app/deps.py`, `app/routers/compositions.py`, `app/routers/sections.py`, `app/routers/sharing.py`, `app/db/repositories/compositions.py`, `app/db/repositories/invitations.py` |
| 4 | Demos + comments + Cloudinary signing | PR 4 | `pytest tests/test_cloudinary_sign.py tests/test_demos_router.py` | `docker compose up` then request an upload signature for a seeded composition | Revert removes `app/core/security/cloudinary_sign.py`, `app/routers/demos.py`, `app/db/repositories/comments.py`, demo fields added to the compositions repository |
| 5 | Frontend skeleton + design-system `core/` (pure logic) + Vitest runner | PR 5 | `npm run test:unit -- core` | `npm run dev` then load the blank SPA shell at `localhost:5173` | Revert removes `frontend/` entirely; backend PRs are unaffected |
| 6 | Design-system `composables/` + `components/` (Vue port) | PR 6 | `npm run test:unit -- composables components` | `npm run dev` then render `ErChordEditor`, `ErTabEditor`, `ErLyricsViewer`, `ErDemoPlayer` against `preview.html` fixtures | Revert removes `frontend/src/design-system/composables/` and `components/`; `core/` (PR 5) stays intact and usable standalone |
| 7 | Feature screens wiring auth + compositions + demos + sharing to the API client | PR 7 | `npm run test:unit -- features` | `docker compose up` then a manual end-to-end pass: register, create composition, add chords, upload a demo, toggle visibility | Revert removes `frontend/src/features/` and `frontend/src/api/`; design-system components (PR 5–6) remain reusable without this wiring |

Resolved: the author chose to split (not `size:exception`) and selected **feature-branch-chain** as
the chain strategy. `sdd-apply` may proceed under this plan once launched — see the standing
apply-handoff note below.

**Note on `rules.tasks` from `openspec/config.yaml`**: "Keep tasks completable in one session (~400 lines authored)" is honored at the work-unit level above; individual checklist tasks below are intentionally smaller than a whole PR.

---

## Phase 0: Decision Record Updates (no code)

- [x] 0.1 Update `openspec/config.yaml` `pending_decisions` to remove the five now-resolved items (backend framework → FastAPI, MongoDB schema → approved in `design.md`, auth method → self-rolled email/password + JWT, demo storage → Cloudinary, design-system integration → Vue reimplementation).
- [x] 0.2 Set `rules.apply.tdd: true`, `rules.apply.test_command`, and `rules.verify.test_command` / `build_command` in `openspec/config.yaml` once the runners from Phase 1 and Phase 5 exist (`pytest` for backend, `npm run test:unit` / `npm run build` for frontend). This task has a dependency on 1.8 and 5.1 completing first — revisit at the end of PR 1 and PR 5.
- [x] 0.3 Update `AGENTS.md`'s stack table to record the confirmed backend framework (FastAPI) per the proposal's deferred "Affected Areas" entry.

---

## Phase 1: Backend Skeleton + Health + Docker (PR 1)

### Backend platform spec — structured response, env config, execution budget

- [x] 1.1 RED: Create `tests/test_health.py` asserting `GET /api/health` returns `200` with a structured JSON body and performs no database round trip (assert via a mock/stub that the Mongo client is never invoked).
- [x] 1.2 GREEN: Create `app/settings.py` with `pydantic-settings` reading `MONGODB_URI`, `MONGODB_DB`, `JWT_SECRET`, `ACCESS_TOKEN_TTL_MINUTES`, `REFRESH_TOKEN_TTL_DAYS`, `INVITE_TOKEN_TTL_DAYS`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_FOLDER_PREFIX`, `APP_BASE_URL` — no defaults for secrets (AGENTS.md rule 4).
- [x] 1.3 RED: Create `tests/test_settings.py` asserting a missing required environment variable raises a clear, structured startup error (scenario: "Missing required configuration fails fast").
- [x] 1.4 GREEN: Confirm 1.3 passes against `app/settings.py`.
- [x] 1.5 GREEN: Create `app/core/errors.py` with domain error types (`NotFoundError`, `ForbiddenError`, `ValidationError`, `InternalError`) and their HTTP status mapping, including the 404-vs-403 rule from `design.md`.
- [x] 1.6 GREEN: Create `app/main.py` — FastAPI instance, exception handlers registering `app/core/errors.py` mappings (structured error body, no stack trace/internal paths leaked), router registration placeholder.
- [x] 1.7 GREEN: Create `app/routers/health.py` with `GET /api/health`, registered in `app/main.py`. Run 1.1 to confirm GREEN.
- [x] 1.8 GREEN: Create `requirements.txt` with `fastapi`, `uvicorn`, `pymongo[srv]`, `pydantic-settings`, `pyjwt`, `argon2-cffi`, `cloudinary`, `pytest`, `pytest-asyncio`, `httpx` (test runner setup — this is the task that makes TDD applicable, per `design.md`'s Testing Strategy note).
- [x] 1.9 RED: Create `tests/test_unhandled_error.py` asserting an endpoint that raises an unexpected exception returns a structured 5xx body with no stack trace or internal exception message (scenario: "Unhandled server error does not leak internals").
- [x] 1.10 GREEN: Wire a catch-all exception handler in `app/main.py` for unhandled exceptions, mapping to `app/core/errors.py::InternalError`. Confirm 1.9 passes.

### Data persistence spec — client reuse, failure handling

- [x] 1.11 RED: Create `tests/test_client.py` asserting (a) calling `get_db()` twice within the same event loop returns the same client instance (warm reuse), and (b) calling it after simulating a changed/closed event loop rebuilds the client (cold-start / loop-guard behavior).
- [x] 1.12 GREEN: Create `app/db/client.py` — module-level lazy `AsyncMongoClient` singleton with event-loop identity guard, pool parameters from `design.md` (`maxPoolSize=5`, `minPoolSize=0`, `maxIdleTimeMS=30000`, `serverSelectionTimeoutMS=3000`, `connectTimeoutMS=3000`, `socketTimeoutMS=5000`, `retryWrites=true`). Confirm 1.11 passes.
- [x] 1.13 RED: Create `tests/test_client_failure.py` asserting a simulated connection failure (mock raising `ServerSelectionTimeoutError`) surfaces as a structured 5xx error from a handler, without leaking the raw PyMongo exception message.
- [x] 1.14 GREEN: Add failure handling in `app/db/client.py` / `app/core/errors.py` so repository-layer exceptions map to the structured 5xx. Confirm 1.13 passes.

### Docker / local dev

- [x] 1.15 Create `docker-compose.yml` with `mongo` (image `mongo:7`, named volume `erato-mongo-data`, healthcheck, local-only credentials from `.env`), `backend` (depends_on `mongo` with `service_healthy`, `uvicorn app.main:app --reload --host 0.0.0.0`, live volume mount), `frontend` (placeholder service, completed in Phase 5).
- [x] 1.16 Create `backend/Dockerfile` (`python:3.12-slim`, installs `requirements.txt`, runs uvicorn).
- [x] 1.17 Create `api/index.py` re-exporting `from app.main import app` (Vercel entrypoint, no logic).
- [x] 1.18 Create `vercel.json` rewriting `/api/(.*)` → `api/index.py`, all else → SPA `index.html`; include the cron entry for the orphan-asset sweep (daily, pointing at a not-yet-created `app/routers/maintenance.py` cron handler stub — implement the stub in this task as a thin `GET` returning `501 Not Implemented` with a comment noting Phase 4 implements the real sweep, to keep `vercel.json` valid without inventing untested behavior).
- [x] 1.19 Create `.env.example` listing all variables from 1.2, documented with comments, no values (AGENTS.md rule 4).
- [x] 1.20 Verify: `docker compose up` brings up `mongo` and `backend`; `curl localhost:8000/api/health` returns `200`.

---

## Phase 2: Authentication (PR 2)

### Password hashing

- [x] 2.1 RED: Create `tests/test_passwords.py` covering: hash/verify round trip; `needs_rehash` returns `True` after a parameter change; a tampered hash fails verification; plaintext password never appears in the returned hash string.
- [x] 2.2 GREEN: Create `app/core/security/passwords.py` using `argon2-cffi`'s `PasswordHasher` with pinned parameters (time cost 2, memory 19 MiB, parallelism 1) and `check_needs_rehash`. Confirm 2.1 passes.

### Tokens

- [x] 2.3 RED: Create `tests/test_tokens.py` covering: valid access-JWT mint/verify round trip; expired token rejected; tampered signature rejected; `alg: none` rejected; token-version mismatch rejected (global revocation); opaque refresh/invite token mint returns plaintext once plus a SHA-256 digest; digest comparison matches only the original plaintext.
- [x] 2.4 GREEN: Create `app/core/security/tokens.py` — access-JWT mint/verify (HS256, claims: subject, issued-at, expiry, token version, nothing else); opaque token mint (256-bit, URL-safe) returning plaintext + SHA-256 digest; digest verification helper. Confirm 2.3 passes.

### Repositories: users, refresh_tokens

- [x] 2.5 RED: Create `tests/test_users_repository.py` (against a test Mongo instance/container) covering: create user with unique email enforced; duplicate email raises a domain error; lookup by email; lookup by id.
- [x] 2.6 GREEN: Create `app/db/repositories/users.py` implementing the `users` collection per `design.md`'s Approved Data Model (`_id`, `email` unique index, `password_hash`, `display_name`, `created_at`). Confirm 2.5 passes.
- [x] 2.7 RED: Create `tests/test_refresh_tokens_repository.py` covering: store a token digest with `family_id`, `revoked`, `expires_at`; redeeming an unexpired, unrevoked token succeeds; redeeming an already-revoked token (reuse) invalidates the whole family; TTL index exists on `expires_at`.
- [x] 2.8 GREEN: Create `app/db/repositories/refresh_tokens.py` implementing the `refresh_tokens` collection (same shape as `invitations`: `token_hash` unique, `family_id`, `revoked: bool`, `expires_at` TTL index) per `design.md`. Confirm 2.7 passes.

### Auth router

- [x] 2.9 RED: Create `tests/test_auth_router.py` covering every authentication-spec scenario: successful registration; duplicate-email rejection; malformed email / weak password rejection; successful login issues JWT; login failure is generic (does not reveal which field was wrong); missing/expired/malformed JWT rejected with `401` on a protected test route; plaintext password never appears in a captured log line during registration/login.
- [x] 2.10 GREEN: Create `app/schemas/auth.py` — Pydantic request/response models for register, login, refresh, logout.
- [x] 2.11 GREEN: Create `app/services/auth_service.py` — framework-agnostic business rules: register (hash + persist), login (verify + mint access/refresh), refresh rotation (single-use, family invalidation on reuse), logout (revoke refresh family).
- [x] 2.12 GREEN: Create `app/routers/auth.py` — `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh` (reads/writes the `HttpOnly; Secure; SameSite=Lax` refresh cookie scoped to `/api/auth`), `POST /api/auth/logout`. Register in `app/main.py`. Confirm 2.9 passes.
- [x] 2.13 GREEN: Create `app/deps.py` (initial cut) — `current_user_optional`, `current_user_required` dependencies verifying the access JWT (no composition-access logic yet; that is Phase 3). Wire into 2.12's protected routes.
- [x] 2.14 Verify: `docker compose up`, then `curl -X POST localhost:8000/api/auth/register` and `curl -X POST localhost:8000/api/auth/login` succeed against the live Mongo container.


---

## Phase 3: Permissions + Composition CRUD + Sharing (PR 3)

### Permission core (pure, framework-free)

- [x] 3.1 RED: Create `tests/test_permissions.py` covering the full role × action × visibility matrix from `design.md`'s Permission Model table: `owner`/`editor`/`viewer`/no-access × `view`/`edit`/`manage_sharing`/`delete`, including the anonymous case and both `public`/`private` visibility.
- [x] 3.2 GREEN: Create `app/core/permissions.py` — `Role` enum (`owner`, `editor`, `viewer`), `Action` enum (`view`, `edit`, `manage_sharing`, `delete`), `resolve_role(user_id, access_record) -> Role | None`, `can(role, action) -> bool`. No FastAPI import. Confirm 3.1 passes.

### Repositories: compositions, invitations

- [x] 3.3 RED: Create `tests/test_compositions_repository.py` covering: create composition with owner; embed/update chords, tablature, lyrics, todos, demos sub-documents; `share_slug` unique+sparse index only set when `visibility: "public"`; lookup by `owner_id`, by `members.user_id`, by `share_slug`; add/remove a member with a role.
- [x] 3.4 GREEN: Create `app/db/repositories/compositions.py` implementing the `compositions` collection per the Approved Data Model (indexes: `owner_id`; `members.user_id`; `share_slug` unique sparse).
- [x] 3.5 RED: Create `tests/test_invitations_repository.py` covering: create invitation with `token_hash`, `expires_at` TTL, `used_at: null`; redemption marks `used_at` and is idempotent against replay; TTL index exists on `expires_at`.
- [x] 3.6 GREEN: Create `app/db/repositories/invitations.py` implementing the `invitations` collection per the Approved Data Model (indexes: `token_hash` unique; `expires_at` TTL).

### `deps.py` — authorization dependency chain

- [x] 3.7 RED: Create `tests/test_deps_require.py` covering: `require(Action.VIEW)` resolves identity, loads the access record once per request (assert single Mongo read via call-count spy), computes role, and authorizes/rejects per the matrix; a non-member on a private composition gets the domain error that maps to `404`; a viewer attempting `edit` gets the domain error that maps to `403`.
- [x] 3.8 GREEN: Extend `app/deps.py` with `composition_access` (loads+caches the access record on `request.state`) and `require(action)` dependency factory per `design.md`'s Interfaces section. Confirm 3.7 passes.
- [x] 3.9 RED: Create `tests/test_404_vs_403.py` asserting directly against the backend-platform and sharing-and-visibility spec scenarios: unauthorized read of a private resource → `404`; unauthorized mutation by a non-invited authenticated user on a public composition → `403`; a direct API request bypassing any frontend path is checked identically (call the router function directly with no UI context).
- [x] 3.10 GREEN: Confirm 3.9 passes against `app/deps.py` / `app/core/errors.py` (adjust mapping if any scenario fails).

### Composition CRUD router

- [x] 3.11 GREEN: Create `app/schemas/compositions.py` — Pydantic request/response models for composition CRUD, chords/tablature/lyrics/todos sections, and the slug-lookup response.
- [x] 3.12 GREEN: Create `app/services/composition_service.py` — framework-agnostic business rules for create/read/update/delete composition and its embedded sections.
- [x] 3.13 RED: Create `tests/test_compositions_router.py` covering: create (owner-only, authenticated); read own and `by-slug` public read with no auth; update sections (owner/editor only); delete (owner only, `403` for editor, `404` for non-member on private).
- [x] 3.14 GREEN: Create `app/routers/compositions.py` — composition CRUD and `GET /api/compositions/by-slug/{slug}`, all routes under `Depends(require(...))`. Confirm 3.13 passes.
- [x] 3.15 RED: Create `tests/test_sections_router.py` covering: chords/tablature/lyrics/todos read/write nested under `/api/compositions/{id}/...`, enforcing the same `require(EDIT)`/`require(VIEW)` dependency.
- [x] 3.16 GREEN: Create `app/routers/sections.py` nested under the compositions router prefix. Confirm 3.15 passes.

### Sharing router

- [x] 3.17 RED: Create `tests/test_sharing_router.py` covering every sharing-and-visibility spec scenario: anonymous view of public composition (no auth); anonymous write attempt rejected (`401`/`403`); invited user edits public composition; non-invited authenticated user edit rejected (`403`); invited user views private composition; non-invited user private view rejected (`403`/`404`, no data leaked in body); non-invited user private edit rejected; visibility toggle and invite issue/list/revoke restricted to `manage_sharing` (owner only, `403` for editor/viewer, `404` for non-member).
- [x] 3.18 GREEN: Create `app/services/sharing_service.py` — visibility toggle (mints `share_slug` via a random 128-bit URL-safe generator on first going public), invite issue (mints opaque token via `app/core/security/tokens.py`, stores digest via `invitations` repository), invite redemption (requires authenticated account; replay-after-login flow), invite revoke.
- [x] 3.19 GREEN: Create `app/routers/sharing.py` — `PATCH .../visibility`, `POST .../invites`, `GET .../invites`, `DELETE .../invites/{id}`, `POST /api/auth/redeem-invite` (or nested equivalent). Confirm 3.17 passes.
- [x] 3.20 Verify: `docker compose up`, seed a user via the auth endpoints, then `curl` through create composition → toggle public → anonymous `GET by-slug` succeeds → anonymous `PATCH` rejected.


---

## Phase 4: Demos + Comments + Cloudinary (PR 4)

### Cloudinary signing

- [x] 4.1 RED: Create `tests/test_cloudinary_sign.py` covering: signed upload-parameter generation includes `timestamp`, `folder=erato/compositions/{id}`, `resource_type`, `tag=pending`, authenticated delivery type, and a signature computed from `API_SECRET`; upload-response verification accepts a correctly-signed response and rejects a forged one; `public_id` prefix check rejects a `public_id` outside the authorized folder; signed delivery URL minting produces a short-lived URL.
- [x] 4.2 GREEN: Create `app/core/security/cloudinary_sign.py` with the three functions from `design.md`'s Interfaces section: sign upload params, verify upload response, mint signed delivery URL. Confirm 4.1 passes.

### Repository: comments (+ demos sub-document helpers)

- [x] 4.3 RED: Create `tests/test_comments_repository.py` covering: create a timestamp-anchored comment; list a demo's comments ordered by `created_at` via the compound index `{composition_id, demo_id, created_at}` without loading the composition document.
- [x] 4.4 GREEN: Create `app/db/repositories/comments.py` implementing the `composition_comments` collection per the Approved Data Model.
- [x] 4.5 GREEN: Extend `app/db/repositories/compositions.py` with demo sub-document helpers (add/remove/list embedded `demos[]` entries, enforce the author's 5–10 expected cap is not hard-validated server-side beyond reasonable bounds — document the decision inline as a comment referencing `design.md`).

### Demos router

- [x] 4.6 RED: Create `tests/test_demos_router.py` covering every media-storage spec scenario: unauthenticated upload-signature request rejected (`401`), no credential issued; authenticated non-invited user on a composition rejected (`403`), no credential issued; authenticated editor/owner receives a signed credential without the backend ever receiving file bytes (assert no file-body parsing in the handler); `POST .../demos` with a forged Cloudinary response signature rejected; a `public_id` outside the authorized folder rejected; a verified upload is persisted with reference fields only (no binary/base64); playback URL endpoint requires `require(VIEW)` and mints a signed delivery URL without on-the-fly transformation parameters; timestamped comment create/list under `require(VIEW)`/`require(EDIT)`.
- [x] 4.7 GREEN: Create `app/schemas/demos.py` — Pydantic models for upload-signature request/response, demo creation (Cloudinary result payload), comment create/list.
- [x] 4.8 GREEN: Create `app/services/demo_service.py` — framework-agnostic: request upload signature (require EDIT); confirm upload (verify signature + folder prefix, untag `pending`, persist reference); mint playback URL (require VIEW); add/list comments.
- [x] 4.9 GREEN: Create `app/routers/demos.py` — `POST .../demos/upload-signature`, `POST .../demos`, `GET .../demos/{demo_id}/url`, `POST .../demos/{demo_id}/comments`, `GET .../demos/{demo_id}/comments`. Confirm 4.6 passes.

### Orphan sweep (cron)

- [x] 4.10 RED: Create `tests/test_orphan_sweep.py` covering: a `pending`-tagged Cloudinary asset older than 24 hours is identified for deletion; an asset younger than 24 hours is not swept; a confirmed (untagged) asset is never touched.
- [x] 4.11 GREEN: Replace the `app/routers/maintenance.py` stub from 1.18 with the real sweep handler (Vercel Cron target) implementing the logic validated in 4.10, guarded so it is only reachable by the cron secret/header Vercel attaches.
- [x] 4.12 Verify: `docker compose up`, request an upload-signature, simulate a Cloudinary response payload fixture, `POST` it to `.../demos`, then `GET .../demos/{id}/url` returns a signed URL.

---

## Phase 5: Frontend Skeleton + Design-System `core/` (PR 5)

- [x] 5.1 Create `frontend/vite.config.ts` — Vite + Vue plugin, path alias to `../erato-design-system/`, dev proxy `/api` → `http://backend:8000`, Vitest config block (test runner setup — makes frontend TDD applicable).
- [x] 5.2 Create `frontend/index.html` loading `tokens.css` then `bundle.css` in that order, setting `data-theme="noche"` by default.
- [x] 5.3 Create `frontend/Dockerfile` (`node:22-alpine`, `vite dev --host`) and wire the `frontend` service in `docker-compose.yml` (port `5173`, live volume mount, depends on `backend`).
- [x] 5.4 RED: Create `frontend/tests/design-system/chords.spec.ts` — table-driven tests for `detectChord()` against reference outputs from `erato-design-system/components/bundle.js:47-67`, covering: a simple major triad (e.g. C major), a slash chord (`D/F#`), extended chords (`Cmaj7`, `F#m7b5`, `D9`), a fifth-less voicing, and the single-note case.
- [x] 5.5 GREEN: Create `frontend/src/design-system/core/chords.ts` — transcribe `NOTE`, `QUAL`, `key()`, `detectChord()` from `bundle.js:35-67` verbatim. Confirm 5.4 passes.
- [x] 5.6 RED: Create `frontend/tests/design-system/tab.spec.ts` — golden-string tests for `tabToText()` covering column padding, bar lines, and multi-character frets, from reference outputs at `bundle.js:222-231`.
- [x] 5.7 GREEN: Create `frontend/src/design-system/core/tab.ts` — transcribe `EMPTY`, `blankTab`, `TECH`, `tabToText()` from `bundle.js:219-232`. Confirm 5.6 passes.
- [x] 5.8 RED: Create `frontend/tests/design-system/guitar.spec.ts` and `frontend/tests/design-system/piano.spec.ts` covering `fretsToMidi`, `autoBase` (guitar) and the white/black key layout (piano) against reference behavior at `bundle.js:115-117` and `:152`.
- [x] 5.9 GREEN: Create `frontend/src/design-system/core/guitar.ts` (`TUNING`, `STR`, `fretsToMidi`, `autoBase`) and `frontend/src/design-system/core/piano.ts` (`WHITE`, `BLACK_AFTER`). Confirm 5.8 passes.
- [x] 5.10 RED: Create `frontend/tests/design-system/lyrics.spec.ts` covering `parseLine`'s chord-over-syllable segmentation (e.g. `[Am7]Bajo el farol…`) against reference behavior at `bundle.js:290-295`.
- [x] 5.11 GREEN: Create `frontend/src/design-system/core/lyrics.ts` (`parseLine`). Confirm 5.10 passes.
- [x] 5.12 RED: Create `frontend/tests/design-system/waveform.spec.ts` asserting `peaks()` is deterministic for a fixed seed and matches the reference's seeded LCG output at `bundle.js:343-347`.
- [x] 5.13 GREEN: Create `frontend/src/design-system/core/waveform.ts` (`peaks`, exact constants transcribed). Confirm 5.12 passes.
- [x] 5.14 GREEN: Create `frontend/src/design-system/core/format.ts` (`pad2`, `fmt`, `cx`) transcribed from `bundle.js:95,342,10`. No independent RED test required (trivial formatting helpers); cover via the components that use them in Phase 6.
- [x] 5.15 Verify: `npm run test:unit` passes for all of `core/`; `npm run dev` serves a blank SPA shell reachable at `localhost:5173` with `tokens.css`/`bundle.css` loaded (inspect computed styles for a token-derived property).

---

## Phase 6: Design-System `composables/` + `components/` (PR 6)

### Composables (re-authored stateful behavior)

- [x] 6.1 RED: Create `frontend/tests/design-system/useTabKeyboard.spec.ts` covering: arrow-key movement, space extends at the end, two-digit fret entry (`1` → `12`), technique-character insertion (`h p b / ~ x`), `|` inserts a bar, backspace/delete on a bar line — matching reference behavior at `bundle.js:246-267`.
- [x] 6.2 GREEN: Create `frontend/src/design-system/composables/useTabKeyboard.ts`. Confirm 6.1 passes.
- [x] 6.3 RED: Create `frontend/tests/design-system/useAutoScroll.spec.ts` covering the autoscroll loop starting/stopping and the Escape-key exit-fullscreen handler, matching reference behavior at `bundle.js:301-318`.
- [x] 6.4 GREEN: Create `frontend/src/design-system/composables/useAutoScroll.ts` using `onScopeDispose` for cleanup. Confirm 6.3 passes.
- [x] 6.5 RED: Create `frontend/tests/design-system/useTakePlayback.spec.ts` covering `<audio>` element coordination, fallback interval timer, and seek behavior, matching reference behavior at `bundle.js:355-368`.
- [x] 6.6 GREEN: Create `frontend/src/design-system/composables/useTakePlayback.ts`. Confirm 6.5 passes.

### Components (1:1 structural + visual parity)

- [x] 6.7 RED: Create `frontend/tests/design-system/components/ErIcon.spec.ts`, `ErButton.spec.ts`, `ErTag.spec.ts`, `ErSegmented.spec.ts`, `ErSideNav.spec.ts` — Vue Test Utils structural assertions comparing emitted `er-*` classes and DOM structure against `erato-design-system/components/*/preview.html` fixtures, under both `data-theme="noche"` and `data-theme="matine"`.
- [x] 6.8 GREEN: Create `frontend/src/design-system/components/ErIcon.vue`, `ErButton.vue`, `ErTag.vue`, `ErSegmented.vue`, `ErSideNav.vue` — real semantic elements (`<button>` etc.) with visible focus ring per the design-system-port spec. Confirm 6.7 passes.
- [x] 6.9 RED: Create `frontend/tests/design-system/components/ErChordEditor.spec.ts` covering: structural parity against `preview.html`; guitar↔piano octave-folding `setInst` behavior (reference `bundle.js:194-201`); `v-model` emits on note change (not `defaultFrets`+`onChange`); chord name renders via `detectChord()` from `core/chords.ts`.
- [x] 6.10 GREEN: Create `frontend/src/design-system/components/ErChordEditor.vue`, `ErFretboard.vue`, `ErPiano.vue`, `ErChordName.vue` (internal). Confirm 6.9 passes.
- [x] 6.11 RED: Create `frontend/tests/design-system/components/ErTabEditor.spec.ts` covering structural parity and integration with `useTabKeyboard()` and `tabToText()`.
- [x] 6.12 GREEN: Create `frontend/src/design-system/components/ErTabEditor.vue`. Confirm 6.11 passes.
- [x] 6.13 RED: Create `frontend/tests/design-system/components/ErLyricsViewer.spec.ts` covering structural parity, fullscreen maximize, `useAutoScroll()` integration, and chord-over-syllable rendering via `parseLine()`.
- [x] 6.14 GREEN: Create `frontend/src/design-system/components/ErLyricsViewer.vue`. Confirm 6.13 passes.
- [x] 6.15 RED: Create `frontend/tests/design-system/components/ErDemoPlayer.spec.ts` covering structural parity, `useTakePlayback()` integration, and waveform rendering via `peaks()`.
- [x] 6.16 GREEN: Create `frontend/src/design-system/components/ErDemoPlayer.vue`. Confirm 6.15 passes.
- [x] 6.17 RED: Create `frontend/tests/design-system/components/ErTodoList.spec.ts` covering structural parity and `v-model` add/toggle/delete/clear-done behavior.
- [x] 6.18 GREEN: Create `frontend/src/design-system/components/ErTodoList.vue`. Confirm 6.17 passes.
- [x] 6.19 GREEN: Create `frontend/src/design-system/components/index.ts` — barrel exporting every `Er*.vue` component; confirm no app code outside `design-system/` imports a component by its direct file path (grep check).
- [x] 6.20 Verify: `npm run test:unit` passes for `composables/` and `components/`; manual visual check of each component under both themes (per the design-system-port spec's contrast/focus-ring scenarios), recorded as a checklist note since automated contrast assertions are out of scope for this change per `design.md`'s Testing Strategy.

---

## Phase 7: Feature Screens (PR 7)

### API client

- [x] 7.1 RED: Create `frontend/tests/api/client.spec.ts` covering: access token held in a module-scoped variable (never `localStorage`); attached as a `Bearer` header; on a `401`, exactly one refresh attempt against `/api/auth/refresh` before replaying the original request; a failed refresh clears state (simulate via a mocked router/navigation call).
- [x] 7.2 GREEN: Create `frontend/src/api/client.ts` and `frontend/src/api/auth.ts`, `compositions.ts`, `demos.ts`, `sharing.ts` — typed HTTP client wrapping `fetch`. Confirm 7.1 passes.

### Feature screens

- [x] 7.3 GREEN: Create `frontend/src/features/auth/` — register/login views using `ErButton`/form primitives, wired to `api/auth.ts`.
- [x] 7.4 RED: Create `frontend/tests/features/auth.spec.ts` covering: login form submit calls the API client; invalid-credentials error surfaces without revealing which field failed (mirrors the backend contract at the UI layer).
- [x] 7.5 GREEN: Confirm 7.4 passes against 7.3.
- [x] 7.6 GREEN: Create `frontend/src/features/compositions/` — composition list, create, detail view assembling `ErChordEditor`, `ErTabEditor`, `ErLyricsViewer`, `ErTodoList` from the design system, wired to `api/compositions.ts`. Design-system components stay presentational; feature components own API calls and state.
- [x] 7.7 RED: Create `frontend/tests/features/compositions.spec.ts` covering: an edit control is hidden/disabled for a viewer-role response from the API (frontend convenience hiding, not the enforcement point — matches AGENTS.md's "Compartir" requirement) while a direct API call is still what the backend checks.
- [x] 7.8 GREEN: Confirm 7.7 passes against 7.6.
- [x] 7.9 GREEN: Create `frontend/src/features/demos/` — demo list/upload/player view assembling `ErDemoPlayer`, wired to the direct-to-Cloudinary upload flow (`api/demos.ts` for signature + confirmation, direct `fetch`/`FormData` POST to Cloudinary for the bytes).
- [x] 7.10 RED: Create `frontend/tests/features/demos.spec.ts` covering: the upload flow never sends file bytes through the backend client (assert the backend API call for upload-signature carries no file body, and the Cloudinary POST target is the Cloudinary URL, not the backend's).
- [x] 7.11 GREEN: Confirm 7.10 passes against 7.9.
- [x] 7.12 GREEN: Create `frontend/src/features/sharing/` — visibility toggle and invite management view, wired to `api/sharing.ts`.
- [x] 7.13 Verify end-to-end (manual, deferred automated E2E per `design.md`): `docker compose up`, register a user, create a composition, add a chord via `ErChordEditor`, toggle it public, open the share link in an incognito window (anonymous view succeeds, edit controls absent/rejected), upload a demo, play it back.

---

## Phase 8: Documentation Close-Out

- [x] 8.1 Generate the root `README.md` per `AGENTS.md`'s required structure (what Erato is, functionalities, stack/architecture diagram, local/Vercel run instructions, "Mi rol en el proyecto" section crediting the author's design decisions and AI-assisted implementation, design-system link, license/contact placeholder pending author input).
- [x] 8.2 Confirm every `.env.example` variable from 1.19 is referenced and documented in the README's "Cómo correrlo" section.
- [x] 8.3 Final pass: confirm `openspec/config.yaml` Phase 0 updates (0.1–0.3) reflect the actually-chosen `pytest`/`npm run test:unit` commands and `tdd: true`.

---

## Notes on Testing Strategy Coverage

Every row in `design.md`'s Testing Strategy table is covered by a task above:
- Permission matrix → 3.1
- Argon2id round trip / `needs_rehash` / tampered hash → 2.1
- Access-token expiry / tampered signature / `alg: none` / revocation → 2.3
- Invite token expiry / single-use / second-account redemption / revoked → 3.5, 3.17
- Cloudinary forged signature / wrong-folder `public_id` → 4.1
- `404`/`403`/`200` per role across content routes → 3.9, 3.17, 4.6
- Refresh rotation reuse-detection → 2.7
- Mongo client singleton identity → 1.11
- `detectChord` table (slash/extended/fifth-less/single-note) → 5.4
- `tabToText` golden strings → 5.6
- `useTabKeyboard` full behavior → 6.1
- `parseLine` / `peaks` determinism → 5.10, 5.12
- Component structural parity × both themes → 6.7, 6.9, 6.11, 6.13, 6.15, 6.17
- Visual/contrast/focus-ring checklist → 6.20 (manual, as the design document specifies)
- E2E flows → 7.13 (manual, deferred automated E2E explicitly out of scope per `design.md`)

**Threat Matrix**: `design.md` marks the Threat Matrix section **N/A** (no shell commands, subprocesses, VCS/PR automation, or process integration introduced by this change). No threat-matrix RED tasks are required.
