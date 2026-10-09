# Tasks: Erato monetization in Vercel Preview (landing, versioning, bands and plans, public footer)

Change: `erato-monetizacion-preview`. Inputs: `proposal.md`, `design.md` (AD1-AD20, OD-1..OD-9 resolved, G-1 deferred to the gateway), 11 delta specs.
Strict TDD is ENABLED: inside every unit the order is RED (failing test, observed failing) -> GREEN -> REFACTOR. A unit is one work-unit commit (or a few), tests and docs shipped with the behavior.
Commit convention (AGENTS.md): messages in Spanish, present tense, descriptive, conventional-commit prefix allowed; no AI attribution.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~8,200 total (public `erato` ~6,230 across 23 units; private `erato-cloud` ~1,970 across 7 units). Range 7,500-9,000 |
| 400-line budget risk | High (total); each unit is planned at or under ~400 authored lines including tests |
| Chained PRs recommended | Yes |
| Suggested split | One PR per unit below. Independent tracks (PV1, L1-L3, G1, X1, V1-V4) stack into `erato` `preview`; bands chain B1 -> B1M -> B2 -> B3 -> B5a -> B5b -> {B6a, B7} -> B6b -> {FX, F2, F3} -> DOC as a feature-branch-chain on `preview`; cloud C0 -> C1 -> C2 -> C3a -> C3b -> {C4, C5} into `erato-cloud` `preview`. Cross-repo rule: the public unit merges first, then the cloud unit bumps the submodule pointer |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain on `preview` (confirmed by the author 2026-10-04, per P20) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain on `preview` (confirmed 2026-10-04)
400-line budget risk: High

Decision resolved 2026-10-04: `feature-branch-chain` on `preview`. Originally: the orchestrator must ask the author for the chain strategy (stacked-to-main is NOT viable because P6 forbids reaching `main`; realistic choices are `feature-branch-chain` on `preview` per P20, or `size-exception`). Recommendation: `feature-branch-chain` for the bands/plans series and stacked PRs into `preview` for the independent tracks, exactly as P20 states. Also a standing note: the author codes with Gemini, so pause before launching sdd-apply (memory feedback).

### Line estimates per unit

| Unit | Repo | Est. lines | Unit | Repo | Est. lines |
|------|------|-----------|------|------|-----------|
| PV1 | erato | 150 | B6a | erato | 200 |
| L1 | erato | 380 | B6b | erato | 300 |
| L2 | erato | 380 | B7 | erato | 260 |
| L3 | erato | 380 | FX | erato | 220 |
| G1 | erato | 120 | F2 | erato | 380 |
| X1 | erato | 260 | F3 | erato | 350 |
| V1 | erato | 380 | DOC | erato | 120 |
| V2 | erato | 250 | C0 | erato-cloud | 250 |
| V3 | erato | 330 | C1 | erato-cloud | 250 |
| V4 | erato | 280 | C2 | erato-cloud | 330 |
| B1 | erato | 280 | C3a | erato-cloud | 280 |
| B1M | erato | 300 | C3b | erato-cloud | 320 |
| B2 | erato | 350 | C4 | erato-cloud | 220 |
| B3 | erato | 220 | C5 | erato-cloud | 320 |
| B5a | erato | 300 | | | |
| B5b | erato | 320 | | | |

Splits versus the proposal table: B1 -> B1 + B1M (migration + restore scripts), B5 -> B5a + B5b (AD18 added create/delete), B6 -> B6a (leave/remove) + B6b (transfer, OD-1 unblocked), C3 -> C3a + C3b (checkout/compensation per AD11), plus DOC (seams and runbook completion). All other IDs are those of `proposal.md` as refreshed by the "Impact on proposal slicing" table of the design.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| PV1 | Preview branch notes, `.env.example`, `APP_BASE_URL` fail-closed, core runbook | erato PR 1 -> `preview` | `.venv/bin/pytest tests/test_settings.py` | `docker compose up` still boots; unset `APP_BASE_URL` -> invite link request 500 `config_missing` | Revert `app/settings.py`, docs, `.env.example` |
| L1 | Landing scaffold + `useSlideNav` | erato PR 2 | `cd landing && npm run test:unit` | `cd landing && npm run dev`, wheel/keys move slides | Delete `landing/` |
| L2 | Slides 1-4 | erato PR 3 | `cd landing && npm run test:unit` | dev server, visual check in both themes | Revert slide components |
| L3 | Slides 5-7, footer, CTAs, responsive, a11y | erato PR 4 | `cd landing && npm run test:unit && npm run build` | build + preview, 980 px collapse, reduced motion | Revert slides/footer |
| G1 | "Guardado en Erato" footer | erato PR 5 | `cd frontend && npm run test:unit -- tests/features/saved-in-erato-footer.spec.ts` | Open a public link anonymously vs logged in | Revert `SavedInEratoFooter.vue` and its wiring |
| X1 | `PlanPolicy` port, `UnlimitedPlanPolicy`, getters, entitlements, contract test | erato PR 6 | `.venv/bin/pytest tests/test_plan_policy_contract.py tests/test_entitlements_router.py` | `GET /api/me/entitlements` against local app returns all-allow, `direct` | Revert new core modules and `main.py` include |
| V1 | Revision counter, conditional save, 409, snapshots | erato PR 7 | `.venv/bin/pytest tests/test_versioning_service.py tests/test_sections_router.py` | Two curl PUTs with same `expected_rev`: 200 then 409 | Revert; no `expected_rev` keeps old behavior |
| V2 | History list/get/restore + gate | erato PR 8 | `.venv/bin/pytest tests/test_history_router.py` | list then restore a revision via curl | Revert `history.py` router |
| V3 | Dirty-section saves, conflict dialog | erato PR 9 | `cd frontend && npm run test:unit -- tests/features/use-section-save.spec.ts` | Two browser tabs editing one section | Revert `useSectionSave` wiring |
| V4 | History panel | erato PR 10 | `cd frontend && npm run test:unit -- tests/features/section-history-panel.spec.ts` | Open panel, preview, restore | Revert panel component |
| B1 | Bands repo, indexes, invitation `target` support | erato PR 11 (chain base) | `.venv/bin/pytest tests/test_bands_repository.py tests/test_ensure_indexes_script.py tests/test_invitations_repository.py` | `python -m scripts.ensure_indexes` then `--rollback` on a scratch DB | Revert repos; `--rollback` drops new indexes |
| B1M | Migration + restore scripts | erato PR 12 | `.venv/bin/pytest tests/test_migrate_bands.py` | dry run, apply, second run, restore on a scratch DB | Restore script; revert scripts |
| B2 | Band context + `resolve_role` + read-only in `require()` | erato PR 13 | `.venv/bin/pytest tests/test_permissions.py tests/test_deps_require.py tests/test_band_roles.py` | `GET /api/compositions/{id}` shows band role | Revert `permissions.py`/`deps.py` |
| B3 | Core gate call sites | erato PR 14 | `.venv/bin/pytest tests/test_plan_policy_contract.py` | deny-all stand-in override hits each gate | Revert gate calls |
| B5a | `BandsService.create/create_for_user/delete_band`, band CRUD read/rename | erato PR 15 | `.venv/bin/pytest tests/test_bands_service.py tests/test_bands_router.py` | `POST /api/bands` direct creation | Revert service/router |
| B5b | Band invites, redeem, atomic seat join, remove member, atomic role set | erato PR 16 | `.venv/bin/pytest tests/test_bands_invites.py tests/test_seat_race.py` | two concurrent redeems at the last seat | Revert invite/join code |
| B6a | Leave and remove (ordered, idempotent) | erato PR 17 | `.venv/bin/pytest tests/test_bands_leave.py` | leave detaches own compositions | Revert leave/remove |
| B6b | Ownership transfer (AD10) | erato PR 18 | `.venv/bin/pytest tests/test_bands_transfer.py` | request, accept, expired accept 410 | Revert transfer methods |
| B7 | Share composition with band; remove composition invites | erato PR 19 | `.venv/bin/pytest tests/test_sharing_router.py tests/test_sharing_roles.py tests/test_band_share.py` | attach/detach composition via curl | Revert sharing changes |
| FX | Payment-only extension factory, entitlements client, `useBandCreation` | erato PR 20 | `cd frontend && npm run test:unit -- tests/app/ tests/features/use-band-creation.spec.ts` | app boots with no `/plan` route | Revert `app.ts`, `main.ts`, router |
| F2 | Band management screen + creation form | erato PR 21 | `cd frontend && npm run test:unit -- tests/features/band-view.spec.ts` | `/bands`, create, invite, leave, transfer in browser | Revert `features/bands/` and routes |
| F3 | `SharingModal`, dashboard, read-only banner | erato PR 22 | `cd frontend && npm run test:unit -- tests/features/sharing-modal.spec.ts tests/features/dashboard-view.spec.ts` | share with band, banner on inactive | Revert those views |
| DOC | `docs/seams.md`, runbook completion | erato PR 23 | `.venv/bin/pytest tests/test_plan_policy_contract.py` (docs pin) | N/A, documentation only | Revert docs |
| C0 | Cloud bootstrap, submodule on `preview`, entry, CI, Vercel config | cloud PR 1 -> cloud `preview` | `.venv/bin/pytest tests/` (in `erato-cloud`) | deployed health route, `api.index.app is app.main.app` | Revert pointer/bootstrap |
| C1 | Subscriptions repository and indexes | cloud PR 2 | `.venv/bin/pytest tests/test_subscriptions_repository.py` | `python -m scripts.ensure_cloud_indexes` on scratch DB | Drop collection/indexes |
| C2 | `SubscriptionPlanPolicy` (AD19) | cloud PR 3 | `.venv/bin/pytest tests/test_policy.py` | `/api/me/entitlements` under cloud app | Remove override in `wiring.py` |
| C3a | Billing port, free provider, kill switch, individual endpoints | cloud PR 4 | `.venv/bin/pytest tests/test_billing_free.py tests/test_plan_router.py` | `POST /api/plan/individual` with flag on/off | Unmount plan router |
| C3b | `BandCheckout`, `/api/plan/checkout/band`, band endpoints | cloud PR 5 | `.venv/bin/pytest tests/test_band_checkout.py` | checkout creates band + subscription; forced failure compensates | Revert checkout/router |
| C4 | Transfer subscription step (AD20) | cloud PR 6 | `.venv/bin/pytest tests/test_transfer_step.py` | accept a transfer on preview, subscription moves | Revert `confirm_band_transfer` impl |
| C5 | Cloud web: plan page, band checkout view | cloud PR 7 | `cd web && npm run test:unit && npm run build` | deployed preview: plan page, `/plan/bands/new` | Revert `web/` |

