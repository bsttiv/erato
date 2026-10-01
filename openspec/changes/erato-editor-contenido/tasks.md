# Tasks: Composition Content Editing and PDF-Faithful Screens

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~3,200–3,900 across 32 frontend/backend modules, stylesheets, and test suites |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 → PR 7 → PR 8 → PR 9 → PR 10 (see Suggested Work Units) |
| Delivery strategy | ask-on-risk |
| Chain strategy | **feature-branch-chain** (recommended per project conventions; requires author confirmation) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

**Feature-branch-chain layout**: PR 1 (Contract Reconciliation) opens against a tracker branch
`feature/erato-editor-contenido`. Each subsequent PR targets the immediately preceding PR's branch
in sequence (PR 2 → PR 1's branch, PR 3 → PR 2's branch, …, PR 10 → PR 9's branch). Only the tracker
branch merges into `main` after all units have passed review and verification.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | API Contract Reconciliation: fix frontend client drift (`compositions.ts`, `sharing.ts`, typed section endpoints) to match FastAPI contract | PR 1 | `npm run test:unit -- api/compositions api/sharing` | `npm run test:unit` | Revert modifies only `frontend/src/api/{compositions,sharing}.ts` and their tests; backend and downstream UI are untouched |
| 2 | Page-Shell Stylesheet & Modal Primitives: create `layout.css`, `AppModal.vue`, `useFocusTrap.ts`; purge inline styles; verify selector disjointness | PR 2 | `npm run test:unit -- layout-css app-modal` | `npm run dev` loading modal in isolated test harness | Revert removes `frontend/src/styles/layout.css`, `frontend/src/shared/`, and stylesheet tests; depends on PR 1 |
| 3 | Routing Infrastructure & Address Space: install `vue-router`, create route definitions, route guard with `authReady`, and `/c/:slug` resolver | PR 3 | `npm run test:unit -- guard` | `npm run dev` navigating `/`, `/login`, `/register`, `/c/:slug` | Revert removes `frontend/src/router/` and restores `App.vue` ref-based view switcher; depends on PR 2 |
| 4 | Auth Split-Screen Shell: 50/50 CSS-only hero layout; update `LoginForm.vue` and `RegisterForm.vue` with PDF copy; purge D11 deferred controls | PR 4 | `npm run test:unit -- auth-view` | `npm run dev` at `/login` and `/register` in Noche and Matiné themes | Revert restores previous `AuthView.vue` and auth form components; depends on PR 2, PR 3 |
| 5 | Composition Metadata & Computed Fields Backend: add 6 optional metadata fields, `SectionsEnabled`, computed `user_role`, list counts, and member projection | PR 5 | `.venv/bin/pytest tests/test_compositions_metadata.py tests/test_compositions_router.py` | `.venv/bin/pytest` against local test runner | Revert removes metadata fields from `app/schemas/compositions.py` and router projections; documents in Mongo remain backward-compatible |
| 6 | Dashboard & Full-Page Composition Creation: implement `DashboardView.vue`, `CompositionCard.vue`, `CompositionCreateView.vue` with 2 visibility options (D7); delete old views | PR 6 | `npm run test:unit -- dashboard composition-create` | `npm run dev` at `/` and `/compositions/new` | Revert restores `CompositionsView.vue` and `CompositionCreateModal.vue`; depends on PR 1, PR 2, PR 3, PR 5 |
| 7 | Composition Detail View & Chord Grid: persistent sidebar, PDF header, count-bearing section jump nav, responsive `ChordGrid.vue`, stacked panels | PR 7 | `npm run test:unit -- composition-detail chord-grid` | `npm run dev` at `/compositions/:id` | Revert restores previous `CompositionDetailView.vue`; depends on PR 1, PR 2, PR 3, PR 5, PR 6 |
| 8 | Sharing Modal, Member Projection & Viewer Role: implement `GET /members`, invite `viewer` role, and PDF-faithful `SharingModal.vue` with 2 visibility cards | PR 8 | `.venv/bin/pytest tests/test_sharing_roles.py tests/test_members_projection.py && npm run test:unit -- sharing-modal` | `npm run dev` opening Compartir modal on a composition | Revert removes members endpoint and restores previous `SharingModal.vue`; depends on PR 2, PR 5, PR 7 |
| 9 | Multi-Tab Tablature Model & Section: implement `TabEntry` model, whole-array `PUT`, pure tab helpers, and `TablatureSection.vue` with `:key` remount | PR 9 | `.venv/bin/pytest tests/test_tablature_tabs.py && npm run test:unit -- tab tablature-section` | `npm run dev` adding and switching tabs in tablature section | Revert restores single-tab schema and `ErTabEditor` direct usage; depends on PR 1, PR 2, PR 7 |
| 10 | Lyrics Chord Assignment Editor: pure bracket algebra (`setChordAt`), `ErChordPalette.vue`, `ErLyricsChordEditor.vue`, and `LyricsSection.vue` | PR 10 | `npm run test:unit -- lyrics lyrics-chord-editor lyrics-section` | `npm run dev` dragging chords onto syllables or using keyboard | Revert removes `ErLyricsChordEditor.vue`, `ErChordPalette.vue`, `LyricsSection.vue`, and bundle CSS additions; depends on PR 1, PR 2, PR 7 |

---

## Phase 1: API Contract Reconciliation (PR 1)

### Frontend client contract correction matching FastAPI endpoints

- [x] 1.1 RED: Create `frontend/tests/api/compositions.spec.ts` asserting:
  - `listCompositions()` returns `CompositionListItem[]` matching the flat backend response.
  - `getComposition(id)` returns `CompositionResponse` with typed `chords`, `tablature`, `lyrics`, `todos`, `demos`, and `user_role` fields (no generic `sections` envelope, `share_slug` instead of `slug`, `visibility` instead of `is_public`).
  - `getCompositionBySlug(slug)` calls `/compositions/by-slug/${slug}`.
  - `createComposition(payload)` sends `CreateCompositionPayload` (`title`, `visibility`, optional metadata).
  - Individual typed section update functions exist and call their dedicated endpoints:
    - `updateChordsSection(id, chords)` calls `PUT /api/compositions/{id}/chords`.
    - `updateTablatureSection(id, tablature)` calls `PUT /api/compositions/{id}/tablature`.
    - `updateLyricsSection(id, lyrics)` calls `PUT /api/compositions/{id}/lyrics`.
    - `updateTodosSection(id, todos)` calls `PUT /api/compositions/{id}/todos` with a bare array.
    - Generic `updateSection()` is removed or deprecated.
- [x] 1.2 GREEN: Rewrite `frontend/src/api/compositions.ts` to export:
  - Types: `Visibility`, `CompositionStatus`, `UserRole`, `TabColumn`, `TabEntry`, `TablatureSection`, `ChordsSection`, `LyricsSection`, `TodoItem`, `SectionsEnabled`, `CompositionCounts`, `CompositionListItem`, `CompositionResponse`, `CreateCompositionPayload`, `UpdateCompositionPayload`.
  - Functions: `listCompositions()`, `getComposition(id)`, `getCompositionBySlug(slug)`, `createComposition(payload)`, `updateComposition(id, payload)`, `updateChordsSection(id, payload)`, `updateTablatureSection(id, payload)`, `updateLyricsSection(id, payload)`, `updateTodosSection(id, payload)`.
- [x] 1.3 RED: Create `frontend/tests/api/sharing.spec.ts` asserting:
  - `setVisibility(id, visibility)` sends `PATCH /api/compositions/{id}/visibility` with `{ visibility }` (`"public"` | `"private"`), not `{ is_public }`.
  - `createInvite(id, payload)` sends `POST /api/compositions/{id}/invites` with `{ email, role }` where role is `"editor"` | `"viewer"`.
  - `listInvites(id)`, `revokeInvite(id, inviteId)`, and `redeemInvite(token)` match backend endpoints and response shapes.
  - `listMembers(id)` calls `GET /api/compositions/{id}/members` returning `MemberDetail[]`.
- [x] 1.4 GREEN: Update `frontend/src/api/sharing.ts` to implement corrected signatures and add `listMembers(id)`.
- [x] 1.5 REFACTOR: Update existing imports in `frontend/src/features/` to use the corrected `api/compositions.ts` and `api/sharing.ts` contracts without regressions. Run `npm run test:unit -- api` to verify.

---

## Phase 2: Page-Shell Stylesheet & Modal Primitives (PR 2)

### App-level layout stylesheet and accessible modal dialog

- [x] 2.1 RED: Create `frontend/tests/styles/layout-css.spec.ts` asserting:
  - Disjointness: Top-level selector set of `frontend/src/styles/layout.css` does not intersect with `erato-design-system/components/bundle.css`.
  - Token purity: No literal hex colors, named colors, literal font stacks, or literal pixel/rem border radii (all use `var(--token)`).
  - Completeness: Every `er-*` class referenced in `layout.css` or existing feature components resolves to either `layout.css` or `bundle.css`.
  - Inline style hygiene: No inline `style="…"` attribute exists in files under `frontend/src/features/`.
- [x] 2.2 GREEN: Create `frontend/src/styles/layout.css` defining token-driven layout classes:
  - App shell: `er-app`, `er-app-main`.
  - Dashboard: `er-topbar`, `er-topbar-brand`, `er-avatar`, `er-dash`, `er-dash-hero`, `er-dash-headline`, `er-filterbar`, `er-dash-count`, `er-comp-grid`, `er-card`, `er-card-head`, `er-card-index`, `er-card-title`, `er-card-chords`, `er-card-counts`, `er-card-foot`, `er-card-new`.
  - Composition shell & page: `er-layout`, `er-layout--noside`, `er-sidebar`, `er-sidebar-foot`, `er-main`, `er-comp-detail`, `er-crumb`, `er-savestate`, `er-comp-header`, `er-comp-title`, `er-comp-meta`, `er-comp-tags`, `er-avatars`, `er-sectionnav`, `er-section`, `er-section-head`, `er-comp-columns`, `er-comp-column`, `er-role-tag`, `er-save-btn`.
  - Create page: `er-createshell`, `er-createbar`, `er-form-card`, `er-field`, `er-field-row`, `er-field-grid`, `er-hint`, `er-usecards`, `er-usecard`, `er-checkbox-label`.
  - Auth: `er-auth-split`, `er-auth-hero`, `er-auth-bars`, `er-auth-bar`, `er-auth-pill`, `er-auth-rules`, `er-auth-wordmark`, `er-auth-tagline`, `er-auth-pane`, `er-auth-view`, `er-auth-header`, `er-auth-form`, `er-auth-error`, `er-auth-links`.
  - Modal overlay: `er-modal-backdrop`, `er-modal`, `er-modal-head`, `er-modal-body`, `er-modal-foot` with `z-index: 60`.
  - Sharing: `er-share-cards`, `er-share-card`, `er-share-link`, `er-perm-list`, `er-invite-row`, `er-invites-block`, `er-invite-created`, `er-invites-list`, `er-member`, `er-member-id`, `er-member-role`.
  - Editors & utilities: `er-tabs-strip`, `er-tab-actions`, `er-chord-grid`, `er-chord-palette`, `er-chord-chip`, `er-lyrics-edit`, `er-lyrics-line`, `er-loading`, `er-empty`, `er-demos-section`.
- [x] 2.3 GREEN: Import `frontend/src/styles/layout.css` in `frontend/src/main.ts` immediately after `bundle.css`.
- [x] 2.4 RED: Create `frontend/tests/shared/app-modal.spec.ts` asserting:
  - Renders overlay with backdrop above page content (`z-index: 60`).
  - Emits `close` when backdrop is clicked.
  - Does NOT emit `close` when modal content itself is clicked.
  - Emits `close` when `Escape` key is pressed.
  - Traps keyboard focus within modal elements while open.
  - Restores keyboard focus to previous trigger element on close.
- [x] 2.5 GREEN: Create `frontend/src/shared/useFocusTrap.ts` implementing focus trap and restoration logic.
- [x] 2.6 GREEN: Create `frontend/src/shared/AppModal.vue` using `useFocusTrap` and `layout.css` modal classes.
- [x] 2.7 REFACTOR: Purge existing inline `style="…"` attributes from `frontend/src/features/demos/DemosSection.vue` and `frontend/src/features/demos/DemoUploadModal.vue`, replacing them with `layout.css` classes. Verify `npm run test:unit -- layout-css app-modal` passes.

---

## Phase 3: Routing & Address Space (PR 3)

### Client-side routing with deep link resolution and navigation guards

- [x] 3.1 RED: Create `frontend/tests/router/guard.spec.ts` asserting:
  - Navigation to protected routes (`/`, `/compositions/new`, `/compositions/:id`) when unauthenticated redirects to `/login`.
  - Public route `/c/:slug` and `/c/:id` is accessible without authentication.
  - `/invite/:token` is accessible without authentication (redirects to redemption flow).
  - Navigation guard waits on `authReady` promise before redirecting so initial refresh does not flash login.
  - `/c/:ref` resolves 24-character hex ID directly and falls back to by-slug on 404; non-hex ref queries by-slug directly.
- [x] 3.2 GREEN: Add `vue-router` to `frontend/package.json` and install runtime dependency.
- [x] 3.3 GREEN: Update `frontend/src/features/auth/useAuth.ts` to expose an `authReady: Promise<void>` resolving once initial token refresh check settles.
- [x] 3.4 GREEN: Create `frontend/src/router/routes.ts` defining route records:
  - `/` -> Dashboard
  - `/login` -> Auth (login mode)
  - `/register` -> Auth (register mode)
  - `/compositions/new` -> Composition creation full page
  - `/compositions/:id` -> Composition detail page
  - `/c/:slug` -> Public composition view
  - `/invite/:token` -> Invitation redemption
- [x] 3.5 GREEN: Create `frontend/src/router/index.ts` instantiating `createRouter` with `createWebHistory()`, registering the navigation guard with `authReady` check and anonymous route exemptions.
- [x] 3.6 GREEN: Update `frontend/src/main.ts` to register router with `app.use(router)`.
- [x] 3.7 GREEN: Refactor `frontend/src/App.vue` from ref-based view switching to render `<router-view />` inside the top-level application shell.
- [x] 3.8 REFACTOR: Run `npm run test:unit -- guard` and verify all routing and guard scenarios pass.

---

## Phase 4: Auth Split-Screen Shell (PR 4)

### Split-screen auth layout with pure-CSS hero and cleaned forms

- [ ] 4.1 RED: Create `frontend/tests/features/auth-view.spec.ts` asserting:
  - Split-screen layout renders 50/50 hero panel and form panel.
  - Hero panel renders brand wordmark, tagline, and pure CSS geometric bars/glow without issuing any network `<img>` or background image request.
  - Form panel switches between `LoginForm.vue` and `RegisterForm.vue` based on current route (`/login` vs `/register`).
  - `LoginForm.vue` contains: title "Inicia sesión", subtitle "Bienvenido de vuelta a tu espacio de composición.", email input, password input with "mostrar" toggle, primary button "Entrar", and link to register.
  - `LoginForm.vue` does NOT render Google button or password-reset link (D11).
  - `RegisterForm.vue` contains: title "Crea tu cuenta", subtitle "Organiza las canciones de tu banda en un solo lugar.", name input, email input, password input, primary button "Crear cuenta", and link to login.
  - `RegisterForm.vue` does NOT render Banda field, Google button, or terms/privacy links (D11).
- [ ] 4.2 GREEN: Restructure `frontend/src/features/auth/AuthView.vue` with 50/50 split-screen container, CSS-only jazz hero (`er-auth-bars`, `er-auth-bar`, `er-auth-pill`, `er-auth-rules`, `radial-gradient` glow), and `<router-view>` or route-bound form container.
- [ ] 4.3 GREEN: Update `frontend/src/features/auth/LoginForm.vue`:
  - Align copy with PDF page 1 ("Inicia sesión", "Bienvenido de vuelta...", "Entrar").
  - Add password visibility toggle button ("mostrar" / "ocultar").
  - Replace mode switch with `<router-link to="/register">¿No tienes cuenta? Regístrate</router-link>`.
  - Remove any disabled or placeholder Google button or reset password controls.
- [ ] 4.4 GREEN: Update `frontend/src/features/auth/RegisterForm.vue`:
  - Align copy with PDF page 1 ("Crea tu cuenta", "Organiza las canciones...", "Crear cuenta").
  - Replace mode switch with `<router-link to="/login">¿Ya tienes cuenta? Inicia sesión</router-link>`.
  - Ensure no Banda input, Google button, or legal terms placeholders exist.
- [ ] 4.5 REFACTOR: Verify `frontend/tests/features/auth-view.spec.ts` and `frontend/tests/features/auth.spec.ts` pass cleanly under `npm run test:unit -- auth`.

---

## Phase 5: Composition Metadata & Computed Fields Backend (PR 5)

### Metadata schemas, advisory role, and list counts in FastAPI

- [ ] 5.1 RED: Create `tests/test_compositions_metadata.py` asserting:
  - Creating a composition accepts optional `key`, `bpm`, `time_signature`, `style_tags`, `status`, and `sections_enabled`.
  - Default creation without metadata sets `status: "idea"`, `sections_enabled` defaults, and nullable fields to `None`.
  - Status accepts only `"idea"`, `"in_progress"`, `"ready"`; any other value raises 422.
  - Updating a composition via `PATCH /api/compositions/{id}` updates metadata fields.
  - Pre-existing compositions without metadata fields serialize cleanly with defaults on read.
- [ ] 5.2 GREEN: Update `app/schemas/compositions.py`:
  - Define `STATUS = Literal["idea", "in_progress", "ready"]`.
  - Define `SectionsEnabled` model (`chords: bool = True`, `tablature: bool = False`, `lyrics: bool = True`, `demos: bool = True`, `todos: bool = True`).
  - Add optional `key`, `bpm`, `time_signature`, `style_tags`, `status`, and `sections_enabled` to `CreateCompositionRequest`, `UpdateCompositionRequest`, `CompositionListItem`, and `CompositionResponse`.
  - Add `CompositionCounts` schema (`chords: int`, `tabs: int`, `demos: int`, `todos_done: int`, `todos_total: int`) and `chord_names: List[str]` to `CompositionListItem`.
- [ ] 5.3 RED: Create `tests/test_user_role_response.py` asserting:
  - `GET /api/compositions/{id}` returns `user_role: "owner"` for the owner.
  - `GET /api/compositions/{id}` returns `user_role: "editor"` for an invited editor member.
  - `GET /api/compositions/{id}` returns `user_role: "viewer"` for an invited viewer member.
  - `GET /api/compositions/by-slug/{slug}` returns `user_role: None` for unauthenticated requests, and correct role if optional auth header is present.
  - `GET /api/compositions` list returns computed `counts` and first 4 `chord_names` from document data without extra queries.
- [ ] 5.4 GREEN: Update `app/routers/compositions.py`:
  - Update `_to_response(doc, role=None)` to accept advisory `role` and populate `user_role`.
  - Update `get_composition` and `update_composition` to pass `auth.role`.
  - Update `create_composition` to pass `Role.OWNER`.
  - Update `get_by_slug` to resolve optional caller identity via `resolve_role()` and populate `user_role`.
  - Update `list_compositions` to compute `counts` and `chord_names` in memory from loaded documents.
- [ ] 5.5 GREEN: Update `app/db/repositories/compositions.py` to allow patching metadata fields in `update_fields` allow-list.
- [ ] 5.6 REFACTOR: Run `.venv/bin/pytest tests/test_compositions_metadata.py tests/test_user_role_response.py tests/test_compositions_router.py` to verify backend behavior.

---

## Phase 6: Dashboard & Full-Page Composition Creation (PR 6)

### Dashboard view with card grid and full-page composition creation shell

- [ ] 6.1 RED: Create `frontend/tests/features/dashboard-view.spec.ts` asserting:
  - Top app bar displays brand, "Nueva canción" button linking to `/compositions/new`, and user avatar initials.
  - Headline renders "Composiciones" display-serif title and subtitle.
  - Filter bar renders `ErSegmented` with options: "Todas", "En progreso", "Listas", "Ideas", updating view filter.
  - Result count displays e.g. "8 canciones" updating dynamically with filter.
  - Card grid renders a `CompositionCard` per item plus the dashed "Empieza una canción nueva" card.
  - `CompositionCard.vue` renders: 2-digit index (`01`, `02`), status `ErTag` (`En progreso`, `Lista`, `Idea`), title, chord names row (up to 4 chords), counts badge row ("acordes X · tab X · demos X · tareas X/Y"), and footer with `updated_at` relative time ("editada hace ...").
  - Omits missing metadata chips (e.g. no bpm chip if bpm is unset).
  - Clicking card navigates to `/compositions/:id`.
- [ ] 6.2 GREEN: Create `frontend/src/features/compositions/CompositionCard.vue` implementing card structure using `layout.css` classes and tokens.
- [ ] 6.3 GREEN: Create `frontend/src/features/compositions/DashboardView.vue` implementing top bar, hero headline, `ErSegmented` filter, card grid, and navigation to creation flow.
- [ ] 6.4 RED: Create `frontend/tests/features/composition-create-view.spec.ts` asserting:
  - Renders full-page creation shell (minimal bar with brand + "Cancelar" link, centered form card; NOT a modal).
  - Form fields: Title input ("Título de la canción"), 3-column metadata row (Tonalidad, Tempo/BPM, Compás).
  - Visibility control presents exactly TWO options (D7): "Con enlace" (public) and "Privada" (private); no band option.
  - Five section include cards (chords, tablature, lyrics, demos, tasks) render as toggleable `<button aria-pressed>` elements with default states (tablature unselected, others selected).
  - Submitting form calls `createComposition()` with title, visibility, metadata, and `sections_enabled`, then navigates to `/compositions/:id`.
  - Canceling navigates back to dashboard `/`.
- [ ] 6.5 GREEN: Create `frontend/src/features/compositions/CompositionCreateView.vue` matching PDF page 2 specifications.
- [ ] 6.6 GREEN: Delete superseded files `frontend/src/features/compositions/CompositionsView.vue` and `frontend/src/features/compositions/CompositionCreateModal.vue`.
- [ ] 6.7 REFACTOR: Update routes in `frontend/src/router/routes.ts` to map `/` to `DashboardView.vue` and `/compositions/new` to `CompositionCreateView.vue`. Run `npm run test:unit -- dashboard composition-create` to verify.

---

## Phase 7: Composition Detail View & Chord Grid (PR 7)

### Detail page shell, persistent sidebar, jump nav, and chord editor grid

- [ ] 7.1 RED: Create `frontend/tests/features/chord-grid.spec.ts` asserting:
  - Renders a responsive grid of `ErChordEditor` components from `chords.entries[]`.
  - Supports adding a new chord diagram and removing an existing chord diagram.
  - Emits updated `ChordsSection` payload when any chord changes.
  - Instrument toggle changes diagram between guitar and piano.
- [ ] 7.2 GREEN: Create `frontend/src/features/compositions/ChordGrid.vue` composing `ErChordEditor` instances with add/remove buttons.
- [ ] 7.3 RED: Create `frontend/tests/features/composition-detail-view.spec.ts` asserting:
  - Persistent sidebar (`ErSideNav`) with link back to dashboard `← todas las composiciones` in `er-sidebar-foot`.
  - Unauthenticated visitor on public share route drops sidebar (`er-layout--noside`).
  - Header displays breadcrumb, display-serif title, save status indicator, metadata chips (tonalidad, tempo, compás, style tags), avatar stack, and actions: "Compartir" button, "Guardar" button.
  - Save button and edit controls render only for `owner` and `editor`, never for `viewer` or unauthenticated public visitors.
  - Jump nav strip renders all enabled sections with live counts ("acordes X", "tablatura Y", "demos Z", "tareas A/B").
  - Jump nav activation scrolls to section without hiding other sections (all panels stacked in document simultaneously).
  - Sections rendered: chords panel (`ChordGrid.vue`), tablature panel (`TablatureSection.vue`), lyrics panel (`LyricsSection.vue`), demos panel (`DemosSection.vue`), todos panel (`ErTodoList.vue`).
- [ ] 7.4 GREEN: Restructure `frontend/src/features/compositions/CompositionDetailView.vue` to implement sidebar, PDF header, count-bearing section jump navigation, and stacked section containers.
- [ ] 7.5 REFACTOR: Update `frontend/src/features/demos/DemosSection.vue` to integrate cleanly into the stacked layout without inline styles. Run `npm run test:unit -- composition-detail chord-grid` to verify.

---

## Phase 8: Sharing Modal, Member Projection & Viewer Role (PR 8)

### Member projection endpoint, viewer-only invite role, and sharing dialog

- [ ] 8.1 RED: Create `tests/test_sharing_roles.py` asserting:
  - `POST /api/compositions/{id}/invites` accepts `role: "viewer"` in addition to `"editor"`; invalid roles reject with 422.
  - Redeeming a viewer-role invitation assigns role `"viewer"` in composition `members[]`.
  - User with `"viewer"` role can `GET` public or private composition.
  - User with `"viewer"` role is rejected with 403 on all write endpoints (`PATCH /api/compositions/{id}`, `PUT /chords`, `PUT /tablature`, `PUT /lyrics`, `PUT /todos`).
  - Authenticated non-invited user cannot edit public composition (returns 403).
- [ ] 8.2 GREEN: Update `app/schemas/compositions.py` `CreateInviteRequest`:
  - Validate `role: str = Field("editor", pattern="^(editor|viewer)$")`.
- [ ] 8.3 RED: Create `tests/test_members_projection.py` asserting:
  - `GET /api/compositions/{id}/members` returns `List[MemberDetail]`:
    - Active members include `user_id`, `display_name`, `email`, `initials`, `role`, and `pending: false`.
    - Pending invitations include `invite_id`, `email`, `role`, and `pending: true`.
  - Requires `MANAGE_SHARING` permission (owner only); rejected with 403 for editor/viewer.
  - `CompositionResponse` returned from `GET /compositions/{id}` and public by-slug route includes `MemberItem[]` with `display_name` and `initials`, but never `email` (D8).
- [ ] 8.4 GREEN: Implement `GET /api/compositions/{id}/members` in `app/routers/compositions.py` resolving user display names, emails, and initials via batched repository lookup.
- [ ] 8.5 RED: Create `frontend/tests/features/sharing-modal.spec.ts` asserting:
  - Wrapped inside `AppModal.vue` with centered backdrop and escape dismissal.
  - Visibility control presents exactly two options (D7): "Con enlace" (public) and "Privada" (private).
  - Toggling visibility calls `setVisibility(id, visibility)`.
  - Displays read-only share link with working "Copiar enlace" button.
  - Displays permission checklist explaining access rules.
  - Invite row provides email input, role dropdown ("Editor" vs "Solo ver"), and "Invitar" button calling `createInvite()`.
  - Member list displays owner, active members, and pending invitations with avatar initials, display name, email, and role badge.
- [ ] 8.6 GREEN: Restructure `frontend/src/features/sharing/SharingModal.vue` matching PDF page 5 design.
- [ ] 8.7 REFACTOR: Run `.venv/bin/pytest tests/test_sharing_roles.py tests/test_members_projection.py` and `npm run test:unit -- sharing-modal` to verify sharing behavior.

---

## Phase 9: Multi-Tab Tablature Model & Section (PR 9)

### Multi-tab data model and tabbed tablature container

- [ ] 9.1 RED: Create `frontend/tests/design-system/tab.spec.ts` updates asserting:
  - `newTabId()` generates unique client-side identifiers.
  - `newTabEntry(title, strings)` returns a new `TabEntry` with blank columns and default 6 strings.
  - TabEntry conforms to `{ id, title, strings, columns }`.
- [ ] 9.2 GREEN: Update `frontend/src/design-system/core/tab.ts` to export `TabEntry`, `newTabId`, and `newTabEntry` while keeping existing `tabToText`, `blankTab`, and `TECH` untouched.
- [ ] 9.3 RED: Create `tests/test_tablature_tabs.py` asserting:
  - `PUT /api/compositions/{id}/tablature` accepts `{ tabs: List[TabEntry] }`.
  - Validates `title` (1–80 chars), `strings` (default 6), and `columns` (list of strings or `"|"`).
  - Persists full tabs array in order without storing derived ASCII text.
  - Empty tabs array `{ tabs: [] }` is valid.
- [ ] 9.4 GREEN: Ensure `app/schemas/compositions.py` `TablatureSection` model and `app/routers/sections.py` validate and persist `tabs` array.
- [ ] 9.5 RED: Create `frontend/tests/features/tablature-section.spec.ts` asserting:
  - Tab strip renders all tabs from `tablature.tabs` plus a "+" button to add a tab.
  - Active tab is highlighted with `aria-selected="true"`.
  - Clicking a tab switches the active tab and remounts `ErTabEditor` via `:key="activeTab.id"` with the switched tab's columns.
  - User can rename the active tab inline.
  - User can delete a tab (with confirmation or prevent deleting last tab if required).
  - Editing columns in `ErTabEditor` emits updated `tabs` array to parent.
  - Read-only mode renders `ErTabEditor` with `readonly` attribute and hides tab manipulation actions.
- [ ] 9.6 GREEN: Create `frontend/src/features/compositions/TablatureSection.vue` wrapping `ErTabEditor` with the horizontal tab strip and `:key` remount.
- [ ] 9.7 REFACTOR: Run `.venv/bin/pytest tests/test_tablature_tabs.py` and `npm run test:unit -- tab tablature-section` to verify multi-tab tablature.

---

## Phase 10: Lyrics Chord Assignment Editor (PR 10)

### Pure bracket-markup algebra, chord palette, and drag/keyboard editor

- [ ] 10.1 RED: Create `frontend/tests/design-system/lyrics.spec.ts` updates asserting:
  - `decomposeLine(line)` breaks a lyrics line into syllable tokens with their current chord annotation.
  - `composeLine(tokens)` reconstructs the bracket-markup string from tokens.
  - `setChordAt(content, target, chord)`:
    - Placing a chord on an unmarked syllable inserts `[Chord]` before the syllable text.
    - Placing a chord on an already marked syllable replaces the chord.
    - Removing a chord (sentinel chip `null` or empty string) deletes the bracket marker without modifying lyric text.
  - Round-trip fidelity: `parseLine(composeLine(decomposeLine(text)))` produces identical segments to `parseLine(text)`.
  - Unmodified read path: `parseLine()` remains untouched.
- [ ] 10.2 GREEN: Implement `decomposeLine`, `composeLine`, and `setChordAt` in `frontend/src/design-system/core/lyrics.ts`.
- [ ] 10.3 GREEN: Add drag and drop utility classes to `erato-design-system/components/bundle.css` (D4):
  - `.er-drag-ghost` (semi-transparent floating chip during pointer drag).
  - `.er-drop-target` with states `.is-armed` and `.is-over`.
- [ ] 10.4 RED: Create `frontend/tests/features/lyrics-chord-editor.spec.ts` asserting:
  - Chord palette renders an `ErButton` chip for each chord in `chords.entries[]`, plus the sentinel chip `✕ quitar`.
  - Keyboard path: Focus palette button, press `Enter`/`Space` to arm; focus syllable `<button>` target, press `Enter`/`Space` to commit chord.
  - Escape key disarms the currently armed chord.
  - Drag path: Synthesised `PointerEvent` (`pointerdown`, `pointermove`, `pointerup` on drop target) inserts chord.
  - Parity: Dragging chord `C` to syllable at offset X produces byte-identical `lyrics.content` as arming `C` and pressing `Enter` on target at offset X.
  - Sentinel chip `✕ quitar` removes chord marker from target syllable via both keyboard and drag paths.
  - All interactive elements are real `<button>` elements with visible focus rings.
- [ ] 10.5 GREEN: Create `frontend/src/design-system/components/ErChordPalette.vue` rendering chord buttons and sentinel chip with `touch-action: none`.
- [ ] 10.6 GREEN: Create `frontend/src/design-system/components/ErLyricsChordEditor.vue` implementing the syllable drop targets, keyboard arm/commit, and pointer event drag handling.
- [ ] 10.7 GREEN: Export `ErChordPalette` and `ErLyricsChordEditor` from `frontend/src/design-system/components/index.ts`.
- [ ] 10.8 RED: Create `frontend/tests/features/lyrics-section.spec.ts` asserting:
  - In read mode, renders `ErLyricsViewer.vue` with auto-scroll and full-screen controls.
  - In edit mode, renders `ErLyricsChordEditor.vue` with chord palette.
  - "Editar acordes" toggle switches between read and edit modes for authorized editors.
  - Read-only visitors never see the edit toggle.
- [ ] 10.9 GREEN: Create `frontend/src/features/compositions/LyricsSection.vue` toggling between viewer and chord editor.
- [ ] 10.10 REFACTOR: Run `npm run test:unit -- lyrics lyrics-chord-editor lyrics-section` to verify all lyrics features.

---

## Phase 11: End-to-End Verification & Quality Gate (Verification on Tracker Branch)

### Comprehensive test passes, styling audits, and visual checklist

- [ ] 11.1 Run the full frontend unit and component test suite:
  ```bash
  npm run test:unit
  ```
  Assert 100% pass across all design-system and feature suites.
- [ ] 11.2 Run frontend typecheck and production build:
  ```bash
  npm run build
  ```
  Assert zero TypeScript errors and successful Vite build output.
- [ ] 11.3 Run full backend test suite:
  ```bash
  .venv/bin/pytest
  ```
  Assert zero regressions across auth, compositions, permissions, sharing, sections, and demos.
- [ ] 11.4 Run stylesheet integrity assertions:
  - Verify layout CSS disjointness test passes (`frontend/tests/styles/layout-css.spec.ts`).
  - Scan codebase to confirm zero inline `style="…"` attributes remain under `frontend/src/features/`.
  - Confirm every referenced `er-*` class resolves to a rule in `bundle.css` or `layout.css`.
- [ ] 11.5 Manual accessibility and theme audit:
  - Verify both Noche (dark) and Matiné (light) themes render with WCAG AA 4.5:1 text contrast on Dashboard, Composition Detail, Creation, and Auth pages.
  - Verify keyboard navigation: focus rings visible, all modal dialogs trap and restore focus, and lyrics editor can be operated entirely without a mouse.
  - Confirm auth hero renders cleanly in both themes without issuing any image network requests.
