# Apply Progress & TDD Evidence: erato-ajustes-ui

**Change**: `erato-ajustes-ui` (UI Adjustments and Phone-Friendly Layout)  
**Status**: APPLY COMPLETE — Ready for SDD Verify  
**Branch Chain**: `feature/erato-ajustes-ui-01-quick-fixes` → `-02-brand-status` → `-03-responsive-foundation` → `-04-horizontal-fretboard` → `-05-chord-carousel`

---

## 1. TDD Evidence Table (RED / GREEN / REFACTOR)

| Work Unit | Phase | Target / Test File | Scenario / Assertions | RED Output | GREEN Implementation | REFACTOR / Verification |
|-----------|-------|--------------------|------------------------|------------|----------------------|-------------------------|
| **WU1: Quick fixes** | RED | `tests/design-system/format.spec.ts` | `formatDate()` formats ISO strings, returns raw on error | FAILED (module not found) | `frontend/src/design-system/core/format.ts` | 6 passed |
| | RED | `tests/features/composition-create-view.spec.ts` | Assert exactly one Cancelar button | FAILED (expected 1, found 2) | Removed top Cancelar in `CompositionCreateView.vue` | Passed |
| | RED | `tests/design-system/components/ErDemoPlayer.spec.ts` | Assert demo take dates formatted via `formatDate()` | FAILED (raw ISO found) | Wrapped take dates with `formatDate()` | Passed |
| | RED | `tests/features/composition-detail-view.spec.ts` | Dashboard link precedes `ErSideNav` | FAILED (element order mismatch) | Reordered sidebar children | Passed |
| | RED | `tests/styles/layout-css.spec.ts` | `.er-field-grid` uses `minmax(0, 1fr)`, inputs `width: 100%` | FAILED (CSS rule missing) | Updated grid and input sizing in `layout.css` | Passed |
| | GREEN/REFACTOR | Full unit test suite | All WU1 tests | — | Verified zero regressions | Commit `6f0eaa4` |
| **WU2: Brand and status** | RED | `tests/design-system/ErBrand.spec.ts` | `ErBrand` component renders lamp + title | FAILED (component not found) | Created `ErBrand.vue` | 2 passed |
| | RED | View specs (`ErSideNav`, `auth-view`, `dashboard-view`, etc.) | `.er-brand` rendered instead of plain wordmark | FAILED (`.er-brand` not found) | Replaced wordmarks with `ErBrand` across views | Passed |
| | RED | `tests/compositions/status.spec.ts` | `STATUS_OPTIONS` and `statusLabel()` mapping | FAILED (module not found) | Implemented `status.ts` | 2 passed |
| | RED | `tests/features/composition-detail-view.spec.ts` | Editor status editing, optimistic update, error rollback | FAILED (control missing) | Integrated `ErSegmented` status control with rollback | Passed |
| | GREEN/REFACTOR | Full unit test suite | All WU2 tests | — | Verified zero regressions | Commit `5e672f7` |
| **WU3: Responsive foundation** | RED | `tests/styles/layout-css.spec.ts` | Added `mediaBlock()` parser; asserted 768px rules, drawer tokens | FAILED (media queries missing) | Added 768px `@media` block and drawer CSS in `layout.css` | Passed |
| | RED | `tests/shared/use-drawer.spec.ts` | Composable `open`, `toggle`, `close` states | FAILED (composable missing) | Created `frontend/src/shared/useDrawer.ts` | 3 passed |
| | RED | `tests/features/composition-detail-view.spec.ts` | Drawer toggle `aria-expanded`, backdrop, Escape close | FAILED (toggle button missing) | Wired `useDrawer` and backdrop into detail & dashboard | Passed |
| | GREEN/REFACTOR | Full unit test suite | All WU3 tests | — | Verified zero regressions | Commit `e18e18d` |
| **WU4: Horizontal fretboard** | RED | `tests/design-system/components/ErChordEditor.spec.ts` | Horizontal string lines (`y1 == y2`), vertical nut (`x1 == x2`), hit testing | FAILED (vertical coordinates found) | Re-engineered `ErFretboard.vue` to horizontal layout | Passed |
| | GREEN/REFACTOR | Full unit test suite | All WU4 tests | — | Verified zero regressions | Commit `68dc6a6` |
| **WU5: Chord carousel & polish** | RED | `tests/features/chord-grid.spec.ts` | Carousel wrapper `role="group"`, `aria-roledescription="carrusel"`, scroll buttons | FAILED (carousel attributes missing) | Added `.er-chord-carousel` and scroll controls in `ChordGrid.vue` | Passed |
| | RED | `tests/styles/layout-css.spec.ts` | Assert carousel snap rules and mobile section polish in 768px media | FAILED (rules missing) | Added snap scrolling and small-screen polish in `layout.css` | Passed |
| | GREEN/REFACTOR | Full unit test suite | All WU5 tests | — | Verified zero regressions | Commit `f934275` |
| **Post-Apply Polish** | GREEN/REFACTOR | `tests/styles/layout-css.spec.ts` | Responsive container padding, space-between header, add buttons | PASSED | Adjusted margins, header layout, removed '+' glyphs | Commit `1d2320f` |
| | GREEN/REFACTOR | `tests/styles/layout-css.spec.ts` | Lyrics viewer and todo list right margin containment, chord card height | PASSED | Homogenized card heights and container bounds | Commit `74dad8e` |
| | GREEN/REFACTOR | `tests/styles/layout-css.spec.ts` | Neutralize `sup.er-chord-quality` font baseline; enlarge fretboard | PASSED | Homogenized extended chord card heights, scaled fretboard | Commit `e32076c` |
| | GREEN/REFACTOR | `tests/features/composition-detail-view.spec.ts` | Remove redundant sidebar dashboard link; keep header back button | PASSED | Removed `.er-sidebar-foot` link from detail view template | Commit `f47c188` |

---

## 2. Quality Gate Verification Results

- **Frontend Unit Tests**: `npm run test:unit`
  - Output: 46 test files passed, 286 tests passed (100%).
- **Frontend Typecheck & Production Build**: `npx vue-tsc --noEmit && npm run build`
  - Output: Clean typecheck, 0 TypeScript errors, Vite build successful (dist generated in ~1.45s).
- **Backend Test Suite Regression**: `.venv/bin/pytest tests/ -q`
  - Output: 81 tests passed, 0 failures (100%).
- **CSS Architecture Integrity**:
  - Key-selector disjointness preserved between `layout.css` and `bundle.css`.
  - Zero hardcoded hex/rgb/px-radius literals in `layout.css`.
  - Zero inline styles in Vue templates.

---

## 3. Commit Trail on Tracker Chain

1. `6f0eaa4` `fix(ui): corrige desbordes, Cancelar duplicado, enlace lateral y fechas de demos`
2. `5e672f7` `feat(ui): unifica el logo con ErBrand y permite editar el estado`
3. `e18e18d` `feat(ui): agrega diseno responsive con barra lateral tipo cajon`
4. `68dc6a6` `feat(ui): muestra el diagrama de acordes de guitarra en horizontal`
5. `f934275` `feat(ui): agrega carrusel de acordes y ajusta secciones para pantallas pequenas`
6. `1d2320f` `fix(ui): ajusta margenes responsivos, encabezado, diapason y botones agregar`
7. `74dad8e` `fix(ui): homogeiniza altura de acordes y ajusta contencion de letra y tareas`
8. `e32076c` `fix(ui): homogeiniza altura de acordes extendidos y agranda diapason`
9. `f47c188` `fix(ui): elimina enlace a todas las composiciones de la sidebar`