Path verification (performed 2026-10-04):
- Exist in `erato`: `pytest.ini`, `tests/conftest.py`, `tests/test_ensure_indexes_script.py`, `scripts/ensure_indexes.py`, `frontend/package.json` (`test:unit` = `vitest run`, `build` = `vue-tsc && vite build`), `frontend/vite.config.ts`, `frontend/src/main.ts`, `frontend/src/router/{index,routes}.ts`, `frontend/tests/**` (frontend specs live in `frontend/tests/`, not beside sources), `.atl/skill-registry.md`.
- Do NOT exist yet (created by the named unit): `landing/` (L1), `.env.example` (PV1), `docs/` (PV1), `app/core/plan_policy.py` (X1), `app/db/repositories/{bands,section_revisions}.py` (B1/V1), `app/services/{bands,versioning}_service.py` (B5a/V1), `app/routers/{bands,history,entitlements}.py`, `scripts/migrate_bands.py` (B1M), `frontend/src/app.ts` (FX), any `frontend/tests/app/`.
- `erato-cloud` contains only `README.md` and the `erato` submodule (checked out at `erato/`, tracking `main`): `pytest.ini`, `tests/`, `api/`, `erato_cloud/`, `web/`, `vercel.json`, CI are all created by C0-C5.
- Host Python path inside `erato-cloud`: `.venv/bin/pytest tests/` needs `pytest.ini` `pythonpath = . erato` (created by C0).

Edit authority: `erato-cloud` is outside the `erato` repo root. Tasks for units C0-C5 name paths under `/home/bspc/proyectos/erato-cloud/`; apply for those units needs the author's explicit grant of edit scope over that folder (proposal Prerequisites) plus the `preview` branch, the Vercel project and the preview env vars created by the author. Paths a task only reads carry `(read-only)`.

Conventions used below: Mongo must be reachable at `localhost:27017` for every backend test command (`docker compose up -d mongo` or `TEST_MONGODB_URI`). "Run" tasks must record observed RED and GREEN output. Every unit ends with a commit task. Spec references use `capability: requirement`.

---

## Phase 0: Prerequisites and decisions (blocking, no code)

- [x] 0.1 Ask the author for the chain strategy (`feature-branch-chain` recommended, or `size-exception`); record the answer in this file's forecast lines. Pause before sdd-apply (author works with Gemini).
- [ ] 0.2 Author creates `preview` in `erato` (from `main`) and, for cloud units, the private repo `preview` branch, the Vercel project, Preview-scoped env vars and the folder edit grant (`preview-deployment: Each repository MUST have a long-lived preview branch`).
- [ ] 0.3 Confirm `docker compose up -d mongo` works so every pytest command below can run (read-only check of `docker-compose.yml` (read-only)).

---

## Phase 1: Public `erato`, independent tracks (PRs into `erato` `preview`)

### Unit PV1 (repo: erato) - preview config and fail-closed base URL (~150 lines)
Specs: `backend-platform: New environment settings MUST be documented and fail closed`; `preview-deployment: Preview environment variables MUST isolate data and secrets`, `Promotion and rollback MUST be documented, not executed`. Design AD16.
Depends on: none.

- [x] PV1.1 RED: in `tests/test_settings.py` add tests: `app_base_url` unset -> `build_app_url("/invite/x")` raises `ConfigurationError` (500, code `config_missing`, message names `APP_BASE_URL`); set -> returns joined URL; never derived from request host. Run `.venv/bin/pytest tests/test_settings.py` and observe failure.
- [x] PV1.2 GREEN: `app/settings.py` make `app_base_url: Optional[str] = None`, add `build_app_url(path)`; `app/core/errors.py` add `ConfigurationError(AppError)` 500 `config_missing`; replace direct `app_base_url` uses in `app/services/sharing_service.py` with the helper (read usages first). `tests/conftest.py` sets `APP_BASE_URL` for the suite.
- [x] PV1.3 REFACTOR: run full `.venv/bin/pytest tests/`; confirm `tests/test_vercel_config.py` still passes and root `vercel.json` is unchanged.
- [x] PV1.4 Create `.env.example` (every setting, owning repo noted, no values: `MONGODB_URI`, `MONGODB_DB`, `JWT_SECRET`, Cloudinary variables incl. `CLOUDINARY_FOLDER_PREFIX`, `APP_BASE_URL`; cloud-owned `FREE_PRO_ENABLED`/`VERCEL_ENV` listed as cloud-owned) and `docs/runbook-preview.md` (core part: `preview` branch rules, landing Vercel project incl. "include source files outside Root Directory" check, index bootstrap against `erato_preview`, Deployment Protection off, noindex, promotion order and rollback documented not executed).
- [x] PV1.5 Commit (Spanish), e.g. `feat(config): exige APP_BASE_URL y documenta variables del preview`.

### Unit L1 (repo: erato) - landing scaffold and navigation (~380 lines)
Specs: `landing-page: seven slides navigable by index`, `Wheel navigation debounced`, `Keyboard navigation`, `Reduced motion`, `reuse the app's design system without modifying it`. Design AD17, Components table (`landing/**`).
Depends on: none (can start in parallel with PV1).

- [x] L1.1 RED: create `landing/tests/useSlideNav.spec.ts` (Vitest, jsdom): index clamps 0-6; counter text; wheel debounce 900 ms; wheel ignored inside scroll-exclusion elements; ArrowDown/PageDown/Space next, ArrowUp/PageUp previous, Home/End; `prefers-reduced-motion` disables transitions flag. Run `cd landing && npm run test:unit` (fails: nothing exists; `landing/package.json` created by L1.2 so first run is after scaffold, record RED after minimal scaffold).
- [x] L1.2 Scaffold `landing/package.json` (scripts `dev`, `build` = `vue-tsc && vite build`, `test:unit` = `vitest run`), `landing/tsconfig.json`, `landing/vite.config.ts` (aliases `@ds-vue` -> `../frontend/src/design-system`, `@design-system` -> `../erato-design-system`, `server.fs.allow: ['..']`, `transformIndexHtml` plugin injecting `<meta name="robots" content="noindex">` when `process.env.VERCEL_ENV !== 'production'`), `landing/index.html`, `landing/src/main.ts`, `landing/src/App.vue` (empty slide host), `landing/vercel.json`. Do not touch root `vercel.json` or `tests/test_vercel_config.py`.
- [x] L1.3 GREEN: implement `landing/src/composables/useSlideNav.ts` until L1.1 passes.
- [x] L1.4 RED then GREEN: `landing/tests/static-checks.spec.ts` asserting tokens from `tokens.css` only (no hex colors in landing sources), no `!` or emoji in copy, `index.html` has the noindex meta outside production. Implement as needed.
- [x] L1.5 REFACTOR + `cd landing && npm run test:unit && npm run build`; add landing section to `docs/runbook-preview.md`.
- [x] L1.6 Commit (Spanish), e.g. `feat(landing): crea la base de la landing con navegación por diapositivas`.

### Unit L2 (repo: erato) - slides 1-4 (~380 lines)
Specs: `landing-page: seven slides`, `support both themes and meet accessibility minimums`. Reference: `erato-design-system/erato-landing/index.html` (read-only).
Depends on: L1.

- [x] L2.1 RED: `landing/tests/slides-1-4.spec.ts`: renders Inicio, Escribir, Leer, Escuchar slides in order with headings, one `<h2>` each, controls are real buttons/links, no `!`/emoji, Spanish tuteo copy. Run `cd landing && npm run test:unit` and observe failure.
- [x] L2.2 GREEN: create `landing/src/slides/SlideInicio.vue`, `SlideEscribir.vue`, `SlideLeer.vue`, `SlideEscuchar.vue` and register them in `landing/src/App.vue`; reuse `@ds-vue` components; CSS from tokens only.
- [x] L2.3 REFACTOR + `npm run test:unit && npm run build`; manual check in Noche and Matine themes (contrast 4.5:1 for text).
- [x] L2.4 Commit (Spanish), e.g. `feat(landing): agrega las diapositivas Inicio, Escribir, Leer y Escuchar`.

### Unit L3 (repo: erato) - slides 5-7, footer, CTAs, responsive (~380 lines)
Specs: `landing-page: Calls to action`, `Footer privacy and terms links MUST be placeholders`, `layout MUST collapse responsively at 980 px`, `Reduced motion`. P17, P18, P19.
Depends on: L2.

- [x] L3.1 RED: `landing/tests/ctas-footer.spec.ts`: "Iniciar sesion" href = `${VITE_APP_URL}/login`; "Empieza gratis" and every plan CTA = `${VITE_APP_URL}/register`; CTAs are native `<a class="er-btn">`; footer links `#privacidad` and `#terminos` exist and no legal text is present; focus ring present; slides 5-7 render. Run and observe failure.
- [x] L3.2 GREEN: create `landing/src/slides/SlidePrecios.vue` (plans), `SlideBandas.vue`, `SlideCierre.vue` (names to follow the reference landing sections), footer component `landing/src/components/LandingFooter.vue`, `landing/src/config.ts` reading `VITE_APP_URL`; 980 px responsive collapse in styles; reduced-motion CSS.
- [x] L3.3 REFACTOR + `cd landing && npm run test:unit && npm run build`; document `VITE_APP_URL` in `.env.example`.
- [x] L3.4 Commit (Spanish), e.g. `feat(landing): completa diapositivas, CTAs al registro y pie con enlaces provisionales`.

### Unit G1 (repo: erato) - "Guardado en Erato" footer (~120 lines)
Specs: `sharing-and-visibility: Anonymous viewers of a public composition MUST see the "Guardado en Erato" footer`.
Depends on: none.

- [x] G1.1 RED: `frontend/tests/features/saved-in-erato-footer.spec.ts`: footer renders with a register link for an anonymous viewer on a public composition; absent for authenticated users and for the owner; absent on private/forbidden views; no `!`/emoji. Run `cd frontend && npm run test:unit -- tests/features/saved-in-erato-footer.spec.ts` and observe failure.
- [x] G1.2 GREEN: create `frontend/src/features/compositions/SavedInEratoFooter.vue` (native `<a class="er-btn">` to `/register`), wire into `frontend/src/features/compositions/CompositionDetailView.vue` for anonymous public views only.
- [x] G1.3 REFACTOR + `cd frontend && npm run test:unit && npm run build`.
- [x] G1.4 Commit by Claude: `feat(composiciones): muestra el pie Guardado en Erato en enlaces públicos anónimos` (Claude replaced the nonexistent `er-btn--quiet` with `er-btn--ghost`).

G1 execution evidence (2026-10-07):
- RED: focused Vitest run -> 1 failed / 11 passed (12), 1.57s; `Unable to get footer` for the anonymous public viewer. An initial command used the wrong relative file path and found no tests; it is not the RED evidence.
- GREEN: focused run -> 12 passed, 1.57s. Final full `npm run test:unit` -> 55 files / 452 tests passed, 12.48s. `npm run build` -> vue-tsc and Vite passed, built in 1.60s.
- Full verification first exposed routers without the named register route and missing required fixture fields; used RouterLink to `/register` and completed the fixture, then reran checks. Existing harness warnings remain.
- Reuses `er-row`, `er-btn`, and `er-btn--quiet`; no new CSS or dependencies. Keyboard focus and SPA navigation tested. Token contrast for ink on bg-100/200/300 is at least 12.61:1 in Noche and 11.75:1 in Matiné; no browser visual audit performed.
- Only G1 component, detail integration, focused spec, and this task record changed. No model changes, git writes, landing/pasos.md/design-system edits, or erato-cloud access. G1.4 remains for Claude.

