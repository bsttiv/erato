# Tasks: UI Adjustments and Phone-Friendly Layout

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1100 across 5 work units (frontend only, tests included) |
| 400-line budget risk | Low per unit (largest ~300), Medium in total |
| Chained PRs recommended | Yes |
| Suggested split | WU1 -> WU2 -> WU3 -> WU4 -> WU5 |
| Delivery strategy | ask-on-risk |
| Chain strategy | **feature-branch-chain** (approved) |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low

**Layout**: tracker branch `feature/erato-ajustes-ui`. WU1 PR targets the tracker; each later PR targets
the previous WU branch. Branches: `feature/erato-ajustes-ui-01-quick-fixes`, `-02-brand-status`,
`-03-responsive-foundation`, `-04-horizontal-fretboard`, `-05-chord-carousel`. Only the tracker merges into `main`.

### Suggested Work Units

| Unit | Goal | Est. lines | Focused test command | Rollback boundary |
|------|------|-----------|----------------------|-------------------|
| 1 | Quick fixes: field grid, single Cancelar, sidebar link first, `formatDate` | ~150 | `npm run test:unit -- format composition-create ErDemoPlayer layout-css composition-detail` | Plain revert of PR |
| 2 | `ErBrand` everywhere + status editing | ~200 | `npm run test:unit -- ErBrand ErSideNav auth-view invite-accept dashboard composition-create composition-detail` | Plain revert; data untouched |
| 3 | 768px foundation + drawer sidebar | ~300 | `npm run test:unit -- use-drawer composition-detail dashboard layout-css` | Plain revert |
| 4 | Horizontal guitar fretboard (D6) | ~200 | `npm run test:unit -- ErChordEditor chord-grid` | Plain revert restores vertical SVG |
| 5 | Chord carousel + small-screen polish | ~250 | `npm run test:unit -- chord-grid layout-css` | Plain revert; depends on WU3 and WU4 |

Conventions: run from `/home/bspc/proyectos/erato/frontend`. Runner: `npm run test:unit -- <pattern>`.
End of every unit: `npx vue-tsc --noEmit` and `npm run build`. Backend untouched; run
`.venv/bin/pytest -q` once at the end (expect 81 passed). Commits: Spanish Conventional Commit,
explicit paths, no AI attribution. UI text Spanish (tuteo, no exclamation marks, no emoji).

---

## WU1: Quick fixes (branch `feature/erato-ajustes-ui-01-quick-fixes`)

Specs: design-system-port (no overflow), app-shell-and-navigation (one Cancelar, sidebar link/crumb), composition-content (dates).

### RED
- [x] 1.1 Create `frontend/tests/design-system/format.spec.ts`: valid ISO yields day/year and 3-letter month prefix (regex); `null`/`undefined`/`''` return `''`; `'not-a-date'` returns raw string, never "Invalid".
- [x] 1.2 `composition-create-view.spec.ts`: update any assertion of the top Cancelar; assert exactly one button with text "Cancelar".
- [x] 1.3 `ErDemoPlayer.spec.ts`: update raw-ISO date expectations; assert take date has no `T`/`Z` and matches the formatted pattern.
- [x] 1.4 `composition-detail-view.spec.ts`: first child of the sidebar is the "todas las composiciones" link (before `ErSideNav`); crumb link `href="/"`; demo dates formatted.
- [x] 1.5 `frontend/tests/styles/layout-css.spec.ts`: `.er-field-grid` uses `minmax(0, 1fr)`; its input/select have `width: 100%` and `min-width: 0`; `.er-crumb a` has hover/underline rule with no hex/rgb.
- [x] 1.6 Run `npm run test:unit -- format composition-create ErDemoPlayer layout-css composition-detail`; confirm new assertions FAIL.

