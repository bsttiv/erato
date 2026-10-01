# Design System Port Specification

## Purpose

Defines the behavioral contract for reimplementing `erato-design-system/` components in Vue 3
(confirmed decision 5), rather than wrapping the existing React bundle. This spec covers fidelity
to the reference design system's appearance, behavior, tokens, and themes. It does not define any
specific feature UI (chord editor layout decisions beyond fidelity, etc.) — those belong to their
respective future feature changes.

## Requirements

### Requirement: Ported components MUST use design system tokens exclusively

Every ported Vue component MUST source colors, typography, spacing, and radii from
`erato-design-system/tokens.css` / `tokens.json`. No component MUST hardcode a color, size, or
radius value that bypasses the token system.

#### Scenario: A ported component renders using token-derived values

- GIVEN a Vue component ports a design-system component (e.g. button, input, card)
- WHEN the component is rendered
- THEN its visual properties (color, spacing, radius, typography) MUST resolve from the design
  system's tokens
- AND MUST NOT contain hardcoded values that duplicate or diverge from a token

### Requirement: Ported components MUST render correctly in both themes

The design system defines two themes — Noche (primary, dark) and Matiné (light). Every ported
component MUST render correctly, with the minimum 4.5:1 text contrast required by AGENTS.md, under
both themes.

#### Scenario: A component renders correctly under the Noche theme

- GIVEN the active theme is Noche
- WHEN a ported component is rendered
- THEN its text contrast MUST meet or exceed 4.5:1
- AND its visual appearance MUST match the design system reference for that theme

#### Scenario: A component renders correctly under the Matiné theme

- GIVEN the active theme is Matiné
- WHEN a ported component is rendered
- THEN its text contrast MUST meet or exceed 4.5:1
- AND its visual appearance MUST match the design system reference for that theme

### Requirement: Non-trivial reference logic MUST be ported with behavioral parity

Logic such as `detectChord()` (including slash chords like `D/F#` and extended chords like
`Cmaj7`, `F#m7b5`, `D9`) and `tabToText()` MUST produce outputs identical to the reference
implementation for equivalent inputs, whether reused directly (if importable independently of the
React bundle) or faithfully reimplemented in Vue/TypeScript.

#### Scenario: Ported chord detection matches the reference for a simple chord

- GIVEN a set of notes that the reference `detectChord()` identifies as a specific chord (e.g. a
  C major triad)
- WHEN the ported implementation receives the same notes
- THEN it MUST return the same chord name as the reference implementation

#### Scenario: Ported chord detection matches the reference for a slash chord

- GIVEN a set of notes with a bass note differing from the root, which the reference
  `detectChord()` identifies as a slash chord (e.g. `D/F#`)
- WHEN the ported implementation receives the same notes
- THEN it MUST return the same slash-chord notation as the reference implementation

#### Scenario: Ported chord detection matches the reference for an extended chord

- GIVEN a set of notes that the reference `detectChord()` identifies as an extended chord (e.g.
  `Cmaj7`, `F#m7b5`, `D9`)
- WHEN the ported implementation receives the same notes
- THEN it MUST return the same extended-chord notation as the reference implementation

#### Scenario: Ported tab-to-text conversion matches the reference

- GIVEN a tablature structure that the reference `tabToText()` converts to a specific text
  representation
- WHEN the ported implementation receives the same tablature structure
- THEN it MUST produce the same text representation as the reference implementation

### Requirement: The tab editor's keyboard interaction MUST be ported with parity

The reference tab editor supports keyboard-driven note entry, arrow-key navigation, measure
insertion, and technique annotations (`h`, `p`, `b`, `/`, `~`, `x`). The ported Vue component MUST
support the same keyboard interactions with equivalent behavior.

#### Scenario: Arrow-key navigation moves the cursor as in the reference

- GIVEN the ported tab editor has focus with a cursor at a given string/position
- WHEN the user presses an arrow key
- THEN the cursor MUST move to the equivalent adjacent position as the reference implementation

#### Scenario: A technique annotation is inserted the same way as the reference

- GIVEN the ported tab editor has focus at a given position
- WHEN the user enters a technique key (`h`, `p`, `b`, `/`, `~`, or `x`)
- THEN the corresponding technique annotation MUST be inserted at that position, matching the
  reference implementation's notation

### Requirement: Interface text and controls MUST follow design system voice and accessibility rules

Per AGENTS.md: interface text is in Spanish, informal (tuteo), without exclamation marks or emoji;
interactive elements MUST be real semantic controls (`<button>`, `<input>`, `<label>`) with a
visible keyboard focus ring.

#### Scenario: A ported interactive control is a real semantic element with visible focus

- GIVEN a ported component includes an interactive control (button, input, etc.)
- WHEN that control receives keyboard focus
- THEN it MUST be implemented as the corresponding real HTML element
- AND MUST display a visible focus ring consistent with the design system's `focus-ring` token
### Requirement: Net-new UI without a reference counterpart MUST be composed from existing primitives and tokens

Some UI introduced by this change has no counterpart in the reference React design system (the
multi-tablature tab strip, the chord palette, drag affordances, and the PDF-faithful page layouts).
This UI MUST be composed from existing ported primitives (`ErButton`, `ErTag`, `ErSegmented`,
`ErSideNav`, etc.) and existing design tokens. Any element that cannot be composed from an existing
primitive — a genuinely new visual component or state — MUST be proposed to the author for approval
before it is built, per AGENTS.md rule 2. Existing ported components used by this change
(`ErChordEditor`, `ErTabEditor`, `ErDemoPlayer`, `ErLyricsViewer`, `ErTodoList`, `ErSideNav`,
`ErSegmented`) MUST remain unmodified by this work.