---

## Phase 2: Public `erato`, shared seam (X1)

### Unit X1 (repo: erato) - PlanPolicy port, getters, entitlements (~260 lines)
Specs: `plan-policy-port: closed set of questions`, `UnlimitedPlanPolicy default`, `overridable dependency getter`, `Plan-gate refusals machine readable`, `entitlements endpoint`, `accept external routers and keep a stable app entry`; `backend-platform: importable as app.main.app and accept host extensions`. Design AD4, AD5, AD6.
Depends on: none (gate for every other seam-dependent unit).

- [x] X1.1 RED: create `tests/test_plan_policy_contract.py`: `UnlimitedPlanPolicy` returns `True, True, True, None, None, True, True` for the seven questions incl. `confirm_band_transfer`; a stand-in implementing the Protocol installed through `app.dependency_overrides[app.deps.get_plan_policy]` is what a request receives; user-scoped methods receive only the user id; `app.dependency_overrides[get_host_capabilities]` works; extra router added via `app.include_router` is served; `api.index.app is app.main.app`; overrides cleared in a fixture. Run `.venv/bin/pytest tests/test_plan_policy_contract.py` and observe failure.
- [x] X1.2 RED: create `tests/test_entitlements_router.py`: `GET /api/me/entitlements` 401 anonymous; under default returns `can_share_with_people`, `can_create_band`, `can_view_history` true, `demo_limit_per_composition` null, `extensions_available` false, `band_creation_mode` "direct"; deny-all stand-in -> `hand_off` and false flags; no per-composition variance. Observe failure.
- [x] X1.3 RED: add to `tests/test_permissions.py` or a new `tests/test_errors.py` a case for `PlanGateError` serializing `{"error": "plan_gate_sharing", ...}` status 403 and `GoneError` 410 (needed by later units; design AD4).
- [x] X1.4 GREEN: create `app/core/plan_policy.py` (`PlanPolicy` Protocol, `UnlimitedPlanPolicy`, `HostCapabilities`); `app/core/errors.py` add `PlanGateError(code)`, `GoneError`; `app/deps.py` add `get_plan_policy`, `get_host_capabilities`; create `app/schemas/entitlements.py`, `app/routers/entitlements.py`; `app/main.py` include the router.
- [x] X1.5 REFACTOR + full `.venv/bin/pytest tests/`.
- [x] X1.6 Commit (Spanish), e.g. `feat(plan): agrega el puerto PlanPolicy, la politica ilimitada y el endpoint de entitlements`.


---

## Phase 3: Public `erato`, versioning track (stacked into `preview` after X1)

### Unit V1 (repo: erato) - revision counter, conditional save, 409, snapshots (~380 lines)
Specs: `composition-versioning: revision counter`, `Saves conditional on expected revision`, `409 carries current state`, `snapshot deduplicated and bounded`; `composition-content: Versioned section writes ... expected revision`, `composition response flat object`. Design AD1-AD3.
Depends on: X1 (error classes).

- [x] V1.1 RED: create `tests/test_section_revisions_repository.py`: insert, prune `rev <= new_rev - 50`, list page, get by rev, newest-at-or-below, delete by composition, unique index `uq_section_revisions_comp_section_rev`. Run `.venv/bin/pytest tests/test_section_revisions_repository.py` -> failure.
- [x] V1.2 RED: create `tests/test_versioning_service.py`: `update_versioned_section` with matching `expected_rev` returns BEFORE doc and bumps; `expected_rev=0` matches missing `section_revs`; stale -> `SectionConflictError` with `current_rev`, `content`, `author`, `updated_at` (newest snapshot at or below, else `author` null and composition `updated_at`); no `expected_rev` = last-write-wins and revision still bumps; identical content creates no snapshot; snapshot failure is swallowed and logged; deleted composition -> 404 not 409; cascade delete of snapshots on composition delete.
- [x] V1.3 RED: extend `tests/test_sections_router.py`: `PUT ...?expected_rev=<int>` 200 returns section model plus `rev`; 409 payload per AD3; invalid body 422 before conflict check; negative `expected_rev` 422; todos endpoint unchanged (bare array, no `rev`); `GET /api/compositions/{id}` exposes `section_revs` defaulting to 0 (extend `tests/test_compositions_router.py`).
- [x] V1.4 GREEN: create `app/db/repositories/section_revisions.py`; modify `app/db/repositories/compositions.py` (`update_versioned_section`); create `app/services/versioning_service.py`; `app/core/errors.py` add `SectionConflictError`; modify `app/routers/sections.py` (query param, `*WriteResponse` models in `app/schemas/compositions.py`), `app/routers/compositions.py` response adds `section_revs`; `app/services/composition_service.py` cascade delete of revisions.
- [x] V1.5 GREEN: add `SectionRevisionsRepository` to `REPOSITORIES` in `scripts/ensure_indexes.py` and extend `tests/test_ensure_indexes_script.py` (RED first, then GREEN) including its `ROLLBACK_INDEXES` entry (`--rollback` flag introduced here, reused by B1).
- [x] V1.6 REFACTOR + full `.venv/bin/pytest tests/`.
- [x] V1.7 Commit (Spanish), e.g. `feat(versionado): detecta conflictos por seccion y registra snapshots`.


### Unit V2 (repo: erato) - history list/get/restore (~250 lines)
Specs: `composition-versioning: History listing and restore MUST be gated through PlanPolicy`. Design API contracts (history), AD5.
Depends on: V1.

- [x] V2.1 RED: create `tests/test_history_router.py`: list (`limit`, `before_rev`, `next_before_rev`), get by rev, restore with required `expected_rev` (creates a new revision, 409 on stale, 422 when missing); `require(EDIT)` first (viewer 403, non-member 404) then gate (`plan_gate_history` 403 with deny stand-in, receives only the user id); unknown section/rev 404; retention cap visible (51st save hides rev 1).
- [x] V2.2 GREEN: create `app/routers/history.py`, `app/schemas/history.py`; extend `app/services/versioning_service.py`; include router in `app/main.py`.
- [x] V2.3 REFACTOR + `.venv/bin/pytest tests/`.
- [x] V2.4 Commit (Spanish), e.g. `feat(historial): lista y restaura versiones de una seccion`.


### Unit V3 (repo: erato) - dirty-section saves and conflict dialog (~330 lines)
Specs: `composition-versioning: The UI MUST save only dirty sections and resolve conflicts per section`; `app-shell-and-navigation: composition page MUST host ... a conflict dialog`. P2.
Depends on: V1.

- [x] V3.1 RED: `frontend/tests/features/use-section-save.spec.ts`: only dirty sections are sent; `Promise.allSettled`; revisions and baseline update on 200; one queued conflict per 409; "Sobrescribir con la mia" resends with `expected_rev = current_rev`; "Cargar la version guardada" replaces local value/baseline; Escape closes without losing the local edit; todos last-write-wins. Run `cd frontend && npm run test:unit -- tests/features/use-section-save.spec.ts` -> failure.
- [x] V3.2 RED: `frontend/tests/api/compositions.spec.ts` extension: `expected_rev` query, `rev` in responses, typed error exposing `error` code (`SectionConflictError`-like) from `frontend/src/api/client.ts`.
- [x] V3.3 GREEN: modify `frontend/src/api/compositions.ts` and `frontend/src/api/client.ts` (error code); create `frontend/src/features/compositions/useSectionSave.ts` and `SectionConflictDialog.vue` (built on `AppModal`); replace `saveAll()` in `frontend/src/features/compositions/CompositionDetailView.vue`.
- [x] V3.4 REFACTOR + `cd frontend && npm run test:unit && npm run build`.
- [x] V3.5 Commit (Spanish), e.g. `feat(composiciones): guarda solo secciones modificadas y resuelve conflictos`.

### Unit V4 (repo: erato) - history panel (~280 lines)
Specs: `composition-versioning: A history panel MUST let editors browse and restore versions`; `plan-policy-port: Policy-gated behavior MUST degrade without data loss`.
Depends on: V2, V3 (and `frontend/src/api/entitlements.ts` from FX is NOT required: panel reads the 403 `plan_gate_history`; entitlements hook is wired in FX/F3).

- [x] V4.1 RED: `frontend/tests/features/section-history-panel.spec.ts`: lists revisions with author/date, previews content, restores via `expected_rev`, shows a notice (no data loss) when the API answers `plan_gate_history`, hidden for viewers.
- [x] V4.2 GREEN: create `frontend/src/api/history.ts`, `frontend/src/features/compositions/SectionHistoryPanel.vue`; host it in `CompositionDetailView.vue`.
- [x] V4.3 REFACTOR + `cd frontend && npm run test:unit && npm run build`.
- [x] V4.4 Commit (Spanish), e.g. `feat(historial): agrega el panel de versiones en la composicion`.

---

## Phase 4: Public `erato`, bands chain (feature-branch-chain on `preview`)

### Unit B1 (repo: erato) - bands repository, indexes, invitation `target` (~280 lines)
Specs: `bands-and-membership: Invitations MUST target a band and carry no role`, `The migration MUST be idempotent ...` (index parts). Design AD8 (repo parts), AD14 (indexes), D3/D4.
Depends on: X1.
B1 adds `redeem_band_invitation` and leaves the legacy composition redeem untouched until F3 (author decision 2026-10-07).

- [x] B1.1 RED: create `tests/test_bands_repository.py`: insert shape `{name, owner_id, members:[{user_id, role:"owner"}], pending_transfer:null, created_at, updated_at}`; get; list by member; rename; `remove_member`; unique-by-structure behaviors; indexes `idx_bands_owner_id`, `idx_bands_members_user_id`. Run `.venv/bin/pytest tests/test_bands_repository.py` -> failure.
- [x] B1.2 RED: extend `tests/test_invitations_repository.py`: `create_band_invitation` with `target {type:"band", id}` and no role; `list_by_band`; `delete_by_band`; multi-use redeem (no `used_at` set for band targets, token reusable until expiry); legacy invitation without `target` -> `GoneError` `invitation_legacy` (410); expired -> `invitation_expired` (410, not 401).
- [x] B1.3 RED: extend `tests/test_ensure_indexes_script.py`: `BandsRepository` in `REPOSITORIES`, `idx_compositions_band_id`, `idx_invitations_target` replaces `idx_invitations_composition_id`, `--rollback` drops only names added by this change (`ROLLBACK_INDEXES`).
- [x] B1.4 GREEN: create `app/db/repositories/bands.py`; modify `app/db/repositories/invitations.py`, `app/db/repositories/compositions.py` (`idx_compositions_band_id`), `scripts/ensure_indexes.py`.
- [x] B1.5 Dry-run first: run `python -m scripts.ensure_indexes` against a scratch DB (`MONGODB_DB=erato_scratch`) and then `python -m scripts.ensure_indexes --rollback`; record output. Never against production.
- [x] B1.6 REFACTOR + full `.venv/bin/pytest tests/`; commit deferred to Claude per author instruction (Spanish), e.g. `feat(bandas): agrega el repositorio de bandas, indices e invitaciones por banda`.

