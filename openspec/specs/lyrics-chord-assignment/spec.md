# Lyrics Chord Assignment Specification

## Purpose

Defines the behavior of assigning a chord to a position within a composition's lyrics: the
pointer-drag interaction, the mandatory keyboard-equivalent interaction, their convergence on a
single bracket-markup edit operation, and round-trip fidelity with the existing read path
(`parseLine()` / `ErLyricsViewer.vue`, both of which remain unmodified). Free-form lyrics text
editing (typing and removing lyric lines or words) is covered by its own requirement at the end of
this spec; chord detection and chord editing remain out of scope.

## Requirements

### Requirement: Placing a chord on a syllable MUST insert bracket markup at that position

Placing a chord at a syllable position in the lyrics editor MUST result in a `[ChordName]` marker
being inserted into the `lyrics.content` string immediately before the text of the targeted
syllable, using exactly the bracket-markup format `parseLine()` already parses.

#### Scenario: Dragging a chord onto an unmarked syllable inserts a new marker

- GIVEN a lyrics line `"Bajo el farol..."` with no chord markers
- WHEN the user places the chord `"Am7"` on the syllable `"farol"`
- THEN the line's stored content MUST become `"Bajo el [Am7]farol..."`
- AND `parseLine()` applied to the result MUST yield a segment with `chord: "Am7"` aligned to
  `"farol..."`

#### Scenario: Placing a chord on an already-marked syllable replaces the existing marker

- GIVEN a lyrics line `"Bajo el [Am7]farol..."`
- WHEN the user places the chord `"Dm"` on the same syllable that already carries `[Am7]`
- THEN the line's stored content MUST become `"Bajo el [Dm]farol..."`
- AND the previous `[Am7]` marker MUST NOT remain in the content

#### Scenario: Removing a chord from a syllable deletes its marker without altering the text

- GIVEN a lyrics line `"Bajo el [Am7]farol..."`
- WHEN the user removes the chord assigned to `"farol"`
- THEN the line's stored content MUST become `"Bajo el farol..."`
- AND no bracket markup MUST remain at that position
- AND the surrounding lyric text MUST be unchanged

### Requirement: Pointer-drag and keyboard placement MUST converge on one shared edit function

Both the pointer-drag interaction and the keyboard-equivalent interaction MUST invoke the same
underlying pure function that performs insert, replace, or remove of a `[Chord]` marker at a
character offset in `lyrics.content`. Neither interaction path MUST contain its own independent
logic for constructing or mutating bracket markup.

#### Scenario: Drag and keyboard placement of the same chord at the same position produce identical content

- GIVEN a lyrics line with no existing chord on a target syllable
- WHEN the chord `"G"` is placed on that syllable via pointer drag in one instance, and via the
  keyboard path in another instance starting from the same initial content
- THEN the resulting `lyrics.content` string MUST be byte-identical in both cases

#### Scenario: The shared edit function is directly unit-testable

- GIVEN the shared bracket-markup edit function
- WHEN it is called directly with an initial content string, an operation (insert/replace/remove),
  a chord name, and a character offset
- THEN it MUST return the resulting content string without requiring a rendered DOM or pointer
  simulation

### Requirement: The keyboard path MUST be a complete, non-degraded equivalent of the drag path

Every chord in the palette and every placeable syllable target MUST be reachable and actionable via
keyboard alone: arming a chord and committing it to a target MUST both be achievable through real
focusable `<button>` elements activated by `Enter` or `Space`, producing the same result as the
equivalent drag gesture.

#### Scenario: A chord is armed and placed using only the keyboard

- GIVEN the lyrics editor is open and a chord palette is visible
- WHEN the user moves focus to a palette chord button and activates it with `Enter` or `Space`,
  then moves focus to a target syllable button and activates it with `Enter` or `Space`
- THEN the chord MUST be placed at that syllable
- AND the resulting `lyrics.content` MUST match what dragging the same chord to the same syllable
  would produce

#### Scenario: Palette chords and drop targets are real, focusable controls

- GIVEN the lyrics editor is rendered with its chord palette and editable syllable spans
- WHEN the DOM is inspected
- THEN every palette chord and every placeable syllable MUST be a real `<button>` element
- AND each MUST display a visible focus ring when focused via keyboard

### Requirement: Chord placement MUST preserve round-trip fidelity with the existing read path

Lyrics content produced by the chord-assignment editor MUST remain fully readable by the unmodified
`parseLine()` function and render correctly, including auto-scroll and maximized mode, in the
unmodified `ErLyricsViewer.vue`.

#### Scenario: Lyrics authored with the chord editor render correctly in the viewer

- GIVEN a lyrics line was edited using the chord-assignment editor to include one or more chord
  placements
- WHEN that line's content is passed to `parseLine()` and rendered by `ErLyricsViewer.vue`
- THEN the viewer MUST display the same chord-over-syllable alignment the editor produced
- AND the viewer's auto-scroll and maximized mode MUST function normally against that content

#### Scenario: The lyrics viewer and parseLine require no code changes

- GIVEN the lyrics chord-assignment editor is implemented
- WHEN `ErLyricsViewer.vue` and `parseLine()` are inspected after implementation
- THEN neither MUST have been modified to support the new editor

### Requirement: The lyrics text MUST be editable as plain text by users who can edit the composition

A user with edit permission on a composition MUST be able to type, change and delete the lyrics
text directly, in a plain-text mode of the lyrics section that is separate from the chord-assignment
mode. The text mode MUST accept the existing markup unchanged (`[Chord]` markers and `# Section`
labels) and MUST NOT interpret or rewrite it. The edited text MUST be persisted as `lyrics.content`
through the typed lyrics endpoint by the same explicit save action used for the other sections. No
data-model change is involved. (Added after the initial release: the original scope left no way to
enter lyrics from the UI.)

#### Scenario: An editor switches to text mode and types lyrics

- GIVEN a user with edit permission views the lyrics section
- WHEN the user activates the "Editar letra" control
- THEN a multi-line text field labelled "Letra" MUST appear containing the current lyrics content
- AND typing in it MUST update the lyrics content held by the composition view immediately
- AND the control's label MUST change to "Ver letra", which returns to the viewer

#### Scenario: Typed lyrics are saved with the explicit save action

- GIVEN the user typed new lyrics in text mode
- WHEN the user activates "Guardar cambios"
- THEN the client MUST send the typed text as `{ content: <typed text> }` to the typed lyrics endpoint
- AND the viewer MUST display the new text after leaving text mode

#### Scenario: Chord markup and section labels are preserved verbatim

- GIVEN the lyrics content contains `"# Coro"` and `"Bajo el [Am7]farol..."`
- WHEN the user opens text mode and leaves it without editing
- THEN the content MUST be unchanged byte for byte

#### Scenario: A read-only visitor cannot edit the lyrics text

- GIVEN a user without edit permission (viewer role or anonymous visitor) views the lyrics section
- WHEN the section renders
- THEN neither the "Editar letra" nor the "Editar acordes" control MUST be rendered
- AND the lyrics MUST remain visible in the viewer
