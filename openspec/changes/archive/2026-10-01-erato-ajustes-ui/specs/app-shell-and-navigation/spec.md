# Delta: app-shell-and-navigation

## ADDED Requirements

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