Verification (2026-10-07): RED bands: 1 collection error (missing module); invitations: 2 failed, 3 passed (missing band methods); indexes: 1 failed, 6 passed (missing bands registration). GREEN focused: 14 passed; full suite: 140 passed. Scratch bootstrap and rollback: exit 0 each; rollback retains the V1 registration and adds only the four B1 index names.

### Unit B1M (repo: erato) - migration and restore scripts, dry-run first (~300 lines)
Specs: `bands-and-membership: The migration MUST be idempotent, safe by default and reversible`. Design AD14. Rollback plan in proposal.
Depends on: B1.

- [x] B1M.1 RED: create `tests/test_migrate_bands.py`: default is DRY RUN (prints affected ids, writes nothing, exit 0); `--apply` without `--confirm-db` refused; `--confirm-db` mismatching `MONGODB_DB` refused; `--apply` writes `backups/migrate_bands-<UTC>.json` (canonical extended JSON with `compositions[{_id, members}]` and full legacy `invitations`), fsynced BEFORE any mutation and aborts if the write fails (simulate unwritable dir: no mutation); apply sets `members: []` for compositions with null/absent `band_id` and non-empty `members`, deletes legacy invitations (`composition_id` present, `target` absent), drops `idx_invitations_composition_id`, creates `idx_invitations_target`; second run prints "nada que migrar", exit 0; compositions with `band_id` untouched.
- [x] B1M.2 RED: restore tests: `scripts/restore_bands_migration.py --backup <file> --confirm-db <name>` re-applies `members`, re-inserts invitations by original `_id` ignoring `DuplicateKeyError`, recreates the legacy index; round trip equals the original data; mismatched `--confirm-db` refused.
- [x] B1M.3 GREEN: create `scripts/migrate_bands.py` and `scripts/restore_bands_migration.py`; add `backups/` to `.gitignore` (edit `.gitignore`).
- [ ] B1M.4 **Partially done: scratch done; erato_preview pending, run by the author.** Dry-run first on a scratch DB: seed legacy data, run `python -m scripts.migrate_bands` (dry run), then `--apply --confirm-db erato_scratch`, then re-run (idempotent), then restore; record outputs. Against `erato_preview` only: dry run, and apply only when the author instructs (empty DB reports nothing to do).
- [x] B1M.5 REFACTOR + `.venv/bin/pytest tests/test_migrate_bands.py`; commit (Spanish), e.g. `feat(migracion): agrega la migracion de bandas con respaldo y restauracion`.

B1M validation record (2026-10-07; changes uncommitted, Claude commits):
- RED `tests/test_migrate_bands.py -k 'not restore' -q`: `6 failed, 3 deselected in 0.81s`; all `ModuleNotFoundError: scripts.migrate_bands`. RED `-k restore -q --tb=short`: `3 failed, 6 deselected in 0.54s`; all `ModuleNotFoundError: scripts.restore_bands_migration`.
- GREEN focused: `9 passed in 1.05s`; after refactor: `9 passed in 1.10s`. Full `tests/`: `149 passed in 12.31s`; after refactor: `149 passed in 12.14s`.
- Scratch CLI dry run (exit 0): `DRY RUN`, composition ids `000000000000000000000001`, `000000000000000000000002`, invitation id `000000000000000000000004`; documents unchanged, no backup.
- Scratch apply `--apply --confirm-db erato_scratch` (exit 0): `Respaldo: backups/migrate_bands-20261007T231852.093180Z.json`; `Migración completada: 2 composiciones, 1 invitaciones`. Second apply (exit 0): `nada que migrar`.
- Scratch restore `--backup <temporary backup> --confirm-db erato_scratch` (exit 0): `Restauración completada: 2 composiciones, 1 invitaciones`; exact document round trip verified. Scratch database dropped and verified empty; temporary directory and backup deleted. No manual commands against other databases; pytest uses dedicated test databases as authorized. Initial scratch guard stopped on existing collections; all were verified empty before seeding. No `erato_preview` run.

### Unit B2 (repo: erato) - band context and role resolution (~350 lines)
Specs: `sharing-and-visibility: Effective role MUST be resolved in a fixed order including band roles`, `Band-derived and invited write access MUST end while the band is not active`; `bands-and-membership: Role-derived access enforced on the backend`; `composition-content: advisory user role`. Design AD7.
Depends on: B1.

- [x] B2.1 RED: extend `tests/test_permissions.py`: `resolve_role(uid, access, band)` order owner > composition member role (honored when `band_id` is null OR `band.is_member`) > band member with `band_editable` EDITOR / otherwise VIEWER > public VIEWER > None; a ex-member's composition role is ignored; compositions without `band_id` unchanged. Pure, no DB.
- [x] B2.2 RED: extend `tests/test_deps_require.py` and create `tests/test_band_roles.py`: `band_context` loads only when `band_id` set and a user present (projection `{owner_id, members.user_id}`, one query); non-VIEW action by non-owner on a band composition calls `policy.is_band_active` and raises 403 `band_inactive`; owner keeps content edits; inactive band blocks sharing changes (enforced at sharing call sites in B5b and B7, not in require; orchestrator resolution per spec and design, 2026-10-07); non-member 404; `GET /api/compositions/{id}` and by-slug return `user_role` with band roles plus `band_id`, `band_editable`, `band_active`; list returns `band_id`, `via_band` (extend `tests/test_compositions_router.py`, `tests/test_user_role_response.py`).
- [x] B2.3 GREEN: modify `app/core/permissions.py` (`BandContext`, `resolve_role`), `app/deps.py` (`band_context`, band-active check in `require()`), `app/db/repositories/compositions.py` (`list_by_user(user_id, band_ids)`), `app/routers/compositions.py` and `app/schemas/compositions.py`, `app/services/composition_service.py` (`list_for_user` with band ids).
- [x] B2.4 REFACTOR + full `.venv/bin/pytest tests/` (existing 404-vs-403 and members-projection tests must still pass: `tests/test_404_vs_403.py`, `tests/test_members_projection.py`).
- [ ] B2.5 Commit (Spanish), e.g. `feat(permisos): resuelve el rol con contexto de banda y bloquea escritura en bandas inactivas`.


B2 validation (2026-10-07): RED `tests/test_permissions.py` + `tests/test_deps_require.py`: 24 failed, 9 passed (missing `BandContext` / `band_context`). RED `tests/test_band_roles.py` + `tests/test_compositions_router.py` + `tests/test_user_role_response.py`: 4 failed, 5 passed (viewer instead of editor, missing band list item, missing `band_id`). GREEN focused command including `test_404_vs_403.py` and `test_members_projection.py`: 46 passed; full `.venv/bin/pytest tests/`: 177 passed. Owner exemption follows AD7; inactive sharing checks belong to B5b/B7. B2.5 remains for Claude.

### Unit B3 (repo: erato) - core gate call sites (~220 lines)
Specs: `plan-policy-port: Plan-gate refusals`, `sharing-and-visibility: Sharing with people MUST be gated by the policy`; `media-storage: Upload credentials MUST be refused when the demo count quota is reached`. Design AD6 table, AD15.
Depends on: B2, V2 (history gate already in place; asserted here too).

- [x] B3.1 RED: extend `tests/test_plan_policy_contract.py`: deny-all stand-in is hit by every call site in the AD6 table that exists after this unit: band-attach `PATCH .../band` with non-null `band_id` (`can_share_with_people` then `is_band_active`), `PUT .../members/{uid}`, history, demo signature/confirm; detach is never gated; user-scoped questions get only the user id; limit 1 and inactive-band stand-ins. Band-attach and member-role gate assertions move to B7, where those endpoints are created (orchestrator resolution per tasks wording, 2026-10-07).
- [x] B3.2 RED: extend `tests/test_demos_router.py`: `demo_limit(user)` reached at credential issue -> 403 `plan_gate_demo_limit`; `confirm_demo` guard with filter `demos.{limit-1} $exists False` closes the parallel-upload race (two confirms, one wins); no limit under `UnlimitedPlanPolicy`.
- [x] B3.3 GREEN: modify `app/services/demo_service.py` (`policy` constructor arg, AD15), `app/db/repositories/compositions.py` (`add_demo_if_below`), `app/routers/demos.py`, `app/services/sharing_service.py` (policy param, gate order), `app/routers/sharing.py`.
- [x] B3.4 REFACTOR + full `.venv/bin/pytest tests/`.
  - [x] Commit (Claude): `feat(plan): aplica la cuota de demos e inyecta la política en compartir`.

### Unit B5a (repo: erato) - band creation and read (~300 lines)
Specs: `bands-and-membership: A user MAY create a band when the policy allows it`, `The core MUST expose band creation and removal as a service operation for a host`, `Band data MUST be visible only to members`. Design AD11 (core part), AD18.
Depends on: B3.

- [x] B5a.1 RED: create `tests/test_bands_service.py`: `create_for_user` shape (`members [{owner}]`, `pending_transfer` null), name 1-80 after strip else 422 `validation_error`, no policy gate; `create` calls `policy.can_create_band(user)` and answers 403 `plan_gate_band_creation` on deny; unlimited allows any number of bands per user; `delete_band` order: detach compositions (`band_id` null, `band_editable` false, `members: []`), delete band invitations, delete band doc; second call and unknown/malformed id are no-ops.
- [x] B5a.2 RED: create `tests/test_bands_router.py`: `POST /api/bands` 201 / 403 / 422 (`extra="forbid"`); `GET /api/bands` lists only the user's bands; `GET /api/bands/{id}` member 200 with `BandResponse` (`seats_used`, `seat_limit`, `active`, `pending_transfer` null, expired reported null), non-member 404; `PATCH` rename owner only (403 otherwise). BandSummary = {id, name, owner_id, user_role, seats_used, seat_limit, active} (orchestrator resolution, 2026-10-07).
- [x] B5a.3 GREEN: create `app/services/bands_service.py`, `app/schemas/bands.py` (`BandCreate`), `app/routers/bands.py` (create, list, get, rename); include in `app/main.py`.
- [x] B5a.4 REFACTOR + `.venv/bin/pytest tests/` completed; commit by Claude: `feat(bandas): crea y consulta bandas con operaciones invocables por el host`.

- [ ] B5a commit (Claude): `feat(bandas): crea y consulta bandas con operaciones invocables por el host`.

Observed B5a TDD output (2026-10-07):
- RED service: `.venv/bin/pytest tests/test_bands_service.py -q` -> `ModuleNotFoundError: No module named 'app.services.bands_service'`; `1 error in 0.15s`.
- RED router: `.venv/bin/pytest tests/test_bands_router.py -q` -> absent routes returned 404 instead of 401/200/403; `3 failed in 0.61s`.
- First implementation run: `2 failed, 4 passed in 1.21s`; corrected test spies (collection instances were not shared; batch lookup side effect referenced the patched method).
- GREEN: `.venv/bin/pytest tests/test_bands_service.py tests/test_bands_router.py` -> `6 passed in 0.79s`.
- Full suite: `.venv/bin/pytest tests/` -> `192 passed in 14.16s`.

