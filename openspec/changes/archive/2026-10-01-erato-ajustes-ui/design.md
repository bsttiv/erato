# Design: UI adjustments and phone-friendly layout

Source: `proposal.md` (D1-D6 approved). No backend, schema or token changes. Chain: tracker branch
`feature/erato-ajustes-ui`, WU1..WU5 each branching from the previous one, one PR each.

## 1. Decisions

**ADR-1 ErBrand.** New `frontend/src/design-system/components/ErBrand.vue`, exported from
`components/index.ts` (and re-exported by `design-system/index.ts`). Markup: `<span class="er-brand">`
containing `<span class="er-nav-lamp" aria-hidden="true"/>` + `<span class="er-nav-name">Erato</span>`
(classes already in `erato-design-system/components/bundle.css:75-77`; reused, not redefined).
Props: `label?: string` (default `'Erato'`, so ErSideNav keeps its existing `brand` prop). No size
prop: one look everywhere is the goal. Wrapping links stay in the views
(`<router-link to="/" class="er-topbar-brand"><ErBrand/></router-link>`); `.er-topbar-brand` keeps
only link behaviour (no text styling). ErSideNav replaces lines 4-6 with `<ErBrand :label="brand"/>`.
AuthView swaps `<h1 class="er-auth-wordmark">` for `<h1 class="er-auth-wordmark"><ErBrand/></h1>`
(keeps the single h1); the wordmark class only sets alignment/size context.
Rejected: a CSS-only shared class. Five call sites would still duplicate markup and drift again.

**ADR-2 Status editing.** Options constant `STATUS_OPTIONS = [{value:'idea',label:'Idea'},
{value:'in_progress',label:'En progreso'},{value:'ready',label:'Lista'}]` in a small module
`features/compositions/status.ts`, also exporting `statusLabel(value)`; DashboardView group titles
and CompositionCard use it so labels stay consistent (dashboard group heading "Listas" remains a
plural heading; card tag uses `statusLabel`). Create view: `ErSegmented` bound to a `status` ref
(default `'idea'`), included in the `createComposition` payload. Detail header: `ErSegmented` shown
when `canEdit`, otherwise an `ErTag` with `statusLabel`. On change: optimistic update, call
`updateComposition(id, {status})`; on rejection revert the previous value and show the existing
save-state text channel (`er-savestate`) with "No se pudo guardar el estado. Intenta de nuevo."
Disabled while the request is in flight. Dashboard regroups because it reads the stored value on
next load; the detail view also updates the local `comp.status`.
Rejected: a `<select>`. ErSegmented is the approved design-system control and already tested.

**ADR-3 formatDate.** In `design-system/core/format.ts` next to `pad2`:
`formatDate(value: string | number | Date | null | undefined): string`. Uses a module-level
`Intl.DateTimeFormat('es', {day:'numeric', month:'short', year:'numeric'})`. Guard: null/undefined/''
returns `''`; unparsable date (`isNaN(d.getTime())`) returns the raw `String(value)`, never
"Invalid Date". Exported via `core/index.ts`. Applied at `ErDemoPlayer.vue:23,53` and in the detail
view wherever a demo/take date is printed. Output is ICU-dependent ("1 oct 2026" / "1 oct. 2026");
tests assert with regex on day, year and a 3-letter month prefix, not an exact string.
Rejected: `toLocaleDateString` inline per view (no shared invalid guard, harder to test).

**ADR-4 Drawer sidebar.** State lives in a tiny composable `useDrawer()` in
`frontend/src/shared/useDrawer.ts` (`open`, `toggle`, `close`), instantiated by each view that renders
`.er-layout` with a sidebar (Detail and Dashboard). Not a store: it is view-local UI state.
Mobile top bar: a `<button class="er-drawer-toggle" aria-expanded aria-controls="er-sidebar"
aria-label="Abrir menú">` rendered inside the existing topbar/header region, hidden above 768px via
CSS (`display:none` default, `display:inline-flex` in the media query). The `<aside>` gets
`id="er-sidebar"` and class `er-sidebar--open` when open. Behaviour: Escape (keydown listener on
document while open) closes; a `<div class="er-drawer-backdrop">` sibling closes on click; a
`watch(route.fullPath)` closes; on close, focus returns to the toggle (template ref `.focus()`).
Focus moves to the first focusable inside the aside on open. CSS in the 768px block: aside
`position:fixed; inset:0 auto 0 0; width:min(20rem,85vw); transform:translateX(-100%);
transition: transform` with `.er-sidebar--open{transform:none}`; backdrop uses the modal approach:
a separate sibling element whose background is a token-based overlay colour, so no `opacity` on a
container holding the panel. Above 768px aside stays static and toggle/backdrop are hidden.
`prefers-reduced-motion: reduce` removes the transition. When the drawer is closed on phones the
aside has `visibility:hidden` (transition-delayed) so its links leave the tab order.
Rejected: native `<dialog>` for the drawer. Extra top-layer semantics fight the persistent desktop
sidebar using the same element.

