# Exploration: erato-monetizacion-preview

Source: Engram `sdd/erato-monetizacion-preview/explore` (obs 142), plus the verified findings forwarded by the orchestrator on 2026-10-03. The explore executor had no write tool, so this file reconstructs the OpenSpec copy.

## Scope explored

Steps 1-4 of `pasos.md`, all running in a Vercel PREVIEW environment. Out of scope: payment gateway, Cloudflare R2 migration, real time (step 5), mobile/PWA (step 6).

## Key findings

### Deployment and environment
- Root `vercel.json` builds only the frontend and rewrites `/api/*` to `api/index.py`; it declares a daily orphan-sweep cron. `tests/test_vercel_config.py` pins its shape: do not touch it.
- The landing needs its own Vercel project (Root Directory `landing/`, own `landing/vercel.json`, "include source files outside Root Directory" must be verified).
- `Settings` already exposes `mongodb_db` (`app/db/client.py`), so a Preview-scoped `MONGODB_DB` isolates preview data on the same free Atlas M0.
- `settings.app_base_url` builds invite URLs (`app/routers/sharing.py:136`). Refresh cookie is `secure=True`, path `/api/auth`.
- Indexes are NOT created at startup: `scripts/ensure_indexes.py` runs by hand; its `REPOSITORIES` list and `tests/test_ensure_indexes_script.py` must be extended for new collections.
- Vercel Crons run only on production deployments: anything time-based in preview needs lazy evaluation.
- Vercel Deployment Protection may block anonymous public links and the landing on preview URLs (verify in project settings).

### Sections and versioning
- `PUT /api/compositions/{id}/{chords|tablature|lyrics|todos}` replaces the whole section (`app/routers/sections.py`, `app/services/composition_service.py:79-89`, `app/db/repositories/compositions.py:113-138`).
- Only one composition-wide `updated_at`; no revision counter.
- Frontend `saveAll()` (`frontend/src/views/CompositionDetailView.vue:565-584`) fires 4 parallel PUTs with no conflict handling.
- Schema options identified (not chosen): A) separate `section_revisions` collection; B) embedded capped array; C) embedded counter + snapshot collection. Conflict check via an `expected_rev` conditional update.

### Permissions and sharing
- `resolve_role(user_id, access_record)` (`app/core/permissions.py:39-75`) is pure over the composition record; band context should be pre-resolved in `composition_access` (`app/deps.py:52-77`) only when `band_id` is set.
- Read-only-when-unpaid belongs in `require()` (`app/deps.py:80-100`).
- Invitations are keyed by `composition_id` (`app/db/repositories/invitations.py`, index `idx_invitations_composition_id`, TTL on `expires_at`). Redeem flow: `POST /api/auth/redeem-invite` -> `SharingService.redeem_invite` -> `add_member` (`app/routers/auth.py:171-190`, `app/services/sharing_service.py`, `app/routers/sharing.py`).
- `add_member` is not atomic (pull then push).
- `list_by_user` needs a `band_id` clause.

### Landing
- `ErButton` renders only `<button>` (no `href`), so link CTAs need native `<a class="er-btn ...">` (the reference landing already does this).
- Design-system Vue components import only relative paths (no `@/`), so `landing/` can reuse them through a Vite alias. `ErTag`, `ErChordEditor`, `ErLyricsViewer`, `ErDemoPlayer` map 1:1 to the landing usage.
- Gaps: CTAs point to `#`, no keyboard navigation between slides, no `prefers-reduced-motion`, privacy/terms links are dead.
- Landing pricing copy: Free = no sharing with people, no version history, "1 demo de audio"; Pro Individual = "Más espacio para demos", "Historial de versiones de letras y acordes"; Pro Banda = up to 8 members, extra member 1.000 CLP, share with the band.

### Free Pro options (resolved by the user afterwards)
- (1) env-flagged self-serve endpoint, (2) allowlist/admin grant, (3) seed script. The user chose (1): any registered user self-activates, `provider: "free"` behind a replaceable billing port, env flag failing closed.

### Frontend impact
- `SharingModal.vue`, dashboard, new screens (band management, plan/upgrade page, read-only banner, history panel, conflict dialog), `frontend/src/router/routes.ts`.

### Testing
- Strict TDD enabled. Backend `.venv/bin/pytest tests/` (needs MongoDB on localhost:27017); frontend `cd frontend && npm run test:unit`, `npx vue-tsc --noEmit`, `npm run build`; the landing gets its own Vitest.

### Rough slicing (explorer)
~4.000-4.500 authored lines in ~14 PR-sized units. Dependencies: Band model -> role resolution -> invitations -> PlanPolicy -> free Pro -> UI; landing, versioning and footer are independent tracks.