### Unit B5b (repo: erato) - invitations, atomic seat join, member removal, atomic role set (~320 lines)
Specs: `bands-and-membership: Invitations MUST target a band and carry no role`, `Joining MUST honor the policy seat limit atomically`; `sharing-and-visibility: invite roles`. Design AD4, AD8, OD-6 data flow.
Depends on: B5a.

- [x] B5b.1 RED: create `tests/test_bands_invites.py`: owner creates/lists/deletes band invitations (`invite_url` built with `build_app_url`); body with `role` -> 422; redeem via `POST /api/auth/redeem-invite` returns `{band_id, status: "joined"|"already_member"}`; invitation multi-use by two users; unknown token 404; legacy 410; expired 410; inactive band -> 403 `band_inactive`.
- [x] B5b.2 RED: create `tests/test_seat_race.py`: `add_member_if_seat` with limit from `policy.seat_limit`; `asyncio.gather` of N redeems at the last seat admits exactly one and the rest get 409 `band_full`; already member is not duplicated; `None` limit means unbounded.
- [x] B5b.3 RED: extend `tests/test_compositions_repository.py`: `set_member_role` is atomic (two concurrent calls leave one entry, no duplicates).
- [x] B5b.4 GREEN: modify `app/db/repositories/bands.py` (`add_member_if_seat`), `app/db/repositories/compositions.py` (`set_member_role`), `app/db/repositories/invitations.py`, `app/services/bands_service.py` (invites, redeem/join), `app/routers/bands.py`, `app/routers/auth.py` (`redeem-invite` returns the join result), `app/schemas/bands.py`. redeem-invite dispatches on target: band tokens join the band; tokens without target keep the legacy composition redeem until F3.2b (orchestrator resolution consistent with the B1 author decision, 2026-10-07).
- [x] B5b.5 REFACTOR + `.venv/bin/pytest tests/`; commit by Claude: `feat(bandas): invita con enlaces multiuso y une miembros con límite atómico de plazas`.

B5b validation record (2026-10-07; uncommitted, Claude commits):
- RED focused run: `5 failed, 5 passed in 1.09s`. `test_bands_invites.py`: create returned `404 != 201`, missing `invite_url`; `test_seat_race.py`: missing `invite_url` and `AttributeError: add_member_if_seat`; `test_compositions_repository.py`: `AttributeError: set_member_role`.
- First GREEN attempt: `1 failed, 9 passed in 1.07s`; corrected expiry comparison for Mongo millisecond precision and naive UTC. GREEN: `10 passed in 1.04s`.
- REFACTOR: imports moved to module scope. An accidentally overlapping focused/full run shared `erato_test` cleanup: focused `1 failed, 9 passed`, full `3 failed, 195 passed`; discarded as concurrent harness interference and rerun sequentially without code changes.
- Final focused `.venv/bin/pytest tests/test_bands_invites.py tests/test_seat_race.py tests/test_compositions_repository.py`: `10 passed in 1.00s`. Full `.venv/bin/pytest tests/`: `198 passed in 14.13s`. `git diff --check` clean.
- Legacy HTTP response preserved per orchestrator resolution; B1 repository still rejects legacy tokens with 410 on the band-only method. No B6/B7 behavior, schema/index changes, or manual database operations.
- [ ] B5b commit (Claude): `feat(bandas): invita con enlaces multiuso y une miembros con límite atómico de plazas`.

### Unit B6a (repo: erato) - leave and remove (~200 lines)
Specs: `bands-and-membership: Members MUST be able to leave, detaching their compositions`. Design AD7 note, AD9.
Depends on: B5b.

- [x] B6a.1 RED: create `tests/test_bands_leave.py`: owner leaving -> 409 `owner_must_transfer`; leave order (detach own compositions with `members: []`, then `$pull`); compositions of others stay unchanged; retry after simulated mid-failure is harmless; owner removes a member (same steps; cannot remove self); a transfer aimed at the departing member is cleared (conditional second update); a detached composition no longer honors old member roles (AD7).
- [x] B6a.2 GREEN: implement `leave`/`remove_member` in `app/services/bands_service.py`, `app/db/repositories/compositions.py` (`detach_owner_band_compositions`), `app/db/repositories/bands.py`; routes `POST /api/bands/{id}/leave`, `DELETE /api/bands/{id}/members/{uid}` in `app/routers/bands.py`.
- [x] B6a.3 REFACTOR + `.venv/bin/pytest tests/`. Commit by Claude: `feat(bandas): permite salir de una banda y quitar miembros`.

B6a validation (2026-10-07): RED `.venv/bin/pytest tests/test_bands_leave.py`: 9 failed (missing routes / service methods and conditional transfer cleanup). GREEN same command: 9 passed; full `.venv/bin/pytest tests/`: 207 passed. Shared detach helper preserves AD9 ordering; no model changes, transfer implementation or sharing changes. Changes left uncommitted for Claude.

### Unit B6b (repo: erato) - ownership transfer (~300 lines)
Specs: `bands-and-membership: Ownership transfer MUST be a request that expires after 14 days`. Design AD10, AD4 rows, OD-1 (unblocked).
Depends on: B5b (needs B6a for the cleared-transfer-on-leave interaction).

- [x] B6b.1 RED: create `tests/test_bands_transfer.py`: request (owner, target is member, creates `pending_transfer` with 14 d expiry); target not member -> 409 `not_a_band_member`; non-expired pending -> 409 `transfer_pending` with existing value unchanged; expired pending is overwritten; transfer to self -> 422; cancel (owner) and reject (target) via `DELETE .../transfer` 204, others 403, absent/expired 404 `transfer_not_found`; accept: other target 403, absent 404, expired -> lazily cleared and 410 `transfer_expired`; `confirm_band_transfer` is called BEFORE any write (stand-in recording order); refusal (`False`) -> 409 `transfer_not_confirmed` with owner, roles and `pending_transfer` untouched; policy `AppError` propagates unchanged; success swaps `owner_id` and member roles with `arrayFilters` and nulls `pending_transfer`; lost swap (owner canceled in the window) -> 404 and `transfer_swap_lost` warning logged; `GET` reports expired transfer as null without writing. Accept with a target no longer in the band clears the stale request and answers 409 not_a_band_member; the swap filter also requires the target to be a member (orchestrator resolution, 2026-10-07).
- [x] B6b.2 GREEN: modify `app/db/repositories/bands.py` (`request_transfer`, `clear_transfer`, `swap_owner`), `app/services/bands_service.py`, `app/routers/bands.py` (`POST /transfer`, `DELETE /transfer`, `POST /transfer/accept`), `app/schemas/bands.py`.
- [x] B6b.3 REFACTOR + `.venv/bin/pytest tests/`; commit by Claude: `feat(bandas): agrega transferencia de propiedad con vencimiento a los 14 días`.

B6b execution evidence (2026-10-07): RED `.venv/bin/pytest tests/test_bands_transfer.py`: 13 failed in 1.09s (missing transfer routes returned generic 404). Initial GREEN: 13 passed in 0.98s. Additional edge-case RED: stale departed target with expired request returned 410 instead of resolved 409 (1 failed, 15 passed in 1.12s). Final GREEN `.venv/bin/pytest tests/test_bands_transfer.py`: 16 passed in 1.18s; `.venv/bin/pytest tests/`: 239 passed in 17.31s. Refactor: shared expiry/error helpers and conditional cleanup; `git diff --check` clean. B6b.3 commit remains pending for Claude; no git write commands run.

### Unit B7 (repo: erato) - share a composition with a band (~260 lines)
Specs: `bands-and-membership: Compositions MUST be shareable with a band`; `sharing-and-visibility: Band sharing MUST be a control separate from visibility`, `An invite MUST support an editor role and a viewer-only role` (member roles restricted to band members), `Only invited editor-role users MUST be able to edit a public composition`, `A private composition MUST be visible only to invited users`. Design AD6, AD7, AD9 (detach), risks table (rewrite tests first).
Depends on: B5b.

- [x] B7.1 RED (tests rewritten first): rewrite `tests/test_sharing_router.py` and `tests/test_sharing_roles.py` for the new model: composition `/invites` endpoints are kept until F3 (author decision 2026-10-07); `PATCH /api/compositions/{id}/band {band_id, band_editable}` owner only, owner must be a member, sharing gate then band active, `band_editable=false` -> viewers (P9); detach (`band_id: null`) empties `members`, sets `band_editable` false and is never gated; `PUT /api/compositions/{id}/members/{uid}` only for users in the composition's band (else 409 `not_a_band_member`); `DELETE .../members/{uid}`; legacy `members` roles ignored after the user leaves the band (AD7); public visibility still allows anonymous view; private composition hidden from non-invited. PUT and DELETE /api/compositions/{id}/members/{uid} on a band composition MUST refuse with 403 band_inactive while the band is inactive (spec sharing-and-visibility: sharing changes refused while inactive).
- [x] B7.2 GREEN: modify `app/services/sharing_service.py` (band attach/detach, member roles, keep composition invitation creation until F3), `app/routers/sharing.py` (keep `/invites` until F3, add `/band`, `/members/{user_id}`), `app/db/repositories/compositions.py` (`set_band`, `detach_all_band_compositions`).
- [x] B7.3 REFACTOR + full `.venv/bin/pytest tests/`; commit by Claude: `feat(compartir): comparte composiciones con una banda y limita los roles a sus miembros`.


B7 validation (2026-10-07; author decision keeps legacy invitations until F3):
- RED focused command: `tests/test_sharing_router.py` 1 failed / 2 passed; `tests/test_sharing_roles.py` 1 failed / 1 passed; `tests/test_plan_policy_contract.py` 12 failed / 11 passed; `tests/test_band_share.py` 2 failed. Total: 16 failed, 14 passed in 1.85s. Missing routes returned 404; repository test raised missing `set_band` AttributeError.
- GREEN `.venv/bin/pytest tests/test_sharing_router.py tests/test_sharing_roles.py tests/test_plan_policy_contract.py tests/test_band_share.py`: 30 passed in 1.75s. Full `.venv/bin/pytest tests/`: 223 passed in 15.92s.
- REFACTOR: band deletion reuses `detach_all_band_compositions`; existing compensation tests pass. No model/index changes. Legacy invite handlers/service methods unchanged; auth redeem and invitations repository byte-for-byte unchanged.
- [x] B7 commit by Claude (see B7.3).

### Unit FX (repo: erato) - payment-only frontend extension point (~220 lines)
Specs: `plan-policy-port: The frontend MUST expose an extension point for cloud pages`, `The core band-creation action MUST adapt to the entitlements mode`; `app-shell-and-navigation: The shell MUST expose an extension point for host pages`. Design AD12.
Depends on: X1 (entitlements endpoint). Placed after B7 in the chain but only X1 is a hard dependency.