**ADR-5 Chord carousel.** Wrapper change only in `ChordGrid.vue`: `.er-chord-grid` stays the track,
a parent `<div class="er-chord-carousel" role="group" aria-roledescription="carrusel"
aria-label="Acordes">` is added. Desktop (>768px): grid unchanged. Phones: `.er-chord-grid` becomes
`display:flex; overflow-x:auto; scroll-snap-type:x mandatory; gap` and each `.er-field` gets
`flex:0 0 85%; scroll-snap-align:center`. The track has `tabindex="0"` (visible `focus-ring`) so
ArrowLeft/ArrowRight scroll natively; prev/next `ErButton`s (`aria-label="Acorde anterior/siguiente"`,
`data-test="chord-prev|chord-next"`) call `track.scrollBy({left:±width, behavior})` where behavior is
`'auto'` if `matchMedia('(prefers-reduced-motion: reduce)').matches` else `'smooth'`; buttons hidden
above 768px by CSS. Per-chord Eliminar button stays inside each slide, always visible (no hover
reveal), so it is reachable by tab and touch. Rejected: a JS carousel library (new dependency, no
need).

**ADR-6 Single 768px breakpoint.** One `@media (max-width: 768px)` block appended to `layout.css`
(plus the existing 620px player rule untouched). Collapse list: `.er-layout` to one column;
`.er-comp-columns`, `.er-auth`, `.er-field-grid` to `grid-template-columns: 1fr`; `.er-comp-header`
and `.er-topbar` `flex-wrap:wrap` with the header actions on their own row; `.er-main`/page paddings
use the smaller existing spacing tokens. Overflow fix (WU1, global): `.er-field-grid` is
`repeat(3, minmax(0,1fr))` and its `input/select` get `width:100%; min-width:0`.
Polish (WU5, inside the same block): tablature container `overflow-x:auto` with `max-width:100%`;
lyrics toolbar wraps and controls get `min-height` 44px equivalent via a spacing token; demo player
controls/comment row wrap, comment input `min-width:0`; todos row actions `flex-shrink:0`; sharing
modal `width:min(100%, ...)` with `max-height` and internal scroll. Only overflow and touch-target
fixes, no redesign.

## 2. File changes per work unit

| WU | Path | Change | ~Lines |
|----|------|--------|--------|
| WU1 | `frontend/src/styles/layout.css` | `.er-field-grid` minmax + input width; `.er-crumb a` hover/underline | 20 |
| WU1 | `features/compositions/CompositionCreateView.vue` | delete top Cancelar (lines 7-9) | -5 |
| WU1 | `features/compositions/CompositionDetailView.vue` | move foot link above ErSideNav; `formatDate` for demo dates | 15 |
| WU1 | `design-system/core/format.ts`, `core/index.ts` | `formatDate` + export | 20 |
| WU1 | `design-system/components/ErDemoPlayer.vue` | use `formatDate` (23, 53) | 6 |
| WU1 | tests: `core/format` spec (new `tests/design-system/format.spec.ts`), `composition-create-view.spec.ts`, `ErDemoPlayer.spec.ts`, `layout-css.spec.ts`, `composition-detail-view.spec.ts` | RED first | 80 |
| WU2 | `design-system/components/ErBrand.vue` (+ `components/index.ts`) | new | 25 |
| WU2 | `ErSideNav.vue`, `DashboardView.vue`, `CompositionCreateView.vue`, `InviteAcceptView.vue`, `AuthView.vue` | swap to ErBrand | 30 |
| WU2 | `features/compositions/status.ts` | options + `statusLabel` | 15 |
| WU2 | `CompositionCreateView.vue`, `CompositionDetailView.vue`, `CompositionCard.vue`, `DashboardView.vue` | status segmented/tag, save+revert, label reuse | 70 |
| WU2 | `layout.css` | `.er-brand`, trim `.er-topbar-brand`/`.er-auth-wordmark` | 15 |
| WU2 | tests: new `ErBrand.spec.ts`, plus ErSideNav, auth-view, invite-accept-view, dashboard-view, composition-create/detail specs | RED first | 90 |
| WU3 | `shared/useDrawer.ts` | new composable | 30 |
| WU3 | `CompositionDetailView.vue`, `DashboardView.vue` | toggle button, ids, backdrop, wiring | 60 |
| WU3 | `layout.css` | 768px block (layout, grids, header, paddings, drawer) | 120 |
| WU3 | tests: new `tests/shared/use-drawer.spec.ts`, detail/dashboard view specs, `layout-css.spec.ts` | | 90 |
| WU4 | `design-system/components/ErFretboard.vue` | axis swap, markers/labels, W/H swap (see 2b) | 90 |
| WU4 | `erato-design-system/components/bundle.css` | only if an `er-fb-*` class needs a token tweak | 10 |
| WU4 | tests: `ErChordEditor.spec.ts` | static geometry + click assertions | 80 |
| WU5 | `features/compositions/ChordGrid.vue` | carousel wrapper, prev/next, reduced-motion; card width from the WU4 diagram width | 45 |
| WU5 | `layout.css` | carousel rules + polish (tab, lyrics, demos, todos, sharing) | 120 |
| WU5 | tests: `chord-grid.spec.ts`, `layout-css.spec.ts` | | 70 |

