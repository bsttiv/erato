# App Shell and Navigation Specification

## Purpose

Defines Erato's page shells and the movement between them, matching `erato-design-system/Erato —
pantallas.pdf`: the dashboard shell, the composition shell, the full-page composition-creation
shell, the split-screen auth shell, client-side routing (including the Vercel SPA rewrite needed
for deep links and public share links), the composition page's count-bearing section jump
navigation, and where page-level layout CSS lives. This is a new capability.

## Requirements

### Requirement: The application MUST present four distinct page shells

The application MUST render four structurally distinct shells matching the PDF: a dashboard shell
(top app bar, no sidebar, card grid), a composition shell (persistent sidebar, composition header,
section strip, stacked section panels), a full-page composition-creation shell (minimal bar plus
centered form card, not a modal), and a split-screen auth shell (50/50 hero and form) shared by
login and register.

#### Scenario: The dashboard shell has no persistent sidebar

- GIVEN the user navigates to the dashboard
- WHEN the page renders
- THEN it MUST show a top app bar
- AND MUST NOT show a persistent left sidebar

#### Scenario: The composition shell has a persistent sidebar

- GIVEN the user navigates to a composition page
- WHEN the page renders
- THEN it MUST show a persistent left sidebar listing the user's compositions
- AND MUST show a composition header, a section strip, and stacked section panels

#### Scenario: Creating a composition is a full page, not a modal

- GIVEN the user initiates creating a new composition
- WHEN the creation UI renders
- THEN it MUST render as its own full page with a minimal top bar and a centered form card
- AND MUST NOT render as an overlay/modal on top of another page

#### Scenario: Login and register share the split-screen auth shell

- GIVEN the user navigates to the login page or the register page
- WHEN either page renders
- THEN it MUST show a 50/50 split screen with a hero panel and a form panel
- AND the hero panel MUST be rendered from CSS (backgrounds, gradients, border-radius) with no
  image asset requested over the network

### Requirement: Composition pages and share links MUST be addressable by URL via client-side routing

The application MUST use client-side routing so that the dashboard, each composition, the creation
flow, and the auth pages each have their own URL. A composition's public share link MUST resolve
directly to that composition's page without requiring prior client-side navigation state.

#### Scenario: A composition has its own bookmarkable URL

- GIVEN a user is viewing a specific composition
- WHEN the browser's address bar is inspected
- THEN it MUST show a URL unique to that composition
- AND reloading the browser at that URL MUST return to the same composition's page

#### Scenario: A public share link works for a logged-out visitor opening it directly

- GIVEN a composition is public and its share link is `/c/{slug}`
- WHEN an unauthenticated visitor opens that URL directly (not via in-app navigation)
- THEN the server MUST serve the application shell for that route rather than a 404
- AND the application MUST then render that composition's viewable content

#### Scenario: A direct deep link to any client-side route does not 404

- GIVEN any client-side route the application defines (dashboard, composition, create, login,
  register)
- WHEN that route's URL is requested directly from the server (e.g. a page reload or a bookmark)
- THEN the server MUST respond with the application shell (SPA rewrite), not a 404
- AND the client-side router MUST then render the correct view for that URL

### Requirement: The composition page's section strip MUST be a count-bearing jump navigation, not a tab switcher

The composition page MUST render one strip showing all sections (lyrics, chords, tablature, demos,
tasks) with a count per section (e.g. "acordes 6", "tareas 2/4"). All sections MUST be rendered
simultaneously, stacked on the page; the strip MUST act as in-page jump navigation to each section's
position, and MUST NOT hide sections the way a tab switcher would.

#### Scenario: All sections are visible at once regardless of strip selection

- GIVEN a composition page with lyrics, chords, tablature, demos, and tasks all present
- WHEN the page renders
- THEN all five section panels MUST be present in the document, stacked in sequence
- AND activating a strip item MUST NOT remove or hide any other section from the document

#### Scenario: The strip displays a live count per section

- GIVEN a composition with 6 chord entries, 1 tablature tab, 3 demos, and 2 of 4 tasks completed
- WHEN the section strip renders
- THEN it MUST display "acordes 6", "tablatura 1", "demos 3", and "tareas 2/4" (or equivalent
  localized count labels matching those values)

#### Scenario: Activating a strip item scrolls to that section

- GIVEN the composition page is rendered with the section strip visible
- WHEN the user activates the "tablatura" item in the strip
- THEN the page MUST scroll so the tablature section panel is brought into view
- AND no other section MUST be hidden as a result

### Requirement: Page-level layout CSS MUST live in one app-level stylesheet with no selector collisions

Page-shell, grid, and shared chrome styling (including modal backdrop/centering) MUST be defined in
one app-level stylesheet built only from existing design-system tokens and `bundle.css` classes.
This stylesheet's top-level selectors MUST NOT overlap with `bundle.css`'s top-level selectors, and
it MUST contain no literal color, font-family, or radius value.

#### Scenario: The layout stylesheet and bundle.css share no top-level selector

- GIVEN the app-level layout stylesheet and `bundle.css`
- WHEN their top-level selector sets are compared
- THEN the intersection MUST be empty

#### Scenario: The layout stylesheet contains no literal visual values

- GIVEN the app-level layout stylesheet
- WHEN its declarations are inspected for color, font-family, and border-radius values
- THEN every such value MUST be a `var(--token)` reference
- AND none MUST be a literal hex color, named color, literal font stack, or literal pixel/rem radius

#### Scenario: Every referenced layout class resolves to a rule

- GIVEN every `er-*` class referenced anywhere under `frontend/src/`
- WHEN each class is looked up against `bundle.css` and the app-level layout stylesheet combined
- THEN every referenced class MUST resolve to at least one rule in one of the two stylesheets

### Requirement: Modal components MUST render as real overlays, not inline content

`CompositionCreateModal`, `SharingModal`, and `DemoUploadModal` (or their successors) MUST render
with a backdrop, be centered over the page, and stack above page content (a higher z-index than
page content), and MUST dismiss when the backdrop is clicked or when `Escape` is pressed. They
MUST NOT render inline in normal document flow.

#### Scenario: A modal renders with a backdrop above page content

- GIVEN the sharing modal (or demo-upload modal) is opened
- WHEN it renders
- THEN it MUST display a backdrop element behind it
- AND the modal MUST be visually centered
- AND the modal and its backdrop MUST render above the page's other content (stacking order)

#### Scenario: Clicking the backdrop dismisses the modal

- GIVEN a modal is open with its backdrop visible
- WHEN the user clicks on the backdrop (outside the modal's content area)
- THEN the modal MUST close
- AND no unsaved change inside the modal MUST be silently persisted as a result of the dismissal

#### Scenario: Pressing Escape dismisses the modal

- GIVEN a modal is open
- WHEN the user presses the `Escape` key
- THEN the modal MUST close

### Requirement: No inline style attributes MUST remain in feature components

Page-level and feature-component markup MUST NOT use inline `style="…"` attributes as a substitute
for the layout stylesheet.

#### Scenario: No feature file contains an inline style attribute

- GIVEN any file under `frontend/src/features/`
- WHEN its markup is inspected
- THEN it MUST NOT contain an inline `style="…"` attribute

### Requirement: No deferred PDF affordance without backing behavior MUST be rendered

Per decision D11, affordances shown in the PDF with no corresponding backend behavior (an OAuth
"Continuar con Google" control, a password-reset link, a band entity, dashboard search, and
terms/privacy links) MUST NOT be rendered, whether functional or as a disabled/dead control.

#### Scenario: The login page has no Google sign-in control

- GIVEN the login page renders
- WHEN its controls are inspected
- THEN there MUST NOT be a "Continuar con Google" button or any other unimplemented OAuth control

#### Scenario: No deferred affordance appears in a disabled state as a placeholder

- GIVEN any of the D11-deferred affordances (Google sign-in, password reset, band entity, dashboard
  search, terms/privacy links)
- WHEN the relevant page renders
- THEN none of these affordances MUST appear in the DOM, including in a disabled or placeholder
  form

### Requirement: Pending composition metadata MUST be omitted, not shown as a placeholder value

Until a metadata field (key, bpm, time signature, style tags, status) is actually set on a
composition, the UI MUST omit the corresponding display element rather than show a fabricated or
zero-like placeholder value.

#### Scenario: A composition with no bpm set shows no bpm chip

- GIVEN a composition has no `bpm` value stored
- WHEN its dashboard card or detail header renders
- THEN no bpm chip or label MUST be shown
- AND the UI MUST NOT display a fabricated value (e.g. a hardcoded or zero bpm)
### Requirement: The create view MUST show exactly one Cancelar control
The composition create view MUST render a single "Cancelar" button, located at the bottom of the form.

#### Scenario: Single cancel
- GIVEN an authenticated user on the create view
- WHEN the page renders
- THEN exactly one control labelled "Cancelar" exists and it is in the form footer

### Requirement: The header link to all compositions MUST exist, the sidebar MUST NOT repeat it, and the breadcrumb word MUST be a visible link
The composition header MUST render the "todas las composiciones" link to the dashboard, and the sidebar MUST contain only the composition nav list (the author moved the link from the sidebar to the header after the first implementation). The breadcrumb word "composiciones" MUST be a link to the dashboard with hover and underline styling, text contrast >= 4.5:1 in Noche and Matine, and a visible focus ring.

#### Scenario: Link location
- GIVEN the composition detail view
- WHEN the page renders
- THEN the header contains the "todas las composiciones" link to the dashboard
- AND the sidebar does not contain that link

#### Scenario: Breadcrumb navigation
- GIVEN the breadcrumb on a composition page
- WHEN the user activates "composiciones"
- THEN the app navigates to the dashboard

### Requirement: Below 768px the sidebar MUST be a collapsible drawer
At a viewport width of 768px or less, the sidebar MUST be an off-canvas drawer closed by default, opened by a toggle button with `aria-expanded` and `aria-controls`. Escape or a backdrop click MUST close it and return focus to the toggle. Above 768px the sidebar MUST remain inline and the toggle MUST NOT be shown. Drawer state MUST be local UI state only.

#### Scenario: Open and close by keyboard
- GIVEN a 390px viewport with the drawer closed (`aria-expanded="false"`)
- WHEN the user activates the toggle, then presses Escape
- THEN the drawer opens (`aria-expanded="true"`), then closes and focus returns to the toggle

#### Scenario: Desktop
- GIVEN a 1024px viewport
- WHEN the page renders
- THEN the sidebar is inline and no toggle is visible

### Requirement: Layouts MUST collapse to one column at 768px and below
At 768px or less, `.er-layout`, `.er-comp-columns`, `.er-field-grid`, `.er-auth` and the header/topbar MUST collapse to a single column or wrap, with no horizontal page scroll at 360px, in both themes. A single 768px breakpoint MUST be used for these rules.

#### Scenario: Phone width
- GIVEN a 360px viewport
- WHEN any page renders
- THEN the document has no horizontal scroll and multi-column groups stack vertically