- [x] FX.1 RED: `frontend/tests/app/create-app.spec.ts`: `createEratoApp()` without payments registers no `/plan` route and renders no nav extras; with `payments` the route resolves inside the shell (shared auth state); factory throws at startup when a route path does not start with `/plan`, when a route has no `meta.requiresAuth`, or when `bandCreationEntry` does not resolve to a registered extension route; nav items render for authenticated users only; extension routes are inserted before the catch-all. Run `cd frontend && npm run test:unit -- tests/app/create-app.spec.ts` -> failure.
- [x] FX.2 RED: `frontend/tests/features/use-band-creation.spec.ts` (three states: `direct` opens core form; `hand_off` + entry navigates via `router.push`; `hand_off` without entry returns not-actionable with explanation) and `frontend/tests/features/use-entitlements.spec.ts` (cached; refresh on login/logout, band join/leave, after returning from a `/plan*` route; gating from the endpoint, never plan names). Band join/leave refresh hooks are wired in F2 via useEntitlements().refresh() (orchestrator resolution, 2026-10-07).
- [x] FX.3 GREEN: create `frontend/src/app.ts` (`EXTENSION_ROUTE_PREFIX`, `PaymentExtension`, `createEratoRouter`, `createEratoApp`, `PAYMENT_EXTENSION_KEY`), `frontend/src/shared/AppNavExtras.vue`, `frontend/src/api/entitlements.ts`, `frontend/src/features/plan/useEntitlements.ts`, `frontend/src/features/bands/useBandCreation.ts`; modify `frontend/src/main.ts` (`ensureAuthReady(); createEratoApp().mount('#app')`) and `frontend/src/router/index.ts` (keep exporting `scrollBehavior`, `setupNavigationGuard`, `routes`, default singleton built by `createEratoRouter()`); existing `frontend/tests/router/guard.spec.ts` must still pass. AppNavExtras is wired into the dashboard only; F2 adds it to the band screen (orchestrator resolution, 2026-10-07).
- [x] FX.4 REFACTOR + `cd frontend && npm run test:unit && npm run build`.

Observed FX verification (2026-10-07):
- RED: each requested spec ran separately with `npm run test:unit -- <spec>` and exited 1: create-app and use-band-creation reported `Failed to resolve import "@/app"`; use-entitlements reported `Failed to resolve import "@/features/plan/useEntitlements"` (one failed suite each, modules absent).
- Additional observed RED regressions: first consumer unmount stops login refresh (`expected "getEntitlements" to be called 1 times, but got 0 times`); logout retains a nav link (`expected ... to have a length of +0 but got 1`); payment-return refresh before a consumer mounts retains stale permissions on logout (`expected ... to be null`). Each was corrected and its spec rerun green.
- GREEN: focused specs plus guard passed (22 tests before the final cache regression); final `cd frontend && npm run test:unit` passed 51 files / 337 tests; `npm run build` passed `vue-tsc` and Vite (129 modules). Existing suite emits Vue test-harness warnings.
- Refactor: navigation guard/scroll behavior extracted unchanged to avoid app/router circular imports; auth state made reactive; detached cache watcher survives view unmount; generations discard stale responses. No new styles, tokens or dependencies. Commit remains for Claude.

- [x] FX.5 Commit by Claude: `feat(frontend): agrega el punto de extensión para páginas de pago`.

### Unit F2 (repo: erato) - band management screen (~380 lines)
Specs: `app-shell-and-navigation: The app MUST provide a band management screen with its own route`; `plan-policy-port: The core band-creation action MUST adapt to the entitlements mode`. Design AD12 (`BandCreateForm`).
Depends on: B6b, FX.

- [x] F2.1 RED: `frontend/tests/features/band-view.spec.ts`: `/bands` and `/bands/:id` require auth; lists bands; direct mode shows `BandCreateForm` and no payment control; `hand_off` with entry navigates, without entry control is disabled with an explanation; shows members, seats used/limit, invite link create/copy/delete, remove member, leave (hidden for owner), transfer request / cancel / accept / reject; maps `error` codes (`band_full`, `transfer_pending`, `owner_must_transfer`, ...) to Spanish messages; no `!`/emoji.
- [x] F2.2 GREEN: create `frontend/src/api/bands.ts`, `frontend/src/features/bands/BandView.vue`, `BandCreateForm.vue` (+ small subcomponents as needed); modify `frontend/src/router/routes.ts` (`/bands`, `/bands/:id`, `meta.requiresAuth`); modify `frontend/src/features/compositions/DashboardView.vue` to link to bands and render `AppNavExtras` (band link only here; band-derived marker is F3).
- [x] F2.3 REFACTOR + `cd frontend && npm run test:unit && npm run build`.
- [x] F2.4 Commit by Claude: `feat(bandas): agrega la pantalla de gestión de bandas`.

F2 validation record (2026-10-07; uncommitted, Claude commits):
- RED `cd frontend && npm run test:unit -- tests/api/bands.spec.ts`: exit 1, one failed suite, `Failed to resolve import "@/api/bands"` (module absent). RED `npm run test:unit -- tests/features/band-view.spec.ts`: exit 1, one failed suite, `Failed to resolve import "@/features/bands/BandView.vue"` (view absent).
- Initial focused GREEN: API 27 passed; view 23 passed / 1 failed due to a date-only fixture rendered in the local timezone. Made the date assertion timezone-aware. Regression RED: accepting ownership did not load invitations (`listBandInvites` called 0 times; 1 failed / 28 passed); late transfer response restored the previous detail after navigation (`Jazz` instead of `Tus bandas`; 1 failed / 29 passed). Both corrected before final GREEN.
- Final focused view: 30 passed. Final full `cd frontend && npm run test:unit`: 53 files / 398 tests passed. `npm run build`: vue-tsc and Vite passed, 137 modules, built in 3.09s. First build exposed the generic 204 return type; corrected before final build. Existing test-harness warnings remain.
- Uses FX `useBandCreation` for all three states; `AppNavExtras` in the band top bar; refresh after successful leave/transfer accept; cancel/reject share the backend DELETE endpoint. Invite URLs are only copyable immediately after creation because invite listing contains no token or URL. Invite acceptance remains F3.
- No new CSS, dependencies, model/backend changes, git writes or edits under the design system/landing or to pasos.md. New production files: 315 lines; new tests: 315 lines (630 total). Production scope stays below the ~380-line target; total exceeds it due to 57 contract/UI tests, including errors, permissions, clipboard failure and navigation races. F2.4 remains pending for Claude.

### Unit F3 (repo: erato) - sharing modal, dashboard, read-only banner (~350 lines)
Specs: `sharing-and-visibility: Band sharing separate from visibility`, `dashboard MUST list compositions shared with the user's bands`, `A read-only banner MUST explain inactive bands`; `app-shell-and-navigation: Editing controls MUST reflect read-only state`, `No deferred PDF affordance`; `plan-policy-port: Policy-gated behavior degrades without data loss`.
Depends on: B7, FX, V4 (panel gating via entitlements).

F3 split into F3a and F3b, orchestrator decision 2026-10-07.

- [x] F3.1a RED (F3a): update `frontend/tests/features/sharing-modal.spec.ts`, `frontend/tests/features/sharing.spec.ts`, `frontend/tests/api/sharing.spec.ts`, `frontend/tests/features/invite-accept-view.spec.ts`: exactly two visibility options, separate band control with `band_editable`, member roles restricted to band members, sharing gate with public link available, invite-accept routes to the band and refreshes entitlements; backend legacy cleanup tests rewritten before implementation.
- [x] F3.1b RED (F3b): update `frontend/tests/features/dashboard-view.spec.ts`; create `frontend/tests/features/read-only-banner.spec.ts`: dashboard lists band compositions with a band-derived marker; inactive-band banner, editing controls disabled; history panel gated by `can_view_history`; no PDF affordance.
- [x] F3.2a GREEN (F3a): modify `frontend/src/api/sharing.ts`, `frontend/src/features/sharing/SharingModal.vue`, `frontend/src/features/sharing/InviteAcceptView.vue`; reuse bands API, entitlements and existing design-system controls; extend `bandErrors.ts` with sharing and invitation messages.
- [x] F3.2c GREEN (F3b): modify `frontend/src/features/compositions/DashboardView.vue`, `frontend/src/features/compositions/CompositionDetailView.vue`; create `frontend/src/features/compositions/ReadOnlyBanner.vue`; disable editing controls, gate history, remove PDF affordances without backing behavior.
- [x] F3.2b GREEN (F3a): remove legacy composition `/invites` endpoints, composition invitation methods from `SharingService`, legacy repository creation/redemption/listing, and the legacy auth redeem branch; tokens without target return 410 `invitation_legacy` through band redemption. `/members` projects owner and existing member roles only; legacy pending invitations are excluded. Tests updated in the same change (author decision 2026-10-07).
- [x] F3.3a REFACTOR (F3a): full backend/frontend suites and frontend build; recorded below. Manual check in the browser by the author (2026-10-07): OK.
- [x] F3.3b REFACTOR (F3b): `cd frontend && npm run test:unit && npm run build` after F3b.
- [x] F3.4 Commits by Claude: F3a `feat(compartir): comparte composiciones con bandas y elimina invitaciones antiguas`; F3b `feat(composiciones): indica acceso por banda y aplica solo lectura`.

F3a execution evidence (2026-10-07):
- RED backend: `.venv/bin/pytest tests/test_sharing_router.py tests/test_bands_invites.py tests/test_members_projection.py tests/test_invitations_repository.py -q` -> 4 failed / 6 passed in 1.30s: removed routes still returned 201; legacy token returned 200 rather than 410; projection included 4 rather than 3 entries; legacy repository methods existed.
- RED frontend: four sharing/invite specs -> 32 failed / 4 passed, 3 failed files / 1 passed, in 1.44s: band/member functions absent, legacy exports present, band control absent, redemption navigated to `/compositions/undefined` instead of the band. Additional focus regression -> 1 failed / 15 passed in 1.42s before applying existing `er-focus` class.
- GREEN focused: backend 12 passed in 1.82s; frontend 36 passed across 4 files in 1.68s, then sharing modal 16 passed in 1.65s after four additional checks (focus, inactive bands, minted public slug, load/clipboard errors).
- Final GREEN: `.venv/bin/pytest tests/` -> 237 passed in 22.39s; `cd frontend && npm run test:unit` -> 53 files / 417 tests passed in 11.58s; `npm run build` -> vue-tsc and Vite passed, 137 modules, built in 1.44s. Initial build caught excess `band_id` in a test literal; corrected using a typed-compatible fixture variable. Existing test-harness warnings remain.
- REFACTOR: shared typed API request/error handling; band/invitation messages reuse `bandErrors`; modal loads its own band context on open, keeping F3b views untouched. No new CSS, components, dependencies, model/index changes, migration, git writes or edits to landing, pasos.md or the design system. No new files. Production additions: 219 lines; test additions: 272 lines; documentation recorded here. Total additions exceed the ~400-line heuristic because the scope also rewrites legacy backend tests and adds contract, confirmation, gating, error and accessibility coverage.