## 2b. Horizontal fretboard (WU4, decision D6)

`ErFretboard.vue` is one SVG used only by `ErChordEditor.vue`. Today strings are columns at
`X0 + s*DX` and frets are rows at `Y0 + (f-base)*DY`. The horizontal version swaps the roles:
- Frets are columns at `X0 + (f-base)*DX`; strings are rows at `Y0 + r*DY`, where `r = 0` is the high
  e string (top) and `r = 5` the low E (bottom), same order as the tablature editor. The data index
  `s` of `frets: number[]` is unchanged; only its drawn row is mapped.
- Nut is a vertical line at the left (`x1 == x2`) when `base == 1`; string lines are horizontal
  (`y1 == y2`); fret lines are vertical.
- Open/mute markers sit left of the nut (column centre `cx` fixed, `cy` per string row) instead of
  at the top `cy=16`; the base-fret number is drawn above the first visible fret column.
- SVG constants `W` and `H` are swapped (wider than tall); hit rects are one per string row + fret
  column, plus a marker hit area per row. Existing `er-fb-*` classes are kept (token-only); touch
  `bundle.css:103-110` only if a class needs a token-based tweak.
- Contract unchanged: props `frets`, `base`; `emit('set', s, fret)`; accessible labels preserved.
  No orientation prop; the vertical SVG is removed. Chord detection and data are untouched.
- Tests (extend `ErChordEditor.spec.ts`): string lines horizontal (`y1 == y2`); nut vertical
  (`x1 == x2`); high-e row `y` less than low-E row `y`; clicking a cell emits the same
  `set(s, fret)` payloads as before; marker click toggles open/mute. jsdom cannot judge pixels, so
  the look is manual QA.
- Manual QA: shapes F, Bm, open and muted strings; Noche and Matine; 360px inside the carousel card.
- Risks: hit-test regressions (off-by-one string/fret after the swap) covered by the click
  assertions; the wider diagram on phones is handled by the WU5 carousel, whose card width is
  derived from the new diagram width. Rollback: revert WU4 restores the vertical SVG.

## 3. CSS class inventory (token-only; no hex/rgb, no px radii)

New: `.er-brand`, `.er-drawer-toggle`, `.er-drawer-backdrop`, `.er-sidebar--open`,
`.er-chord-carousel`, `.er-chord-nav` (prev/next wrapper). Modified: `.er-field-grid`, `.er-crumb a`,
`.er-topbar-brand`, `.er-auth-wordmark`, `.er-chord-grid`, `.er-sidebar`. Colours, spacing, radii,
shadows, and durations all via `var(--...)`; breakpoint literal 768px is the only raw number (media
queries cannot use vars). Overlay colour for backdrop must be an existing token (check
`tokens.css` for the modal overlay token; reuse what the modal backdrop uses).
`layout-css.spec.ts` additions: (a) every new selector above exists as a rule; (b) the new rules
contain no `#hex`, `rgb(`, or px `border-radius`; (c) the file contains `@media (max-width: 768px)`
and that block mentions `.er-comp-columns`, `.er-auth`, `.er-field-grid`, `.er-sidebar--open`;
(d) `.er-field-grid` uses `minmax(0, 1fr)`; (e) `.er-chord-grid` block under the media query has
`scroll-snap-type`; `.er-chord-grid > .er-field` has `scroll-snap-align`; (f) reduced-motion
`@media (prefers-reduced-motion: reduce)` rule exists. Note the spec's rule regex is non-nested,
so for media blocks the new assertions must slice the block text first (balanced-brace scan).