#### Scenario: The chord palette is built from an existing primitive

- GIVEN the lyrics chord-assignment editor's chord palette
- WHEN its chips are inspected
- THEN each chip MUST be implemented using the existing `ErButton` component (not a new component)

#### Scenario: A genuinely new visual state requires prior author approval

- GIVEN a UI need that cannot be met by an existing primitive or token-derived class (e.g. a
  drag-ghost cursor follower, a drop-target highlight)
- WHEN that need is identified during implementation
- THEN it MUST be proposed to the author as a new design-system state or component before any code
  implementing it is written
- AND MUST NOT be implemented preemptively on the assumption of approval

#### Scenario: Reused components are not modified to support new features

- GIVEN `ErChordEditor`, `ErTabEditor`, `ErDemoPlayer`, `ErLyricsViewer`, `ErTodoList`, `ErSideNav`,
  and `ErSegmented` are reused by this change
- WHEN this change is implemented
- THEN none of these components' source files MUST be modified
- AND any new behavior MUST be implemented in a wrapping container or a new sibling component

### Requirement: Page-level layout CSS is a first-class part of the design-system port

Page-shell, grid, and modal CSS (the layout stylesheet described by the app-shell-and-navigation
capability) is part of the design-system port's scope, not an ad-hoc addition outside it. It MUST
reference only existing design tokens, and its selector set MUST NOT collide with `bundle.css`'s
selector set.

#### Scenario: Layout CSS is reviewed under the same token-only rule as ported components

- GIVEN the app-level layout stylesheet introduced by this change
- WHEN it is reviewed for design-system fidelity
- THEN it MUST be held to the same "tokens only, no hardcoded values" requirement already defined
  for ported components
- AND a selector found in both the layout stylesheet and `bundle.css` MUST be treated as a defect
### Requirement: A single ErBrand component MUST render the logo identically everywhere
`ErBrand` MUST render the amber lamp dot (`er-nav-lamp`) and the italic "Erato" (`er-nav-name`) using only existing tokens. It MUST be used in the dashboard topbar, create bar, invite view, auth hero and sidebar, with no per-view logo markup.

#### Scenario: Same logo
- GIVEN the dashboard, create, invite, auth and sidebar views
- WHEN each renders
- THEN each contains the `ErBrand` markup with identical lamp and name elements

### Requirement: The Tonalidad/Tempo/Compas row MUST NOT overflow its card
`.er-field-grid` MUST use three equal `minmax(0, 1fr)` columns with inputs at `width: 100%`, so no input exceeds the form card at any width.

#### Scenario: Compas stays inside
- GIVEN the create form at any viewport width
- WHEN the three-up row renders
- THEN each input's right edge is within the card's content box

### Requirement: Chords MUST scroll as a keyboard-accessible snap carousel at 768px and below
At 768px or less, `ChordGrid` MUST render chords in a horizontal CSS `scroll-snap` track (grid kept above 768px). The track MUST be focusable, scrollable with arrow keys, and show a visible focus ring. Per-chord edit and remove buttons MUST remain visible and reachable, with touch targets of at least 40px.

#### Scenario: Phone carousel
- GIVEN a composition with 6 chords at 390px
- WHEN the chord section renders
- THEN chords snap horizontally and each chord's edit and remove buttons are focusable

### Requirement: Tablature, lyrics, demos, todos and the sharing modal MUST be usable from 360px
At 360px to 768px these sections MUST have no horizontal page overflow and interactive controls MUST have touch targets of at least 40px, in both Noche and Matine, with text contrast >= 4.5:1.

#### Scenario: Sharing modal on phone
- GIVEN a 360px viewport
- WHEN the sharing modal opens
- THEN it fits within the viewport and all its controls are reachable

### Requirement: The guitar chord diagram MUST render horizontally
The guitar chord diagram (`ErFretboard`) MUST draw strings as horizontal rows with the high e string on top and the low E at the bottom, the nut on the left and frets growing to the right, with open/mute markers left of the nut and the base-fret number above the first visible fret column. It REPLACES the vertical diagram (no orientation option), keeps the `set(string, fret)` event, and uses only existing tokens in Noche and Matine (design decision D6).

#### Scenario: Strings are rows, high e on top
- GIVEN the chord editor in guitar mode
- WHEN the diagram renders
- THEN each string line is horizontal and the high e row is above the low E row

#### Scenario: Nut left, frets to the right
- GIVEN a diagram with base fret 1
- WHEN it renders
- THEN the nut is a vertical line at the left and fret lines are vertical, increasing to the right

#### Scenario: Same click contract
- GIVEN the diagram with no notes
- WHEN the user clicks the cell of string `s` at fret `f`
- THEN the same `set` event is emitted with the same string and fret numbers as the vertical diagram, and clicking the marker area left of the nut toggles open/mute

#### Scenario: Operable and themed
- GIVEN either theme
- WHEN the diagram is used by keyboard or assistive technology
- THEN its accessible labels and focus behavior match the current diagram and no new colors, radii or fonts are introduced
