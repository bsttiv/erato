# Delta for Design System Port

## ADDED Requirements

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
