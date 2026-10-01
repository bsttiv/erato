# Proposal: UI adjustments and phone-friendly layout

> Upstream artifact: Engram `sdd/erato-ajustes-ui/explore` (observation #132).
> Decisions D1-D6 are already approved by the author and are not re-opened.

## Intent

The author reviewed the running app and listed eight points. Five are small inconsistencies; two
are real gaps; the eighth turns the vertical guitar chord diagram horizontal. The brand looks different on each screen. The "compas" input overflows its card.
The create view shows two "Cancelar" buttons. The "todas las composiciones" link sits below the nav
and the breadcrumb word "composiciones" does not look clickable. Demo take dates render as raw ISO
strings. Status groups (Listas / En progreso / Idea) are shown but cannot be changed. Finally,
`layout.css` has zero `@media` rules, so the app is unusable on a phone. Goal: a consistent,
polished UI that works from phone width up, with no backend or data-model change.

## Scope

### In scope
1. One `ErBrand` component used everywhere (topbar, create bar, invite view, auth hero, sidebar).
2. `.er-field-grid` fix so inputs no longer overflow; one column on phones.
3. Remove the top "Cancelar" in `CompositionCreateView.vue` (keep the bottom one).
4. Sidebar link "todas las composiciones" moved to the top; breadcrumb link looks like a link.
5. `formatDate` helper; demo dates shown as "1 oct 2026" style in `ErDemoPlayer` and the detail view.
6. Status editing UI in the create form and the detail header (existing `status` field).
7. Responsive layout at 768px: drawer sidebar with toggle, chord carousel, small-screen polish
   for tablature, lyrics, demos, todos and sharing.
8. Guitar chord diagram (`ErFretboard.vue`) rendered horizontally instead of vertically.

### Out of scope
- Any backend, schema, endpoint or MongoDB change (`status` already exists: `idea|in_progress|ready`).
- New colours, fonts, radii or tokens; new breakpoints beyond 768px.
- Visual-regression tooling, native app behaviour, offline support.
- Redesign of the auth flow or of the tablature/lyrics editors themselves.

## Decisions (approved by the author)

- **D1** New `ErBrand` component: amber lamp dot (`er-nav-lamp`) + italic "Erato" (`er-nav-name`),
  built only from existing tokens; replaces `.er-topbar-brand` text and `.er-auth-wordmark`.
- **D2** "Collapsible drawer sidebar with toggle button" and "chord carousel" are approved
  design-system additions, built only from existing tokens. Carousel uses CSS `scroll-snap`,
  keyboard accessible, with per-chord edit/remove buttons always reachable.
- **D3** Single breakpoint at 768px, plus the existing 620px player rule.
- **D4** Status is edited in the create form and the detail header (`ErSegmented`/`ErTag`), only
  when the user can edit, saved through `updateComposition`.
- **D5** "todas las composiciones" link goes at the TOP of the sidebar above the nav list; the
  breadcrumb word "composiciones" gets hover/underline styling with existing tokens.
- **D6** (approved) The guitar chord diagram is HORIZONTAL: nut on the left, frets grow to the
  right, high e string on top and low E at the bottom (same order as the tablature editor),
  open/mute markers left of the nut. It REPLACES the vertical SVG (no orientation prop) and is an
  approved design-system variant of the DS vertical diagram. Data model, chord detection and the
  `set(string, fret)` event are unchanged.

## Approach per work unit

**WU1 Quick fixes (points 2, 3, 4, 5, ~150 lines).**
`.er-field-grid` to `repeat(3, minmax(0, 1fr))` with inputs `width:100%`. Delete the top Cancelar
block (`CompositionCreateView.vue:7-9`) and update any test that expects two. Move the foot link
(`CompositionDetailView.vue:16-20`) above `ErSideNav`; style `.er-crumb a` (`layout.css:243-254`).
Add `formatDate` in `design-system/core/format` using
`Intl.DateTimeFormat('es', {day:'numeric', month:'short', year:'numeric'})` with an invalid-date
guard (returns the raw value or empty); apply in `ErDemoPlayer.vue:23,53` and the detail view.

**WU2 Brand + status (points 1, 6, ~200 lines).**
Create `ErBrand`; swap it into `DashboardView`, `CompositionCreateView`, `InviteAcceptView`,
`AuthView` and `ErSideNav`. Add a status `ErSegmented` to the create form (already accepted by
`createComposition`) and to the detail header, visible only to editors, persisting via
`updateComposition`; dashboard grouping and `CompositionCard` update from the stored value.

**WU3 Responsive foundation (point 7, ~300 lines).**
One `@media (max-width: 768px)` block: `.er-layout` single column, reduced page padding,
`.er-comp-columns`, `.er-auth` and `.er-field-grid` to one column, header/topbar wrap. Sidebar
becomes an off-canvas drawer with a toggle button (`aria-expanded`, `aria-controls`, Escape and
backdrop close, focus returned to the toggle). Drawer state is local UI state.

**WU4 Horizontal fretboard (point 8, ~200 lines).**
Swap the axes in `ErFretboard.vue` (strings become rows, frets columns, markers left of the nut,
base-fret number above the first visible column), keep `er-fb-*` classes and the `set` contract.
Tests extend `ErChordEditor.spec.ts` with static geometry assertions. Comes BEFORE the carousel
because the carousel card width is derived from the new diagram width.

**WU5 Chord carousel + small-screen polish (point 7, ~250 lines; depends on WU3 and WU4).**
`ChordGrid.vue` renders chords in a horizontal scroll-snap track on phones (grid kept above
768px), with focusable track, visible focus and always-visible edit/remove buttons. Check
tablature (already scrolls), lyrics maximize/autoscroll, demo player and comments, todos and the
sharing dialog at 360-768px; fix overflow and touch-target sizes only.

## Delivery plan

Five work units, one PR each, each about 400 changed lines or fewer (review policy: 400 lines).
Total ~1100 lines.

| WU | Points | Est. lines |
|----|--------|-----------|
| WU1 | 2, 3, 4, 5 | ~150 |
| WU2 | 1, 6 | ~200 |
| WU3 | 7 (foundation, drawer) | ~300 |
| WU4 | 8 (horizontal fretboard) | ~200 |
| WU5 | 7 (carousel, polish) | ~250 |

Branches: `feature/erato-ajustes-ui-01-quick-fixes`, `-02-brand-status`,
`-03-responsive-foundation`, `-04-horizontal-fretboard`, `-05-chord-carousel`.
Recommended: feature-branch-chain with a tracker branch `feature/erato-ajustes-ui`, each unit
branching from the previous one. WU1 and WU2 are independent; WU5 depends on WU3's breakpoint and
on WU4's diagram width.
**Open decision:** the author has not yet chosen the chain strategy (feature-branch-chain vs
stacked-to-main).

## Risks

- No visual-regression tooling: phone-width checks (360, 390, 768px) are manual in both themes
  Noche and Matine, and must be listed in each PR.
- Drawer and carousel are new patterns: keyboard and focus behaviour need unit tests and a manual
  screen-reader pass.
- Contrast (4.5:1) of the link styling and status tags must hold in both themes.
- Removing the top Cancelar may break an existing test selector.
- `ErSideNav` changes (brand, top link) touch a shared component used by several views.
- Horizontal fretboard (WU4): visual regression on chord editing and hit-testing (jsdom cannot
  judge pixels, so geometry is asserted statically and the look is manual QA); the wider diagram
  on phones is handled by the chord carousel (WU5).
- Status save failures need a visible error and a revert of the optimistic value.
- Strict TDD: each unit starts with RED tests; CSS-only changes are covered by class/DOM tests,
  so layout correctness relies on the manual checks above.

## Rollback

Each unit is an independent PR with no data change, so rollback is a plain `git revert` of that
PR. Status data stays valid because the field already existed. Reverting WU4 restores the vertical
SVG (no data or contract change).

## Success criteria

- The logo is identical on dashboard, create, invite, auth and sidebar views.
- The "compas" input stays inside its card at every width.
- The create view shows a single "Cancelar".
- "todas las composiciones" is first in the sidebar; the breadcrumb word is visibly a link and
  navigates to the dashboard.
- Demo dates read like "1 oct 2026"; invalid values never show "Invalid Date".
- An editor can change a composition's status in the create form and detail header; the dashboard
  regroups accordingly; non-editors see it read-only.
- At 360px width there is no horizontal page scroll; the sidebar opens as a drawer; chords scroll
  as a snap carousel with reachable edit/remove buttons; all sections are usable.
- All UI text is Spanish (tuteo, no exclamation marks or emoji); focus rings visible; both themes
  pass; all new and existing tests green; no backend files changed.