## 4. Test strategy (strict TDD, RED first)

- **WU1:** `format.spec.ts`: valid ISO gives day/month/year pattern; `null`, `undefined`, `''`
  return `''`; `'not-a-date'` returns the raw string, never contains "Invalid". Create view spec:
  exactly one button with text "Cancelar". ErDemoPlayer spec: take date rendered through
  `formatDate` (no raw ISO `T`/`Z`). Detail spec: first child of the sidebar is the "todas las
  composiciones" link, before the nav; crumb link `href="/"`. layout-css: `.er-field-grid` minmax.
- **WU2:** `ErBrand.spec.ts` renders lamp + name, default and custom label. One assertion per view
  (Dashboard, Create, Invite, Auth, SideNav) that `.er-brand` exists and no leftover
  `.er-auth-wordmark` plain text. Status: create view default `idea`, selecting "Lista" posts
  `status:'ready'`; detail view editor clicking "En progreso" calls mocked `updateComposition` with
  `{status:'in_progress'}`; failure reverts and shows the error text; non-editor sees ErTag and no
  segmented; `statusLabel` mapping used by card/dashboard.
- **WU3:** `use-drawer.spec.ts`: toggle/close state. View specs: toggle has `aria-expanded=false`,
  `aria-controls` matching aside id; click sets `true` and adds `er-sidebar--open`; Escape closes
  and focus returns to toggle; backdrop click closes; route change closes. layout-css as in 3.
- **WU4:** see 2b (geometry and click assertions in `ErChordEditor.spec.ts`).
- **WU5:** `chord-grid.spec.ts`: carousel group has role/aria-label; track `tabindex=0`; Eliminar
  buttons present per chord; prev/next call `scrollBy` (stubbed on element; stub `matchMedia`
  reduced-motion to assert `behavior:'auto'`). layout-css assertions for snap and polish rules.
- **Static vs manual:** jsdom cannot evaluate media queries, layout, scroll-snap behaviour, real
  overflow or contrast. Those are asserted only as rule existence in `layout.css` (text analysis)
  and verified manually (section 5). `Intl` month text depends on Node ICU; use regex.

## 5. Manual QA checklist (per PR, record in the description)

Widths 360, 390, 768, 1024 in Noche and Matine:
- No horizontal page scroll at 360; "compas" input inside its card (WU1+).
- Single Cancelar; sidebar link first; crumb looks and works as a link; focus ring visible.
- Dates read like "1 oct 2026"; bad date never shows "Invalid Date".
- Same logo on dashboard, create, invite, auth, sidebar, in both themes; contrast of lamp and name.
- Status change persists after reload; failure path (offline) reverts with message; viewer sees tag.
- Drawer: open/close by button, Escape, backdrop, link tap; focus returns; Tab does not reach hidden
  links when closed; works with screen reader (VoiceOver/TalkBack announce expanded state).
- Carousel: swipe snaps, arrows and buttons scroll, Eliminar reachable, reduced-motion respected.
- Tablature scrolls inside its card; lyrics maximize and autoscroll; demo player/comments; todos;
  sharing modal fits and scrolls. Touch targets comfortable. Contrast 4.5:1 for link and tags.

## 6. Risks and rollback

- WU1: Cancelar selector in existing tests; grid change affects every form (low). Revert PR.
- WU2: ErSideNav is shared (brand swap) so run all view specs; status revert logic must not race
  with a quick second click (disable during request). Revert PR; data untouched.
- WU3: drawer focus/hidden handling is the riskiest a11y piece; media-query regressions only
  caught manually. Keep rules scoped inside the single block so revert is clean.
- WU4: see 2b (hit-testing regression, manual look check).
- WU5: depends on WU3 breakpoint and WU4 diagram width; scroll-snap with focus can jump on iOS; verify manually.
- Overlay token for the drawer backdrop must exist; if not, stop and propose per AGENTS.md rule 2.
- Global: each unit is a plain `git revert`; no migrations. Review budget 400 lines holds (largest
  unit ~300 including tests).
