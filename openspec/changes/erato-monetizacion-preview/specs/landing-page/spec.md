# Landing Page Specification

Repo: `erato` (directory `landing/`, own Vercel project).

## Purpose

Defines the public marketing site that leads visitors to the app's registration. It is a separate
Vue 3 SPA reusing the app's design system, with no waitlist and no legal text.

## Requirements

### Requirement: The landing MUST present seven slides navigable by index

The landing MUST render seven slides (index 0-6: Inicio, Escribir, Leer, Escuchar, and three further
slides including plans and closing) and MUST show a slide counter reflecting the current index and
total.

#### Scenario: Initial state

- GIVEN a visitor opens the landing
- WHEN the page renders
- THEN slide index 0 MUST be active
- AND the counter MUST show position 1 of 7

#### Scenario: Index bounds

- GIVEN the active slide is index 6
- WHEN the visitor requests the next slide
- THEN the active slide MUST remain index 6
- AND given the active slide is index 0, requesting the previous slide MUST keep index 0

### Requirement: Wheel navigation MUST be debounced and MUST respect scroll exclusions

A wheel gesture MUST move at most one slide per 900 ms. Wheel events originating inside an element
that can itself scroll (a scroll exclusion) MUST NOT change the slide.

#### Scenario: Debounced wheel

- GIVEN slide index 2 is active
- WHEN two wheel-down events occur within 900 ms
- THEN the active slide MUST be index 3 (a single advance)

#### Scenario: Wheel after the debounce window

- GIVEN a wheel advance happened 900 ms or more ago
- WHEN another wheel-down event occurs
- THEN the slide MUST advance again

#### Scenario: Wheel inside a scrollable region

- GIVEN the pointer is over a scrollable region marked as a scroll exclusion
- WHEN a wheel event occurs there
- THEN the active slide MUST NOT change

### Requirement: Keyboard navigation MUST be supported

The landing MUST support keyboard slide navigation (arrow keys, PageUp/PageDown, Home, End) without
requiring a pointing device.

#### Scenario: Arrow keys

- GIVEN slide index 1 is active
- WHEN the visitor presses ArrowDown or ArrowRight
- THEN slide index 2 MUST become active
- AND ArrowUp or ArrowLeft MUST return to index 1

#### Scenario: Keys while typing in a field

- GIVEN focus is inside an editable control
- WHEN the visitor presses an arrow key
- THEN the slide MUST NOT change

### Requirement: Reduced motion MUST be respected

When `prefers-reduced-motion: reduce` matches, slide transitions and decorative animation MUST be
removed or replaced by instant changes.

#### Scenario: Reduced motion preference

- GIVEN the visitor's system prefers reduced motion
- WHEN they navigate between slides
- THEN no animated transition MUST run and the target slide MUST be active immediately

### Requirement: The layout MUST collapse responsively at 980 px

At a viewport width of 980 px or less, multi-column slide layouts MUST collapse to a single column,
with no horizontal page scroll.

#### Scenario: Narrow viewport

- GIVEN a 390 px wide viewport
- WHEN any slide renders
- THEN its content MUST stack in one column
- AND the document MUST have no horizontal scroll

### Requirement: Calls to action MUST lead to the app's register or login

CTAs MUST be native anchors with class `er-btn` (no `ErButton` link variant) whose targets are built
from `VITE_APP_URL`: "Iniciar sesión" to `${VITE_APP_URL}/login`; "Empieza gratis" and every plan
CTA to `${VITE_APP_URL}/register`. There MUST be no waitlist form or email capture.

#### Scenario: Primary CTA

- GIVEN `VITE_APP_URL` is `https://app.example`
- WHEN the visitor activates "Empieza gratis"
- THEN the browser MUST navigate to `https://app.example/register`

#### Scenario: Login link and plan CTAs

- GIVEN the same configuration
- WHEN the "Iniciar sesión" link and each plan CTA are inspected
- THEN the login link MUST target `/login` and every plan CTA MUST target `/register`

#### Scenario: No waitlist

- GIVEN any slide of the landing
- WHEN its controls are inspected
- THEN there MUST be no email-capture or waitlist form

### Requirement: Footer privacy and terms links MUST be placeholders

The footer MUST contain links targeting `#privacidad` and `#terminos`. The landing MUST NOT contain
legal text authored by the agent.

#### Scenario: Placeholder links

- GIVEN the landing footer
- WHEN its links are inspected
- THEN a privacy link with `href="#privacidad"` and a terms link with `href="#terminos"` MUST exist
- AND no privacy policy or terms-of-service body text MUST be present

### Requirement: The landing MUST support both themes and meet accessibility minimums

The landing MUST render in both Noche and Matiné using design-system tokens only (no literal colors,
radii or font stacks), with text contrast of at least 4.5:1, a visible keyboard focus ring, and
real interactive controls (`<a>`, `<button>`).

#### Scenario: Contrast in both themes

- GIVEN the landing in Noche and in Matiné
- WHEN text and background token pairs are evaluated
- THEN every text pair MUST have a contrast ratio of at least 4.5:1

#### Scenario: Focus visibility

- GIVEN a visitor tabs through the page
- WHEN an interactive element receives focus
- THEN a visible focus ring MUST be shown

#### Scenario: Tokens only

- GIVEN the landing stylesheets
- WHEN declarations for color, font-family and border-radius are inspected
- THEN each value MUST be a `var(--token)` reference

### Requirement: The landing MUST reuse the app's design system without modifying it

The landing MUST import design-system components and styles from the app's design system through a
build alias and MUST NOT duplicate or alter them. UI copy MUST be Spanish, informal "tu" address,
without exclamation marks or emoji.

#### Scenario: Shared source

- GIVEN the landing build
- WHEN it resolves design-system imports
- THEN they MUST resolve to `frontend/src/design-system`
- AND no design-system file MUST be changed by this capability

#### Scenario: Copy rules

- GIVEN all visible landing strings
- WHEN they are scanned
- THEN none MUST contain "!" or an emoji character