### GREEN
- [x] 2.1 `frontend/src/design-system/core/format.ts` + `core/index.ts`: add and export `formatDate` (module-level `Intl.DateTimeFormat('es', {day:'numeric', month:'short', year:'numeric'})`, invalid-date guard).
- [x] 2.2 `design-system/components/ErDemoPlayer.vue` (lines ~23, 53): render dates via `formatDate`.
- [x] 2.3 `features/compositions/CompositionCreateView.vue`: delete top Cancelar block (lines 7-9), keep the bottom one.
- [x] 2.4 `features/compositions/CompositionDetailView.vue`: move foot link (lines 16-20) above `ErSideNav`; use `formatDate` for demo dates.
- [x] 2.5 `frontend/src/styles/layout.css`: `.er-field-grid` to `repeat(3, minmax(0, 1fr))` with input/select `width:100%; min-width:0`; style `.er-crumb a` (hover, underline) with existing tokens only.

### REFACTOR / verify
- [x] 3.1 `npm run test:unit -- format composition-create ErDemoPlayer layout-css composition-detail` all green; then full `npm run test:unit`.
- [x] 3.2 `npx vue-tsc --noEmit` and `npm run build` clean.
- [ ] 3.3 Manual QA (author only): 360/390/768/1024px in Noche and Matine; compas input inside card, single Cancelar, link first, crumb contrast 4.5:1, dates like "1 oct 2026".
- [x] 3.4 Work-unit commit: `fix(ui): corrige desbordes, Cancelar duplicado, enlace lateral y fechas de demos` with explicit paths.

---

## WU2: Brand and status (branch `feature/erato-ajustes-ui-02-brand-status`)

Specs: design-system-port (ErBrand), composition-content (status editing).

### RED
- [x] 1.1 New `frontend/tests/design-system/ErBrand.spec.ts`: renders `.er-brand` with `.er-nav-lamp` (aria-hidden) and `.er-nav-name`; default label "Erato"; custom `label` honored.
- [x] 1.2 Per view specs (`ErSideNav`, `auth-view`, `invite-accept-view`, `dashboard-view`, `composition-create-view`): `.er-brand` exists; no plain-text `.er-auth-wordmark` left; auth keeps a single h1.
- [x] 1.3 New `tests/compositions/status.spec.ts`: `STATUS_OPTIONS` has idea/in_progress/ready; `statusLabel` maps to Idea / En progreso / Lista.
- [x] 1.4 `composition-create-view.spec.ts`: status default `idea`; selecting "Lista" posts `status:'ready'`.
- [x] 1.5 `composition-detail-view.spec.ts`: editor clicking "En progreso" calls mocked `updateComposition(id, {status:'in_progress'})`; control disabled while in flight; rejection reverts value and shows "No se pudo guardar el estado. Intenta de nuevo."; non-editor sees `ErTag` and no segmented control.
- [x] 1.6 `dashboard-view.spec.ts` / card spec: card tag uses `statusLabel`; groups follow stored status.
- [x] 1.7 `layout-css.spec.ts`: `.er-brand` rule exists, token-only; `.er-topbar-brand` has no text styling.
- [x] 1.8 Run focused command; confirm FAIL.

### GREEN
- [x] 2.1 Create `design-system/components/ErBrand.vue`; export in `components/index.ts` and `design-system/index.ts`.
- [x] 2.2 Swap in `ErSideNav.vue` (`<ErBrand :label="brand"/>`), `DashboardView.vue`, `CompositionCreateView.vue`, `InviteAcceptView.vue`, `AuthView.vue` (inside the existing h1).
- [x] 2.3 Create `features/compositions/status.ts` (`STATUS_OPTIONS`, `statusLabel`).
- [x] 2.4 `CompositionCreateView.vue`: status `ErSegmented`, default `idea`, included in payload.
- [x] 2.5 `CompositionDetailView.vue`: editor `ErSegmented` with optimistic update, disabled in flight, revert + `er-savestate` error on failure; non-editors get `ErTag`.
- [x] 2.6 `CompositionCard.vue`, `DashboardView.vue`: reuse `statusLabel`.
- [x] 2.7 `layout.css`: add `.er-brand`; trim `.er-topbar-brand` and `.er-auth-wordmark` to link/alignment only.