F3b execution evidence (2026-10-07):
- RED: `cd frontend && npm run test:unit -- tests/features/dashboard-view.spec.ts tests/features/read-only-banner.spec.ts` -> 10 failed / 6 passed across 2 failed files in 1.65s. Missing inactive-band status notice, unprotected todo controls and history rendered while entitlements were loading. The marker selector initially also matched the amber status tag; after correcting the selector, reran without the marker -> 1 failed / 5 passed in 1.25s, `expected ['En progreso'] to include 'Compartida con tu banda'`, then restored the marker.
- GREEN focused: dashboard, read-only and history specs -> 30 passed across 3 files in 1.79s. Updated the existing restore integration fixture to explicitly allow history. Initial full suite caught that missing permission fixture (1 failed / 427 passed), corrected before final verification.
- Final GREEN: `cd frontend && npm run test:unit` -> 54 files / 428 tests passed in 11.02s; `npm run build` -> vue-tsc and Vite passed, 139 modules, built in 1.51s. Existing harness warnings remain. `git diff --check` passed.
- REFACTOR: reused ErTag/er-hint for the banner and band marker; centralized editing in canEdit (inactive blocks non-owner editors; owners remain editable; null/undefined active); guarded status writes; history mounts only with an explicit entitlement grant, without resetting composition content. Native disabled fieldset protects every todo control; seven CSS lines reset only its browser border/spacing/min-width, preserving the existing todo panel. No new visual tokens or dependencies.
- DashboardView already lists every API composition; marker belongs in CompositionCard, so DashboardView needs no change. Frontend API interfaces now declare the existing backend band fields; no backend/model changes. ReadOnlyBanner.vue: 14 authored lines; read-only-banner.spec.ts: 118 authored lines. About 184 implementation/test/CSS additions, within the ~300-line heuristic. Only F3b frontend files and this task evidence changed; no git writes, landing, pasos.md or design-system edits. Changes left uncommitted for Claude.

F3b review corrections (2026-10-07):
- RED: `cd frontend && npm run test:unit -- tests/features/read-only-banner.spec.ts` -> 5 failed / 6 passed in 1.69s: `expected 'Tu banda está inactiva' to be 'Banda inactiva'`; history buttons while loading `expected true to be false`.
- GREEN: focused spec -> 11 passed in 1.70s; full `npm run test:unit` -> 54 files / 429 tests passed in 10.83s; `npm run build` -> vue-tsc and Vite passed, built in 1.59s.
- Passed canViewHistory into lyrics, chords and tablature; history buttons require an explicit grant and existing edit access. Replaced banner copy with neutral band wording for public viewers and anonymous visitors, with the requested owner variant. Tests cover loading, denial, grant and revocation, exact banner copy, and no exclamation marks or emoji. No new CSS, dependencies, design-system edits or git writes.

### Unit DOC (repo: erato) - seams contract and runbook completion (~120 lines)
Specs: `plan-policy-port: The core MUST accept external routers and keep a stable app entry`; `preview-deployment: Indexes MUST be bootstrapped`, `Promotion and rollback documented`. Design "docs/seams.md".
Depends on: B6b, FX, F3.

- [x] DOC.1 RED: add a docs-pin test in `tests/test_plan_policy_contract.py` that `docs/seams.md` exists and mentions each port method, `get_plan_policy`, `get_host_capabilities`, `BandsService.create_for_user`, `BandsService.delete_band`, `createEratoApp`, `PaymentExtension`. Observe failure.
- [x] DOC.2 GREEN: create `docs/seams.md` (getters, port methods, entitlements shape, host operations, `createEratoApp` payments option, entry point, import rule `app.*` never `erato.app.*`); complete `docs/runbook-preview.md` (migration dry-run then apply only on `erato_preview`, rollback steps, pointer check, pointer-bump order).
- [x] DOC.3 Run full `.venv/bin/pytest tests/` and `cd frontend && npm run test:unit && npm run build`.
- [x] DOC commit by Claude: `docs(seams): documenta el contrato para erato-cloud y completa el runbook`, plus `fix(frontend): limita la extensión de pagos a rutas bajo /plan` found while documenting.

DOC execution evidence (2026-10-07):
- RED docs pin: `1 failed, 23 deselected in 0.46s`; `AssertionError: docs/seams.md must document the host contract`. GREEN focused: `1 passed, 23 deselected in 0.39s`.
- Full backend: `238 passed in 20.52s`. Frontend: `53 files / 417 tests passed` in 11.75s; `vue-tsc && vite build` passed, 137 modules, built in 1.62s. Existing frontend harness warnings remain.
- Names/signatures and core script flags verified from code; no migration/bootstrap run against preview or production. Cloud commands are documented future host procedures, not verified by accessing erato-cloud.
- Design discrepancies: AD18 uses Motor `AsyncIOMotorDatabase`/`BandDocument`, code uses PyMongo `AsyncDatabase`/`dict`; AD12 declarations live in `extension.ts` and are re-exported by `app.ts`; `/plan` guard is a string prefix, not a path-segment boundary. AD6 injection holds for HTTP, but sharing/demo/versioning service constructors retain unlimited fallbacks when directly constructed without policy.
- Authored lines exceed ~120 because the seven-method contract, actual frontend guards, safe migration/restore limitations and operational pointer/rollback procedures require additional detail. Only the two DOC documents, contract test and this task record changed; no dependencies, git writes, landing/pasos.md edits or erato-cloud access.


---

## Phase 5: Private `erato-cloud` (PRs into `erato-cloud` `preview`; each unit that needs a core change starts only after that `erato` unit merged into `erato` `preview` and bumps the submodule pointer in the same PR)

All paths below are under `/home/bspc/proyectos/erato-cloud/`; requires the folder edit grant (task 0.2). Commit messages in Spanish.

### Unit C0 (repo: erato-cloud) - bootstrap (~250 lines)
Specs: `preview-deployment: App and API MUST deploy as one Vercel project from erato-cloud`, `Indexes MUST be bootstrapped`; `backend-platform: importable as app.main.app and accept host extensions`; design AD13, AD17, Risks (submodule HTTPS, bundle `includeFiles`).
Depends on: X1 merged in `erato` `preview`; author prerequisites.

