# Delta: design-system-port

## ADDED Requirements

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