### REFACTOR / verify
- [x] 3.1 Focused command green, then full `npm run test:unit` (ErSideNav is shared).
- [x] 3.2 `npx vue-tsc --noEmit` and `npm run build` clean.
- [ ] 3.3 Manual QA (author only): 360/390/768/1024px, both themes; same logo on all five places; status persists after reload; offline failure reverts; viewer sees tag.
- [x] 3.4 Work-unit commit: `feat(ui): unifica el logo con ErBrand y permite editar el estado` with explicit paths.

---

## WU3: Responsive foundation (branch `feature/erato-ajustes-ui-03-responsive-foundation`)

Specs: app-shell-and-navigation (drawer, one-column collapse).

### RED
- [x] 1.1 `layout-css.spec.ts` helper first: add a balanced-brace `mediaBlock(css, query)` helper (existing `ruleBody` regex does not handle nested `@media`); keep every existing assertion green (`npm run test:unit -- layout-css`).
- [x] 1.2 `layout-css.spec.ts`: file has `@media (max-width: 768px)`; block mentions `.er-layout`, `.er-comp-columns`, `.er-auth`, `.er-field-grid`, `.er-sidebar--open`; new selectors `.er-drawer-toggle`, `.er-drawer-backdrop` exist, no hex/rgb/px radius; `prefers-reduced-motion: reduce` rule removes transition; backdrop uses `--bg-000` on a `::before` layer, no `opacity` on a container holding the panel.
- [x] 1.3 New `tests/shared/use-drawer.spec.ts`: `open` starts false; `toggle` flips; `close` sets false.
- [x] 1.4 `composition-detail-view.spec.ts` and `dashboard-view.spec.ts`: toggle has `aria-expanded="false"` and `aria-controls="er-sidebar"` matching aside id; click sets true and adds `er-sidebar--open`; Escape closes and focuses toggle; backdrop click closes; route change closes.
- [x] 1.5 Run focused command; confirm new assertions FAIL.

### GREEN
- [x] 2.1 Create `frontend/src/shared/useDrawer.ts` (`open`, `toggle`, `close`) next to `AppModal.vue` and `useFocusTrap.ts`.
- [x] 2.2 `CompositionDetailView.vue`, `DashboardView.vue`: toggle button (`aria-label="Abrir menú"`), `id="er-sidebar"`, `er-sidebar--open` class, backdrop sibling, Escape listener while open, `watch(route.fullPath)` close, focus to first link on open and back to toggle on close.
- [x] 2.3 `layout.css`: single `@media (max-width: 768px)` block: `.er-layout` one column; `.er-comp-columns`, `.er-auth`, `.er-field-grid` to `1fr`; header/topbar `flex-wrap`; reduced page paddings (existing tokens); off-canvas `.er-sidebar` (`fixed`, `translateX(-100%)`, `visibility:hidden` when closed, delayed); `.er-drawer-backdrop` with `--bg-000` color and opacity on `::before`; toggle shown only inside the block; reduced-motion rule.

### REFACTOR / verify
- [x] 3.1 Focused command green, then full `npm run test:unit`.
- [x] 3.2 `npx vue-tsc --noEmit` and `npm run build` clean.
- [ ] 3.3 Manual QA (author only): 360/390/768/1024px, both themes; no horizontal scroll at 360; drawer opens/closes via button, Escape, backdrop, link tap; focus returns; Tab skips hidden links; screen reader announces expanded state.
- [x] 3.4 Work-unit commit: `feat(ui): agrega diseno responsive con barra lateral tipo cajon` with explicit paths.

---

## WU4: Horizontal fretboard (branch `feature/erato-ajustes-ui-04-horizontal-fretboard`)

Specs: design-system-port (horizontal chord diagram, D6).

### RED
- [ ] 1.1 Extend `frontend/tests/design-system/components/ErChordEditor.spec.ts`: string lines horizontal (`y1 == y2`); nut vertical (`x1 == x2`); high-e row above low-E row; clicking a cell emits the same `set(s, fret)` payloads as before; marker click toggles open/mute.
- [ ] 1.2 Run `npm run test:unit -- ErChordEditor chord-grid`; confirm new assertions FAIL.

