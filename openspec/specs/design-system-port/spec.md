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