- [x] C0.1 Set `.gitmodules` `erato` to the HTTPS URL with `branch = preview` and bump the pointer to `erato` `preview` HEAD (verify the pointer equals `preview` HEAD).
- [x] C0.2 RED: create `tests/conftest.py` (reuse the core env fixture shape; `erato/tests/conftest.py` (read-only)) and `tests/test_wiring.py`: `api.index.app is app.main.app`; after `erato_cloud.wiring.install(app)` the overrides for `get_plan_policy` and `get_host_capabilities` are set (capabilities `extensions_available=True`) and the plan router is mounted; `X-Robots-Tag: noindex` header on API responses only when `VERCEL_ENV == "preview"`; `CloudSettings` defaults `free_pro_enabled=False`. Create `pytest.ini` (`pythonpath = . erato`, `asyncio_mode = auto`) and run `.venv/bin/pytest tests/` -> failure.
- [x] C0.3 GREEN: create `api/index.py` (insert `erato/` at the front of `sys.path`, import `app.main.app`, call `install`), `erato_cloud/__init__.py`, `erato_cloud/settings.py`, `erato_cloud/wiring.py` (placeholder policy override finalized in C2; plan router stub), noindex middleware; `requirements.txt` (`-r erato/requirements.txt`). Done: Vercel CLI cannot parse `-r` includes, so `requirements.txt` lists the core runtime deps directly, `requirements-dev.txt` adds test deps, and `tests/test_requirements.py` guards drift (erato-cloud PR #3).
- [x] C0.4 Create `vercel.json` (build `web`, function `api/index.py` with `includeFiles: "erato/app/**"`, rewrites like the core), `.github/workflows/ci.yml` (recursive submodule checkout, Mongo service, pytest, web vitest + build), `.env.example` (variable ownership table), `docs/runbook-preview.md` (Vercel project, env vars per scope, Deployment Protection off, pointer equals `erato` `preview` HEAD check, promotion order, rollback). Done with author adjustment: `vercel.json` and CI cover the API only; C5 adds the `web` build to `vercel.json` and the web vitest + build steps to CI. The core `orphan-sweep` cron is not yet in the cloud `vercel.json`; C1 adds it.
- [x] C0.5 Verification gate before other cloud units: deployed health route works, submodule clones over HTTPS, nested `-r erato/requirements.txt` resolves (design Risks). Record the result. Done 2026-10-08 on Preview (`2a126f4`): `/api/health` 200, `X-Robots-Tag: noindex`, submodule pointer equals `erato` `preview` HEAD; recorded in `erato-cloud` `docs/runbook-preview.md`. Production noindex omission is checked on the first Production deploy.
- [x] C0.6 `.venv/bin/pytest tests/` green; commit (Spanish), e.g. `feat(cloud): crea la base de erato-cloud con submodulo, entrada de API y CI`.

### Unit C1 (repo: erato-cloud) - subscriptions repository and indexes (~250 lines)
Specs: `plans-and-subscriptions: The subscriptions store MUST enforce one active subscription per subject`. D4, design Components table.
Depends on: C0.

- [ ] C1.1 RED: create `tests/test_subscriptions_repository.py`: insert shape (`subject {type,id}`, `plan`, `status`, `provider`, `provider_subscription_id`, `payer_id`, `extra_seats`, `cancel_at_period_end`, `current_period_end`, `canceled_at`, timestamps); `find_effective`; flag/cancel/revert conditional on written values; second active subscription for one subject -> `DuplicateKeyError` mapped to 409 `subscription_already_active`; a canceled or `cancel_at_period_end: true` one does not block a new insert; indexes `idx_subscriptions_subject` and `uq_subscriptions_subject_active` (partial filter `{status: "active", cancel_at_period_end: false}`) created; test the index set against the CI Mongo version (design risk: two indexes on equal key patterns). Run `.venv/bin/pytest tests/test_subscriptions_repository.py` -> failure.
- [ ] C1.2 GREEN: create `erato_cloud/subscriptions/__init__.py`, `erato_cloud/subscriptions/repository.py`, `scripts/ensure_cloud_indexes.py` (idempotent, `MONGODB_DB` aware).
- [ ] C1.3 Dry-run first: run `python -m scripts.ensure_cloud_indexes` against a scratch DB twice (idempotent); if Mongo rejects the two indexes, stop and ask the author (D4 owns the index set).
- [ ] C1.4 REFACTOR + `.venv/bin/pytest tests/`; commit (Spanish), e.g. `feat(cloud): agrega el repositorio de suscripciones con indice unico parcial`.

### Unit C2 (repo: erato-cloud) - SubscriptionPlanPolicy (~330 lines)
Specs: `plans-and-subscriptions: Three plans MUST exist with fixed entitlements`, `SubscriptionPlanPolicy MUST answer the core's questions from subscriptions`, `Members of an active band MUST have Pro features across their whole account`, `Unpaid bands MUST be read-only ...`, `Sharing with people and demo quotas MUST be gated by plan`. Design AD19; P10, P14, P16.
Depends on: C1; core B3 and B5a merged (pointer bump in this PR).

- [ ] C2.1 RED: create `tests/test_policy.py` (real Mongo): catalogue: Gratis demo limit 1, Pro 20, `can_create_band` always False, `can_share_with_people`/`can_view_history` = pro; `seat_limit` = 8 + max(`extra_seats`) over effective subscriptions (inactive band answers 8); `is_band_active` = effective list non-empty; EFFECTIVE definition incl. `cancel_at_period_end` with future `current_period_end`; OD-4: Gratis member of an active band is Pro for a composition outside the band, loses it on leave or when the band is inactive, keeps it via own Pro Individual or another active band; kill switch (`FREE_PRO_ENABLED` unset) ignores free subscriptions including band inheritance; memo: one resolution per request (query-count spy, at most three queries); per-request instance via `Depends` cache; no cross-request cache (leave takes effect next request); band-less user with no subscription is Gratis.
- [ ] C2.2 RED: extend `tests/test_wiring.py`: entitlements endpoint through the cloud app reports `band_creation_mode: "hand_off"`, `extensions_available: true`; direct `POST /api/bands` is 403 `plan_gate_band_creation` for everyone incl. owners of active bands and inherited-Pro members (OD-4 does not unlock creation); inactive band blocks band-derived writes through the core `require()`.
- [ ] C2.3 GREEN: create `erato_cloud/policy.py` (`SubscriptionPlanPolicy`, catalogue constants, `get_subscription_plan_policy`); finalize `erato_cloud/wiring.py` override; bump the `erato` submodule pointer to include B3/B5a.
- [ ] C2.4 REFACTOR + `.venv/bin/pytest tests/`; commit (Spanish), e.g. `feat(cloud): resuelve entitlements por suscripcion propia o banda activa`.

### Unit C3a (repo: erato-cloud) - billing port, free provider, individual endpoints (~280 lines)
Specs: `plans-and-subscriptions: The billing port MUST isolate providers from policy and UI`, `Free Pro MUST fail closed behind FREE_PRO_ENABLED`, `Subscription lifecycle endpoints MUST be mounted by the cloud app`; `preview-deployment: Free Pro MUST NOT be reachable in production`. Design AD11 (provider), AD13; P12, P13, P14, P15, OD-7, OD-8.
Depends on: C2.

- [ ] C3a.1 RED: create `tests/test_billing_free.py`: `FreeBillingProvider.checkout_band` returns confirmed only when `FREE_PRO_ENABLED` is true and `VERCEL_ENV != "production"`, else 403 `billing_unavailable`; unset flag means unavailable AND free subscriptions not honored (kill switch); `activate` creates `provider: "free"` with null `provider_subscription_id` and null `current_period_end`; `cancel` is immediate (`status: "canceled"`, `canceled_at`) and `set_extra_seats` supported; the gateway-style `cancel_at_period_end` path exists in the port contract (tested with a fake provider).
- [ ] C3a.2 RED: create `tests/test_plan_router.py`: `GET /api/plan` shape (`plan`, `source` own|band|none, `own_subscription`, `owned_bands`, `provider_available`; OD-7 inherited Pro shown with `source: "band"` and no cancel action; OD-8 may also activate Pro Individual); `POST /api/plan/individual` 201 / 409 `subscription_already_active` / 403 when flag off or production; `DELETE /api/plan/individual`; 401 anonymous.
- [ ] C3a.3 GREEN: create `erato_cloud/billing/__init__.py`, `erato_cloud/billing/port.py` (`BillingProvider`: `checkout_band`, `activate`, `cancel`, `set_extra_seats`), `erato_cloud/billing/free.py`, `erato_cloud/routers/__init__.py`, `erato_cloud/routers/plan.py` (individual endpoints + `GET /api/plan`); mount in `erato_cloud/wiring.py`.
- [ ] C3a.4 REFACTOR + `.venv/bin/pytest tests/`; commit (Spanish), e.g. `feat(cloud): agrega el proveedor gratuito con interruptor y los endpoints de plan individual`.

### Unit C3b (repo: erato-cloud) - band checkout, compensation, band lifecycle endpoints (~320 lines)
Specs: `plans-and-subscriptions: A band MUST be created only through a payment flow that calls the core`, `Subscription lifecycle endpoints`, `A plan page MUST allow activation, cancel and seats` (API part). Design AD11, AD18 (host calls), OD-9.
Depends on: C3a; core B5a merged (`BandsService.create_for_user`, `delete_band`).

- [ ] C3b.1 RED: create `tests/test_band_checkout.py`: `POST /api/plan/checkout/band {name}`: success returns 201 `{band, subscription}` with subject `{type: "band", id}`, `payer_id` = user, `extra_seats` 0; invalid name -> 422 BEFORE any payment step; flag off or production -> 403 `billing_unavailable` and nothing created; core creation failure -> re-raised, no subscription; activation failure -> core `delete_band` called, band gone, original error re-raised; compensation failure is logged with band id and original error still raised; multiple bands per owner each need their own checkout; old `POST /api/plan/bands {name}` is gone (404/405).
- [ ] C3b.2 RED: extend `tests/test_plan_router.py`: `POST /api/plan/bands/{id}` reactivates an inactive band (owner), `DELETE /api/plan/bands/{id}` cancels (payer of the effective subscription only), `PUT /api/plan/bands/{id}/seats {"extra_seats": 0..12}` owner only, 422 outside range, 409 `seats_below_members`; join seat limit changes accordingly through the core.
- [ ] C3b.3 GREEN: create `erato_cloud/checkout/__init__.py`, `erato_cloud/checkout/band.py` (`BandCheckout.run(user, name)`: steps 1-6 of AD11 using `app.services.bands_service.BandsService` and `app.schemas.bands.BandCreate` imported as `app.*`); extend `erato_cloud/routers/plan.py`; bump submodule pointer if needed.
- [ ] C3b.4 REFACTOR + `.venv/bin/pytest tests/`; commit (Spanish), e.g. `feat(cloud): crea bandas mediante checkout con compensacion si falla la activacion`.

### Unit C4 (repo: erato-cloud) - subscription step of ownership transfer (~220 lines)
Specs: `plans-and-subscriptions: Ownership transfer MUST move the band's subscription to the new owner as payer`. Design AD20, OD-9.
Depends on: C3b; core B6b merged (pointer bump).

- [ ] C4.1 RED: create `tests/test_transfer_step.py`: no effective subscription -> returns True and nothing created; provider unavailable -> raises `billing_unavailable` and nothing changed; free provider: previous superseded immediately (`status: "canceled"`) and the new one inserted with `payer_id` = B and copied `extra_seats`; gateway-style overlap (non-null `current_period_end`): previous flagged `cancel_at_period_end: true`, new inserted, seat limit = 8 + max extra over both so no join is wrongly refused; insert failure -> previous reverted (conditional on the values just written) and returns False so the core answers 409 `transfer_not_confirmed`; end-to-end through the core `POST .../transfer/accept` incl. payer-only cloud actions afterwards (B can cancel, A cannot).
- [ ] C4.2 GREEN: implement `confirm_band_transfer` in `erato_cloud/policy.py`; add flag/supersede/revert helpers in `erato_cloud/subscriptions/repository.py`; bump submodule pointer.
- [ ] C4.3 REFACTOR + `.venv/bin/pytest tests/`; commit (Spanish), e.g. `feat(cloud): mueve la suscripcion de la banda al nuevo propietario al transferir`.

### Unit C5 (repo: erato-cloud) - cloud web: plan page and band checkout (~320 lines)
Specs: `plans-and-subscriptions: A plan page MUST allow activation, cancel and seats`; `app-shell-and-navigation: extension point`; design AD12 cloud entry, AD17. All pages under `/plan`.
Depends on: C3b, FX merged in `erato` `preview` (pointer bump).

- [ ] C5.1 RED: create `web/tests/payments.spec.ts` (`cd web && npm run test:unit`): every registration passes the `/plan` prefix guard and has `meta.requiresAuth`; `bandCreationEntry` (`{ name: 'band-checkout' }`) resolves; `createEratoApp` mounted from the cloud shows the plan nav item for authenticated users only; `BandCheckoutView` handles 403 `billing_unavailable` and 422; `PlanView` shows Pro from a band with the band name as reason and no cancel (OD-7), optional Pro Individual (OD-8), activate/cancel, extra seats 0-12 with `seats_below_members` error; Spanish tuteo copy, no `!`/emoji; a test that only `/plan*` routes are registered.
- [ ] C5.2 GREEN: create `web/package.json` (`dev`, `build` = `vue-tsc && vite build`, `test:unit` = `vitest run`), `web/tsconfig.json`, `web/vite.config.ts` (aliases `@` -> `../erato/frontend/src`, `@design-system` -> `../erato/erato-design-system`, `resolve.dedupe: ['vue', 'vue-router']`, noindex `transformIndexHtml` plugin when `VERCEL_ENV !== 'production'`), `web/index.html`, `web/src/main.ts` (`createEratoApp({ payments: { routes: [planRoute, bandCheckoutRoute], navItems: [planNav], bandCreationEntry: { name: 'band-checkout' } } })`), `web/src/PlanView.vue`, `web/src/BandCheckoutView.vue`, `web/src/api/plan.ts`; refresh entitlements on return from `/plan*`.
- [ ] C5.3 REFACTOR + `cd web && npm run test:unit && npm run build`; update `vercel.json` build output if needed.
- [ ] C5.4 Commit (Spanish), e.g. `feat(cloud): agrega la pagina de plan y el checkout de banda`.

---

## Phase 6: Preview verification (manual, documented, no production changes)

- [ ] 6.1 Author runs the index bootstraps against `MONGODB_DB=erato_preview`: `python -m scripts.ensure_indexes` (erato) and `python -m scripts.ensure_cloud_indexes` (erato-cloud). Dry-run `python -m scripts.migrate_bands` first; apply only if the DB has legacy data.
- [ ] 6.2 Verify submodule pointer equals `erato` `preview` HEAD before testing; deployed landing and app share `noindex`, Deployment Protection off.
- [ ] 6.3 Walk the runbook checklist on the preview: anonymous public link + footer; checkout creates a band (hand-off from core "Crear banda"); invite until seat limit and concurrent join; share a composition with the band; read-only after cancel; transfer incl. expiry; unset `FREE_PRO_ENABLED` blocks activation and ignores free subscriptions.
- [ ] 6.4 Confirm root `vercel.json` and `tests/test_vercel_config.py` unchanged and the production project untouched.
- [ ] 6.5 Open follow-ups (not in this change): core CI workflow for `erato`, gateway work with G-1 (persist requested band name across checkout redirect), legal texts for landing placeholders.

## Dependency summary

- `erato` independent: PV1, L1 -> L2 -> L3, G1, X1 -> V1 -> {V2, V3} -> V4.
- `erato` bands chain: X1 -> B1 -> {B1M, B2} -> B3 (needs V2) -> B5a -> B5b -> {B6a, B7} -> B6b -> {FX (needs X1 only), F2 (B6b, FX), F3 (B7, FX, V4)} -> DOC.
- `erato-cloud`: C0 (needs X1) -> C1 -> C2 (needs B3, B5a) -> C3a -> C3b (needs B5a) -> {C4 (needs B6b), C5 (needs FX)}.
- Parallelizable: L-track, G1, PV1 and the versioning track run in parallel with each other and with the bands chain (one writer per track; no parallel writers on the same files, note V3/V4/F3 all edit `CompositionDetailView.vue`, so keep them sequential: V3 -> V4 -> F3).
- Sequential bottlenecks: X1 gates everything seam-related; B5a gates C3b; B6b gates C4; FX gates C5 and F2.