### GREEN
- [ ] 2.1 `frontend/src/design-system/components/ErFretboard.vue`: rewrite geometry (frets as columns, strings as rows high e on top, markers left of the nut, base-fret label above first column, W/H swapped, hit rects remapped); keep `er-fb-*` classes, props and `emit('set', s, fret)`.
- [ ] 2.2 `erato-design-system/components/bundle.css` (lines ~103-110): adjust only if a class needs a token-based tweak.

### REFACTOR / verify
- [ ] 3.1 `cd frontend && npm run test:unit -- ErChordEditor chord-grid` green, then full `npm run test:unit`.
- [ ] 3.2 `npx vue-tsc --noEmit` and `npm run build` clean.
- [ ] 3.3 Manual QA (author only): shapes F and Bm, open and muted strings, both themes, 360px inside the card; click sets/clears fret and marker toggles open/mute.
- [ ] 3.4 Work-unit commit: `feat(ui): muestra el diagrama de acordes de guitarra en horizontal` with explicit paths, no AI attribution.

---

## WU5: Chord carousel and polish (branch `feature/erato-ajustes-ui-05-chord-carousel`)

Specs: design-system-port (carousel, usable from 360px). Depends on WU3 (breakpoint) and WU4 (card width derived from the horizontal diagram width).

### RED
- [ ] 1.1 `chord-grid.spec.ts`: wrapper has `role="group"`, `aria-roledescription="carrusel"`, `aria-label="Acordes"`; track `tabindex="0"`; one Eliminar button per chord always present; prev/next (`data-test="chord-prev|chord-next"`, aria-labels "Acorde anterior/siguiente") call stubbed `scrollBy` with +/- width; reduced-motion `matchMedia` stub yields `behavior:'auto'`, otherwise `'smooth'`.
- [ ] 1.2 `layout-css.spec.ts` (use `mediaBlock`): inside 768px block `.er-chord-grid` has `scroll-snap-type`, `.er-chord-grid > .er-field` has `scroll-snap-align`; `.er-chord-carousel`, `.er-chord-nav` exist and are token-only; nav hidden above 768px; polish rules present (tablature `overflow-x:auto`, lyrics toolbar wrap, demo comment row wrap and `min-width:0`, todos actions `flex-shrink:0`, sharing modal `max-height` with scroll).
- [ ] 1.3 Run `npm run test:unit -- chord-grid layout-css`; confirm FAIL.

### GREEN
- [ ] 2.1 `features/compositions/ChordGrid.vue`: add `.er-chord-carousel` wrapper, focusable track, prev/next buttons with `scrollBy` and reduced-motion behavior; keep Eliminar inside each slide.
- [ ] 2.2 `layout.css`: carousel rules (flex track, `scroll-snap-type: x mandatory`, slide `flex:0 0 85%`, visible focus ring, nav hidden above 768px).
- [ ] 2.3 `layout.css` polish inside the 768px block: tablature, lyrics toolbar and touch targets (40px minimum, per spec), demo player and comments, todos, sharing modal. Overflow and target fixes only.

### REFACTOR / verify
- [ ] 3.1 `npm run test:unit -- chord-grid layout-css` green, then full `npm run test:unit`.
- [ ] 3.2 `npx vue-tsc --noEmit` and `npm run build` clean.
- [ ] 3.3 Backend regression, once: `cd /home/bspc/proyectos/erato/backend && .venv/bin/pytest -q` (expect 81 passed; no backend files changed).
- [ ] 3.4 Manual QA (author only): 360/390/768/1024px, both themes; swipe snaps, arrows/buttons scroll, Eliminar reachable, reduced-motion respected; tablature, lyrics maximize/autoscroll, demos/comments, todos, sharing modal usable; contrast 4.5:1.
- [ ] 3.5 Work-unit commit: `feat(ui): agrega carrusel de acordes y ajusta secciones para pantallas pequenas` with explicit paths.
