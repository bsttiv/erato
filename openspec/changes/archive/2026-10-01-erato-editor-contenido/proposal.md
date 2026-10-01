# Proposal: Composition content editing and PDF-faithful screens

> Upstream artifact: `openspec/changes/erato-editor-contenido/exploration.md` (Engram
> `sdd/erato-editor-contenido/explore`, observation #116).
> Two product decisions are already **settled** by the author and are not re-opened here:
> the `tabs` array direction (Engram `erato/constraints/multi-tab-schema`, #114) and
> drag-and-drop as the chord-assignment interaction (Engram
> `erato/constraints/lyrics-chord-dragdrop`, #115). What follows is the concrete shape and plan
> to implement them, plus the bug-fix scope that must travel with them.
>
> **Amendment (2026-10-01).** A fourth concern was added after the author ran `docker compose up`
> and saw unstyled raw HTML: the built screens have no page-level CSS at all, and their information
> architecture does not match `erato-design-system/Erato — pantallas.pdf`. Scope item 7 and
> decisions **D5–D11** are new. Everything above D5 is unchanged and D1–D4 remain confirmed.
> The title changed because "multi-tablature and a chord-on-lyrics editor" no longer describes the
> change; the directory and topic key `erato-editor-contenido` are unchanged.

## Intent

A song rarely has one tablature. The intro riff, the bridge and the solo are different fragments
with different names, and today Erato can store exactly one: `TablatureSection { strings, content }`
holds a single flat ASCII string. A band member who writes down the solo overwrites the riff. The
author has approved moving to a `tabs` array so each fragment keeps its own title and identity.

Separately, lyrics can already *display* chords over syllables (`[Am7]Bajo el farol…`), but nothing
can *write* that markup: `ErLyricsViewer.vue` is read-only and no lyrics editor exists. Placing a
chord means hand-typing bracket markup, which is exactly the kind of raw-syntax work the product
set out to remove. The author has approved dragging a chord onto the syllable where it belongs.

There is a third, non-negotiable reason this change needs to happen now. Exploration confirmed that
`frontend/src/features/compositions/CompositionDetailView.vue` and `frontend/src/api/compositions.ts`
are written against an API shape the backend does not have. They read a `sections` wrapper
(`sections.tab.columns`, `sections.chords.frets`, `sections.lyrics.text`, `sections.todos.items`)
and PUT to `/compositions/{id}/sections/{type}`; the real `CompositionResponse` is flat
(`chords`, `tablature`, `lyrics`, `todos`, `demos`, `members`) and the real routes are
`/chords`, `/tablature`, `/lyrics`, `/todos`. The TypeScript `CompositionResponse` also declares
`slug`, `is_public` and `user_role`, none of which the backend returns. That view is mounted, so
**content editing is currently broken end to end**. Building a multi-tab editor and a lyrics editor
on top of that wiring would not ship two features; it would ship two features that cannot save.

### Amendment: the screens are not built, only their contents are

The design-system components are real, ported and styled. The **pages that hold them are not.**
Every page-level class the feature components use is undefined — not in `bundle.css`, not anywhere,
because `frontend/` contains no stylesheet of its own; `main.ts` imports exactly `tokens.css` and
`bundle.css` and nothing else. The result is that `ErChordEditor` renders correctly inside a
`<div class="er-comp-grid">` that is not a grid, inside a `<div class="er-layout">` that is not a
layout. Three modals render inline in document flow because `er-modal-backdrop` and `er-modal` do
not exist either.

Underneath the missing CSS there is a second, larger gap: the screens that *do* exist are a
different product from the PDF. The PDF has a dashboard of composition cards with filters and a
dedicated full-page creation flow; Erato has a single sidebar-plus-detail shell. The PDF has a
split-screen login with a color-block hero; Erato has a panel with a segmented toggle. Fixing the
CSS of what exists would produce a styled version of the wrong screens.

### What success looks like

A band member opens a composition, sees its tablatures as named tabs, adds "Solo", writes it, drags
`F#m7b5` from the chord palette onto the word it lands on, saves, reloads, and finds everything
exactly where they left it — on a laptop with a mouse, on a tablet at rehearsal with a finger, and
with the keyboard alone. And the screen they do it on looks like the screen the author drew.

## Scope

### In Scope

1. **Backend — `tabs` array.** Replace `TablatureSection { strings, content }` with
   `TablatureSection { tabs: List[TabEntry] }`, `TabEntry { id, title, strings, columns }`
   (exact shape in *Approach*, pending author confirmation under AGENTS.md rule 1).
2. **Backend — tablature endpoint.** Keep `GET/PUT /api/compositions/{id}/tablature` and change its
   body/response to the new section shape (whole-array write; see *Approach*).
3. **Frontend — multi-tab tablature UI.** A container above `ErTabEditor.vue` holding `tabs[]`, with
   an `ErSegmented` strip for switching and add / rename / delete / reorder affordances.
4. **Frontend — lyrics chord editor.** An editable lyrics surface with a chord palette sourced from
   `chords.entries[].name`, pointer-event drag-and-drop onto a syllable, and a mandatory keyboard
   path ("arm a chord, then choose a target"). Both paths call one shared bracket-markup edit
   function; `parseLine()` and `ErLyricsViewer.vue` stay unchanged as the read path.
5. **Prerequisite bug fix — API contract reconciliation.** Rewrite `frontend/src/api/compositions.ts`
   and `CompositionDetailView.vue` against the real flat `CompositionResponse` and the real typed
   per-section routes, including the chord-editor wiring (`entries[].notes`, not `frets`) and the
   editability check (today `user_role` is always `undefined`, so the save button never renders).
6. **Tests.** Backend: tablature section round-trip with multiple tabs, permission enforcement
   unchanged (`AGENTS.md` work-style rule). Frontend: the shared bracket-markup edit function
   (insert / replace / remove a chord at an offset) and multi-tab add/rename/delete/reorder.
7. **Page layouts faithful to `Erato — pantallas.pdf` (new).**
   - A single app-level layout stylesheet supplying every page-shell, grid and modal class the
     feature components already reference, built only from `tokens.css` custom properties and
     `bundle.css` classes — no new colors, radii or fonts (AGENTS.md rule 2).
   - Removal of the ad-hoc inline `style="…"` attributes currently standing in for that stylesheet
     in `App.vue`, `CompositionsView.vue`, `CompositionDetailView.vue`, `SharingModal.vue`,
     `DemosSection.vue`, `DemoUploadModal.vue` and `CompositionCreateModal.vue`.
   - Restructuring the screens to the PDF's two distinct page shells: a dashboard (top app bar, no
     sidebar, card grid, filter strip, "Empieza una canción nueva" card) and a composition page
     (persistent `ErSideNav` sidebar, composition header, section strip, stacked section panels).
     Routing is required for this and the project has none today — see **D5**.
   - A full-page "Nueva composición" flow replacing today's modal (PDF page 2).
   - The split-screen auth hero for login and register (PDF pages 6–7).
   - Compartir modal brought to PDF page 5: visibility radio cards, read link with copy,
     permission checklist, invite-by-email with role, and a member list with roles and pending state.
   - Visual-regression-free reuse: `ErChordEditor`, `ErTabEditor`, `ErDemoPlayer`, `ErLyricsViewer`,
     `ErTodoList`, `ErSideNav` and `ErSegmented` are **used as they are**; this item builds the
     frames around them, not replacements for them.

### Out of Scope

- Any change to how chords themselves are detected or edited (`ErChordEditor`, `detectChord()`).
  The palette only *reads* `ChordEntry.name`.
- Automatic tablature generation, tab-from-audio, or chord-from-audio. Tabs stay hand-written per
  AGENTS.md.
- Chord assignment on the maximized / auto-scrolling viewer. Editing happens in the editor surface;
  the viewer stays read-only and untouched.
- Per-tab or per-line collaborative editing, presence, or conflict resolution. The app has no
  optimistic locking anywhere today and this change does not introduce one. This includes the PDF's
  "Ana está editando" presence indicator on page 3 — the words will not be rendered rather than
  rendered falsely.
- A migration script for deployed data. See decision **D1** — the working assumption is that none
  exists, and the author must confirm it rather than have it assumed.
- Audio, storage, auth, or hosting changes. Nothing here touches the free-tier footprint.
- Transposition, capo handling, or chord-diagram rendering inside the lyrics.
- **New (scope item 7).** Every PDF affordance with no backend behind it: "Continuar con Google",
  "¿La olvidaste?" (password reset), the band entity ("Los Faroles", the register form's optional
  *Banda* field), the global search box on the dashboard, and the terms/privacy links. These are
  deferred and will not be rendered as dead controls — see **D11**.
- Responsive / mobile breakpoints beyond what the existing component CSS already does. The PDF is
  drawn at desktop width only. A tablet layout for the rehearsal scenario is real work and deserves
  its own change rather than being smuggled in as "and make it responsive".
- Any new design-system *component*. Scope item 7 composes existing primitives and adds layout
  classes; anything that turns out to need a genuinely new component stops and asks (AGENTS.md
  rule 2).

## Capabilities

### New Capabilities

- `composition-content`: the stored shape and API contract of a composition's editable content
  sections — specifically the multi-tablature `tabs` model, the per-section endpoint contract, and
  the flat response shape the frontend must consume.
- `lyrics-chord-assignment`: assigning a chord to a position in the lyrics, covering the pointer
  drag path, the mandatory keyboard path, their convergence on one bracket-markup edit operation,
  and round-trip fidelity with `parseLine()`.
- `app-shell-and-navigation` *(new in this amendment)*: the application's page shells and movement
  between them — the dashboard shell, the composition shell, the auth shell, how a composition is
  addressed in the URL, and where the page-level layout CSS lives and what it is allowed to contain.

### Modified Capabilities

- `design-system-port`: today this spec covers fidelity to the reference React design system. This
  change adds UI with **no reference counterpart** (a multi-tab strip, a chord palette, drag
  affordances). It needs a requirement stating that net-new UI MUST be composed from existing
  ported primitives and tokens, and that anything genuinely new is proposed to the author under
  AGENTS.md rule 2 before it is built. The amendment extends this: the spec must also state that
  **page-level layout CSS is a first-class part of the port**, that it may only reference existing
  tokens, and that its selector set must not collide with `bundle.css`.
- `sharing-and-visibility` *(newly modified by this amendment)*: PDF page 5 shows a member list with
  names, emails, role labels and a pending-invitation state, and a `solo ver` role. The backend's
  `MemberItem { user_id, role }` cannot express any of that and `CreateInviteRequest.role` accepts
  only `editor`. If **D7** and **D8** are approved, this spec's requirements change.
- `data-persistence` *(newly modified by this amendment, conditional on D6)*: the PDF's composition
  cards and detail header show `tonalidad`, `bpm`, `compás`, `estilo` tags and a status
  (`en progreso` / `lista` / `idea`). None of these fields exist in the stored document. Adding them
  is a MongoDB schema change and therefore an AGENTS.md rule 1 hard gate.

`authentication`, `backend-platform` and `media-storage` are **unmodified**. Note that
`data-persistence` declares collections and fields out of its own scope and defers them to a
separately approved schema proposal — this document is that proposal, now for both the tablature
field (D1) and the composition metadata fields (D6).

## Approach

### 1. The `tabs` shape (requires author confirmation — AGENTS.md rule 1)

```python
# app/schemas/compositions.py
TabColumn = Union[List[str], Literal["|"]]   # six fret/technique strings, or a barline

class TabEntry(BaseModel):
    id: str                                   # stable, client-generated, unique per composition
    title: str = Field(..., min_length=1, max_length=80)   # "Riff intro", "Solo"
    strings: int = 6
    columns: List[TabColumn] = []

class TablatureSection(BaseModel):
    tabs: List[TabEntry] = []
```

Stored document, under the **unchanged** top-level `tablature` key:

```json
"tablature": {
  "tabs": [
    { "id": "t1", "title": "Riff intro", "strings": 6,
      "columns": [ ["", "", "", "2", "", ""], "|", ["0", "", "", "", "", ""] ] }
  ]
}
```

Four deliberate choices, each with its reason:

- **`columns` mirrors the frontend `TabColumn = string[] | "|"` exactly.** The editor already speaks
  this type; storing it verbatim means zero conversion on either side. The alternative — a tagged
  object `{ kind: "col" | "bar", frets: [...] }` — is tidier in a strongly typed store but buys
  nothing here and costs a mapping layer in both directions. The mixed-type array is intentional
  and the trade is named, not overlooked.
- **ASCII is derived, never stored.** `tabToText()` stays the export/display path, computed from
  `columns`. Storing both would create two sources of truth that drift.
- **`strings` moves from the section to the entry.** A composition could hold a 6-string guitar tab
  and a 4-string bass tab. Putting it per entry now costs one field and avoids a second schema
  change later.
- **The Mongo top-level key stays `tablature`.** The repository's generic
  `update_section(id, "tablature", content)` keeps working untouched, and
  `create_composition`'s `"tablature": None` initializer stays valid. Renaming the key to `tabs`
  would buy cosmetics and cost a repository change plus a rename migration.

**Migration.** The working assumption is **no production data and no deployed database** — this
matches the archived design's own "No migration. Nothing is deployed and no data exists." and
`create_composition` writing `tablature: None`. Under that assumption there is nothing to backfill
and the change is a clean cutover. This assumption is stated rather than assumed silently, because
it is the author's to confirm (decision **D1**). If local development data with a non-null
`tablature.content` does exist, the recommendation is to **reset that local data rather than write
an ASCII→columns parser**: re-parsing rendered ASCII back into structured columns is lossy and
error-prone, and a parser written for throwaway dev data is a permanent maintenance liability.

### 2. Tablature endpoint granularity — recommend whole-array PUT

**Recommendation: keep one endpoint**, `GET/PUT /api/compositions/{id}/tablature`, with
`TablatureSection` as body and response. Add / rename / delete / reorder are all expressed as the
client sending the full `tabs` array.

| | Whole-array PUT (recommended) | Per-tab sub-resources |
|---|---|---|
| Routes added | 0 | ~4 (`POST`, `PUT /{tab_id}`, `DELETE /{tab_id}`, reorder) |
| Repository | generic `$set`, unchanged | positional `$` / `arrayFilters` operators, new methods |
| Permission wiring | one existing dependency | four new dependency mounts |
| Consistency with other sections | identical to `/chords`, `/lyrics`, `/todos` | the odd one out |
| Concurrent edits to different tabs | last write wins | independent |
| Payload size | whole array per save | one tab per save |

Rationale: tabs are small, bounded, embedded data, and the frontend already holds the whole
composition in memory behind a single "Guardar cambios" action. Per-tab endpoints would buy
finer-grained concurrency the application cannot currently express — there is no optimistic
locking, no `If-Match`, and no presence anywhere in Erato — while adding four routes and array-
operator complexity to the repository. The accepted cost is last-write-wins when two editors save
the same composition at once, which is **exactly today's behavior for every other section**, so it
is not a regression. If collaborative editing later becomes real, the upgrade path is an
`updated_at` precondition on the existing endpoint, not a different route shape.

### 3. Frontend API reconciliation (work item 0 — must land first)

`api/compositions.ts` is rewritten to mirror the real backend:

| Frontend today | Backend reality |
|---|---|
| `sections: Record<string, any>` | flat `chords`, `tablature`, `lyrics`, `todos`, `demos`, `members` |
| `is_public: boolean` | `visibility: "public" \| "private"` |
| `slug: string` | `share_slug?: string` |
| `sections.chords.frets` | `chords.entries[]` with `{ bar, notes: number[], name }` |
| `sections.lyrics.text` | `lyrics.content` (bracket markup) |
| `sections.todos.items` | `todos: TodoItem[]` (bare array) |
| `PUT /compositions/{id}/sections/{type}` with `{ content }` | `PUT /compositions/{id}/{chords\|tablature\|lyrics\|todos}` with the section body directly |

`updateSection()` is replaced by four typed functions (`updateChords`, `updateTablature`,
`updateLyrics`, `updateTodos`) so the compiler catches the next drift instead of a silent 404 at
runtime. `CompositionDetailView.vue` is rewired accordingly, and `ErChordEditor`'s input is derived
from `chords.entries` rather than the non-existent `frets`.

One sub-decision falls out of this (**D3**): `canEdit` currently reads `composition.user_role`,
which the backend never sends, so it is always falsy and the save button never renders.
**Recommendation: the backend computes `user_role` in `_to_response`**, using the `resolve_role()`
logic that already exists in `app/core/permissions.py`. Deriving the role in the frontend from
`owner_id` and `members[]` would duplicate authorization logic on the client, which sits badly
against AGENTS.md's "los permisos se validan en el backend en cada petición". The field is advisory
UI state only — the backend still enforces on every request — but it should come from the one place
that already knows the answer. This is an API-response addition, not a Mongo schema change, so
rule 1 does not gate it; it is listed because it is a contract decision, not an implementation
detail.

### 4. Interaction design

- **Tab strip**: reuse `ErSegmented.vue` (`role="group"`, `aria-pressed`, real `<button>`s) for
  switching between **tablatures**, inside the tablature section. Add / rename / delete sit beside
  it as `ErButton`s, not as new primitives. (The *section* strip at the top of the composition page
  is a different control — see §7.4 and **D9**.)
- **Drag**: pointer events (`pointerdown` / `pointermove` / `pointerup` with `setPointerCapture`),
  not the HTML5 Drag and Drop API. HTML5 DnD has no reliable touch support, and AGENTS.md's
  rehearsal scenario explicitly includes tablets and phones. This was settled in exploration.
- **Keyboard path, mandatory and equal**: every palette chord and every drop target is a real
  `<button>`. `Enter`/`Space` arms a chord; `Enter`/`Space` on a target commits. It is not a
  degraded fallback — it is the same operation reached differently, required by AGENTS.md's
  accessibility rule (real controls, visible `focus-ring`).
- **One write path**: both drag and keyboard call a single pure function operating on the
  `lyrics.content` string — insert, replace, or remove a `[Chord]` marker at a character offset.
  That function is the unit-test target, and because it writes the same bracket markup `parseLine()`
  already reads, `ErLyricsViewer.vue` and `core/lyrics.ts` need no changes at all.

### 5. Design-system primitives — recommend no new component

**Recommendation: build the chord palette and drop targets from existing primitives; propose only
two new visual *states* to the author under AGENTS.md rule 2.**

- Palette chips → `ErButton` (`size="sm"`, `variant="quiet"`). It is already a real `<button>` with
  the design-system focus ring. `ErTag` is a `<span>` and therefore unusable as a control; it must
  not be given a click handler.
- Drop targets → the syllable spans the lyrics editor renders, promoted to `<button>` **in the
  editor surface only**, reusing the existing `er-seg-lyr` / `er-seg-chord` classes. The viewer keeps
  its spans.
- Genuinely absent from the design system: (a) a floating "ghost" that follows the pointer while
  dragging, and (b) a highlight for the hovered/armed drop target. These are two token-derived state
  classes, not two components. Proposing them as states (decision **D4**) keeps the design system
  from growing a component it does not need.

### 6. The CSS gap, measured

Every `er-*` class in `bundle.css` was enumerated and compared against every class the feature
components use. `frontend/` contains no other stylesheet — `main.ts` imports `tokens.css` and
`bundle.css`, and nothing else — so a class absent from `bundle.css` is absent, full stop.

**Defined in `bundle.css` and working:** `er-row`, `er-label`, `er-panel`, `er-input`, `er-check`,
plus every component-internal class (`er-btn*`, `er-tag*`, `er-seg*`, `er-nav*`, `er-chord*`,
`er-fb-*`, `er-pk-*`, `er-tab-*`, `er-kbd`, `er-lyrics*`, `er-player`, `er-take*`, `er-wave*`,
`er-pin`, `er-times`, `er-comment*`, `er-compose`, `er-todo*`, `er-iconbtn`, `er-ico`, `er-focus`,
`er-select`, `er-range`, `er-stage`).

**Undefined — zero CSS behind them:**

| File | Undefined classes it uses | Consequence |
|---|---|---|
| `App.vue` | `er-app`, `er-header`, `er-app-main` | No shell; header shape comes entirely from four inline `style` attributes |
| `CompositionsView.vue` | `er-compositions-view`, `er-layout`, `er-sidebar`, `er-main`, `er-loading` | The two-column layout does not exist; sidebar and main stack vertically |
| `CompositionDetailView.vue` | `er-comp-detail`, `er-comp-header`, `er-comp-title`, `er-comp-meta`, `er-comp-grid`, `er-comp-column`, `er-role-tag`, `er-save-btn` | The two-column content grid does not exist; panels stack full-width |
| `AuthView.vue` | `er-auth-view`, `er-auth-header` | No split screen, no hero; a bare `er-panel` |
| `LoginForm.vue`, `RegisterForm.vue` | `er-auth-form`, `er-auth-error`, `er-field` | Labels and inputs have no spacing; the error block is unstyled body text |
| `CompositionCreateModal.vue` | `er-modal-backdrop`, `er-modal`, `er-field`, `er-field-row`, `er-checkbox-label`, `er-auth-error` | **Not a modal.** Renders inline in document flow, no backdrop, no centering, no z-index |
| `SharingModal.vue` | `er-modal-backdrop`, `er-modal`, `er-field`, `er-hint`, `er-invites-block`, `er-invite-created`, `er-invites-list`, `er-loading` | Same — not a modal |
| `DemoUploadModal.vue` | `er-modal-backdrop`, `er-modal`, `er-field`, `er-auth-error`, `er-loading` | Same — not a modal |
| `DemosSection.vue` | `er-demos-section` | Harmless wrapper; the player inside it is fully styled |

The three modals are the sharpest finding: `er-modal-backdrop` and `er-modal` are referenced
identically by three unrelated features and defined nowhere, so none of the three is a modal.

### 7. Page layouts — approach

#### 7.1 Where the layout CSS lives — recommend one app-level stylesheet

**Recommendation: `frontend/src/styles/layout.css`, imported third in `main.ts`**, after
`tokens.css` and `bundle.css`. Not scoped `<style>` blocks per component.

Four reasons, in order of weight:

1. **The missing classes cross component boundaries.** `er-layout` / `er-sidebar` / `er-main` are
   authored in `CompositionsView.vue` but must size `CompositionDetailView.vue`'s root, which is a
   child component. Vue's `scoped` attribute deliberately does not apply to a child component's
   internals; expressing this with scoped styles means `:deep()` at every boundary, which is scoped
   styling conceding that it is not scoped.
2. **Three files need the same modal CSS.** `er-modal-backdrop` / `er-modal` are used identically by
   `CompositionCreateModal`, `SharingModal` and `DemoUploadModal`. Scoped blocks triplicate the rule
   and let the three copies drift.
3. **It keeps AGENTS.md rule 2 auditable.** These are `er-`-prefixed, token-only classes — the same
   species as `bundle.css`. One file is one review surface for "no hardcoded colors, sizes or radii",
   and if a class later earns promotion into `erato-design-system/components/bundle.css` the move is
   a copy, not a rewrite.
4. **It is where the inline styles go.** The ~20 inline `style="…"` attributes scattered through the
   feature components are the ad-hoc substitute for this file. They are untestable, unthemeable and
   duplicated. Scoped blocks would relocate the duplication rather than remove it.

The honest cost: a global stylesheet has no encapsulation, so a selector that collides with
`bundle.css` silently overrides it. Mitigation is cheap and turns the risk into a build failure
rather than a visual bug — a unit test that parses both stylesheets and asserts their top-level
selector sets are disjoint. That test is in scope.

This is not a ban on scoped styles. Styling that is genuinely local to one component and used
nowhere else stays in that component's scoped block. The rule is: **page shell, grids, and shared
chrome live in `layout.css`.**

#### 7.2 Information architecture — the PDF has two shells, not one

The brief framed this as "dashboard grid *versus* persistent sidebar". Reading the PDF, that is a
false choice: it has both, on different pages.

- **Page 1 (dashboard)** has a **top app bar** — brand, band name, search, "+ Nueva composición",
  avatar — and **no sidebar**. Below it: a hero headline, a filter strip
  (`todas · en progreso · listas · ideas`), a result count with a sort control, a 3-column card
  grid, and a dashed "Empieza una canción nueva" card.
- **Page 3 (composition)** has a **persistent left sidebar** carrying the brand, `Los Faroles · 6
  composiciones`, the numbered composition list with a key letter per row, and a
  `← todas las composiciones` link at its foot. No top app bar. That sidebar is exactly
  `ErSideNav.vue`, whose `er-nav*` classes are already defined and working in `bundle.css`.
- **Page 2 (new composition)** is a **third shell**: a minimal bar with the brand and `Cancelar`,
  and a centered form card. It is a full page, not a modal.
- **Pages 6–7 (auth)** are a **fourth shell**: a 50/50 split screen.

So today's `CompositionsView.vue` is not "the sidebar version of the dashboard" — it is the
composition page's shell being used as the application's only shell, with the dashboard missing
entirely. The work is to add the shells the PDF has and move the existing content into the right
one. See **D5**, which also covers the routing this requires.

#### 7.3 The auth hero is CSS, not an asset

Confirmed by reading PDF pages 6 and 7. The left panel is: three tall rounded rectangles, one short
rounded rectangle, one small moss-colored pill, a set of thin horizontal rules crossing the lower
half of the bars, a warm radial glow on near-black, the wordmark and a one-line tagline. There is no
photograph and no illustration.

The four block colors map one-to-one onto existing tokens — `--amber` `#e3a857`, the cream paper
tone, `--wine` `#e07a86`, `--ember` `#e07f55`, with the pill on `--moss` `#a9b56e`. The bars use
`--radius-md`/`--radius-lg`, the pill `--radius-pill`, the rules `--line`, the glow
`--shadow-glow`'s amber. **It is literally the token palette drawn as rectangles.**

Consequence, stated explicitly: this introduces **no image asset, no asset pipeline, and no
licensing question**. It is `background`, `border-radius` and `radial-gradient` over existing custom
properties, and it rethemes for Matiné for free because the tokens do.

#### 7.4 Composition header and the section strip

The header (PDF page 3) is: breadcrumb, save state, `// COMPOSICIÓN 00` label, display-serif title,
a status pill, a `Am · 72 bpm · 4/4` metadata chip, style tags, collaborator avatar initials, a
`Compartir` button and an overflow `…`. `ErTag` covers the status pill and style tags. Avatar
initials are a small token-only circle — no component exists, and it should be a layout class rather
than a new design-system component unless the author decides otherwise.

The strip below it (`letra · acordes 6 · tablatura 1 · demos 3 · tareas 2/4`) needs a correction to
the brief. **It is not a tab switcher.** PDF pages 3 and 4 show the same composition with the same
strip and *all* sections rendered, stacked down one scrolling page: letra and tareas side by side,
then the chord grid, then the tablature, then the demos. The strip carries per-section **counts**
and is drawn as a plain underlined row, not as `ErSegmented`'s bordered pill group. Treating it as
an `ErSegmented` tab switcher would both change the behavior (hiding four sections at a time) and
miss the counts, which are the strip's point — they tell you what the song has before you scroll.

Recommendation: build the section strip as a **count-bearing jump navigation** over the stacked
sections, and keep `ErSegmented` for the two places it genuinely is a switcher: the multi-tablature
strip (scope item 3) and the per-chord `guitarra · piano` toggle, which `ErChordEditor` already uses.
This is **D9** and it is the author's call, because it contradicts the instruction this amendment
was given.

#### 7.5 The chord grid

PDF page 3 shows six chord cards with a `+ Agregar acorde` button. Each card is: chord name, note
list, a `guitarra · piano` `ErSegmented`, a fretboard with `‹ ›` fret-position buttons.

That is `ErChordEditor.vue` exactly as it already is — same structure, same `ErChordName`, same
`er-chord-notes`, same `ErSegmented`, same `er-iconbtn` arrows. Nothing inside the card is new work.
What is missing is (a) a responsive grid to lay several of them out, which is a `layout.css` class,
and (b) wiring `chords.entries[]` to render one editor per entry plus an add/remove affordance,
which is part of scope item 5's API reconciliation.

#### 7.6 Page 4 is already built — confirmed, not assumed

Both items the brief flagged as possibly-new were checked against the source:

- **Keyboard-shortcut legend.** `ErTabEditor.vue` lines 65–71 already render it
  (`er-tab-hint` with six `er-kbd` chips: `0–24` traste, `h p b / ~ x` técnica, `← → ↑ ↓` moverse,
  `espacio` avanzar, `enter` insertar tiempo, `|` compás). Both classes are defined in `bundle.css`
  (lines 142–143). This matches the PDF legend token for token. **Already built.**
- **Demo waveform and timestamped comments.** `ErDemoPlayer.vue` already renders the take list
  (`er-takes`/`er-take`), the waveform (`er-wave`, `er-wave-bar`, `er-wave-head`), the pink timestamp
  pins (`er-pin`), the time readouts (`er-times`), the comment list (`er-comments`, `er-comment`,
  `er-comment-t`, `er-comment-who`, `er-comment-txt`) and the comment composer (`er-compose`). All
  are defined in `bundle.css`. **Already built.**

The only gap on page 4 is the page frame and the `+ Subir audio` button's placement — both
`layout.css` work. This is the cheapest part of scope item 7 and should not be budgeted as if it
were component work.

#### 7.7 What the PDF needs that the backend does not have

Three independent data gaps, each surfaced as a decision rather than invented:

1. **Composition metadata.** Cards and the detail header show tonalidad, bpm, compás, estilo tags
   and a status (`en progreso` / `lista` / `idea`). The stored document has none of them —
   `CompositionResponse` is `id, owner_id, title, visibility, share_slug, chords, tablature, lyrics,
   todos, demos, members, created_at, updated_at`. Adding them is a MongoDB schema change →
   **D6**, AGENTS.md rule 1 hard gate. The dashboard and the detail header cannot be built as drawn
   without it.
2. **Visibility vocabulary.** The PDF disagrees with itself: page 2's create form offers three
   options (`la banda · con enlace · solo yo`), page 5's Compartir modal offers two
   (`Con enlace · Privada`). The backend has two (`public` / `private`). → **D7**.
3. **Member identity.** Page 5's member list needs display name, email, avatar initials, a role
   label including `solo ver`, and a `invitación pendiente` state. `MemberItem` is
   `{ user_id, role }` and `CreateInviteRequest.role` is pattern-constrained to `^(editor)$`.
   → **D8**.

Where a decision is pending, the recommendation is to **omit the affordance rather than render a
convincing placeholder**. A bpm chip reading `— bpm` teaches the author the field exists; a hardcoded
`72 bpm` teaches them it works.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/schemas/compositions.py` | Modified | `TablatureSection` → `{ tabs: List[TabEntry] }`; new `TabEntry`, `TabColumn`; optional `user_role` on `CompositionResponse` (D3); metadata fields (D6); member projection (D8) |
| `app/routers/sections.py` | Modified | `/tablature` GET/PUT body and response adopt the new section shape |
| `app/routers/compositions.py` | Modified | `_to_response` populates `user_role` (D3); metadata on create/update (D6) |
| `app/routers/sharing.py` | Modified (D7/D8 only) | Role vocabulary and the resolved member list |
| `app/db/repositories/compositions.py` | Unchanged | Generic `update_section` `$set` already handles the new shape |
| `frontend/src/api/compositions.ts` | Modified | Rewritten against the real flat response; `updateSection` → four typed functions |
| `frontend/src/main.ts` | Modified | Third import: `./styles/layout.css` |
| `frontend/src/styles/layout.css` | **New** | Every page-shell, grid, modal and auth-hero class, token-only (§7.1) |
| `frontend/src/router.ts` (or equivalent) | **New** (D5) | Dashboard, composition, create and auth routes |
| `frontend/src/App.vue` | Modified | Becomes a shell switch; inline styles removed |
| `frontend/src/features/compositions/CompositionsView.vue` | **Restructured** | Becomes the PDF dashboard: top app bar, filter strip, card grid, new-song card |
| `frontend/src/features/compositions/CompositionCard.vue` | **New** | One dashboard card (index, status, title, chord line, counts, footer) |
| `frontend/src/features/compositions/CompositionDetailView.vue` | **Restructured** | Sidebar shell, PDF header, section strip, stacked panels; hosts the multi-tab container and the lyrics editor |
| `frontend/src/features/compositions/CompositionCreateModal.vue` | **Replaced** | Becomes a full-page `CompositionCreateView.vue` (PDF page 2) |
| `frontend/src/features/auth/AuthView.vue` | **Restructured** | Split screen with the token-built hero panel |
| `frontend/src/features/auth/{LoginForm,RegisterForm}.vue` | Modified | PDF copy and field set; inline-style removal; no dead OAuth control (D11) |
| `frontend/src/features/sharing/SharingModal.vue` | **Restructured** | PDF page 5: radio cards, copy link, permission checklist, invite-by-email, member list |
| `frontend/src/features/demos/DemosSection.vue` | Modified | Frame only; `ErDemoPlayer` unchanged |
| `frontend/src/design-system/core/tab.ts` | Modified | Add `TabEntry` type and a stable id generator; `tabToText` unchanged |
| `frontend/src/design-system/core/lyrics.ts` | Modified | Add the shared chord-markup edit function; `parseLine` unchanged |
| `frontend/src/design-system/components/ErTabEditor.vue` | Unchanged | Still edits one `TabColumn[]`; the new container wraps it. Its keyboard legend already matches the PDF |
| `frontend/src/design-system/components/ErDemoPlayer.vue` | Unchanged | Waveform, pins and timestamped comments already match the PDF |
| `frontend/src/design-system/components/ErChordEditor.vue` | Unchanged | Already the PDF's chord card; only the grid around it is new |
| `frontend/src/design-system/components/ErSideNav.vue` | Unchanged | Already the PDF's composition sidebar |
| `frontend/src/design-system/components/` | New | Multi-tab container, lyrics chord editor, chord palette |
| `frontend/src/design-system/components/ErLyricsViewer.vue` | Unchanged | Remains the read-only viewer; this is a design goal, not an omission |
| `frontend/src/design-system/components/ErSegmented.vue` | Unchanged | Reused for the tablature strip and the chord instrument toggle — not for the section strip (D9) |
| `erato-design-system/` | Proposed addition | Two state classes (drag ghost, drop-target highlight) pending author approval (D4) |
| `frontend/package.json` | Modified (D5) | Adds `vue-router` — the only new runtime dependency in this change |
| `tests/`, `frontend/src/**/__tests__` | New | Tablature round-trip, permission regression, markup-edit function, tab operations, stylesheet selector-disjointness |

## Open Decisions for the Author

| ID | Decision | Recommendation | Blocks |
|----|----------|----------------|--------|
| **D1** | Confirm the exact `TabEntry` / `TablatureSection` shape above, and confirm no deployed data has a non-null `tablature.content` | Adopt as written; no migration, reset local dev data if any exists | Backend schema work; `sdd-design` can proceed, `sdd-apply` cannot |
| **D2** | Whole-array `PUT /tablature` vs per-tab sub-resource endpoints | Whole-array PUT (table above) | Endpoint work only |
| **D3** | Backend-computed `user_role` on `CompositionResponse` vs frontend derivation from `owner_id`/`members` | Backend-computed, from existing `resolve_role()` | The editability fix in work item 0 |
| **D4** | Two new design-system state classes (drag ghost, drop-target highlight) vs a new component vs reusing existing states only | Two state classes, no new component | Lyrics editor visuals only |
| **D5** | **Information architecture and routing.** The PDF has four shells (dashboard with top bar and no sidebar; composition page with persistent sidebar; full-page create; split-screen auth). Adopt them, which requires adding `vue-router` — the project has none and `App.vue` switches on a `ref`. Alternative: keep one sidebar shell and give up the dashboard | **Adopt the PDF exactly and add `vue-router`.** Beyond matching the drawing, AGENTS.md's share-by-link requirement needs real URLs (the PDF's own read link is `erato.app/c/noche-de-otono-7f3k`), which a `ref`-based view switch cannot produce. The sidebar is not lost — it is the composition page's shell, as drawn | Scope item 7 almost entirely; also the share-link feature |
| **D6** | **Composition metadata fields** — `key`/tonalidad, `bpm`, `time_signature`/compás, `style_tags[]`, `status` (`en progreso`/`lista`/`idea`), and the create form's per-section include toggles. None exist in the stored document. **MongoDB schema change → AGENTS.md rule 1 hard gate** | Add them as optional fields on the composition document, all nullable, none required to create a song (the PDF's own copy says "Lo demás lo puedes completar después"). Exact field list and types to be presented for approval before any code | The dashboard cards, the create form, and the composition header. Everything else in scope item 7 proceeds without it |
| **D7** | **Visibility vocabulary.** PDF page 2 offers three values (`la banda` / `con enlace` / `solo yo`); PDF page 5 offers two (`Con enlace` / `Privada`); the backend has two (`public` / `private`). Which is canonical? | Ask — this is a product decision, not a reconciliation. If three is right, the backend enum and `UpdateVisibilityRequest` change; if two is right, page 2's form is corrected to match page 5 | The create form and the Compartir modal |
| **D8** | **Member list identity.** PDF page 5 shows name, email, avatar initials, role labels including `solo ver`, and `invitación pendiente`. `MemberItem` is `{ user_id, role }` and invites accept only `role=editor` | Return a **resolved member projection** on the response (name/email/initials/role/pending), computed server-side like D3's `user_role` — a response addition, not a stored-schema change, so rule 1 does not gate it. The `solo ver` role **is** a schema/authorization change and does gate | The Compartir modal's member list and the header's collaborator avatars |
| **D9** | **Section strip semantics.** The brief asked for `ErSegmented` as a letra/acordes/tablatura/demos/tareas tab switcher. PDF pages 3–4 show all sections stacked on one scrolling page with the strip carrying per-section counts and drawn as a plain underlined row | Build it as a **count-bearing jump navigation**, not a tab switcher, and keep `ErSegmented` for the tablature strip and the chord instrument toggle. This contradicts the instruction, so it is the author's call, not a silent correction | The composition page's header area only |
| **D10** | **Where layout CSS lives** — one app-level `frontend/src/styles/layout.css` vs scoped `<style>` per component. AGENTS.md rule 3 makes folder structure an author decision | One app-level stylesheet, for the four reasons in §7.1, plus a selector-disjointness test against `bundle.css`. Scoped blocks remain allowed for genuinely component-local styling | All of scope item 7 |
| **D11** | **PDF affordances with no backend.** "Continuar con Google", "¿La olvidaste?", the band entity (`Los Faroles`, the register form's optional *Banda*), the dashboard search box, terms/privacy links, and the "Ana está editando" presence line | **Defer all of them and render none of them.** A dead "Continuar con Google" button is worse than its absence. Each is a real feature deserving its own change; Google OAuth in particular is the auth-method decision AGENTS.md already reserves for the author | Nothing — this decision only sets what is *omitted* |

These are returned to the orchestrator for the author, not resolved here. Work that does not depend
on them — the frontend API reconciliation of chords, lyrics and todos, the shared markup-edit
function with its tests, the modal and page-shell CSS, and the auth hero (which needs no backend at
all) — is independent and need not wait.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A deployed or shared database does hold `tablature.content` data, making the cutover destructive | Low | D1 confirms before any apply; the archived design states nothing is deployed. If wrong, add a tolerant read that treats legacy `content` as an untitled empty tab and preserves the original string in a `legacy_content` field until the author decides |
| The frontend drift is wider than the four section reads already found (`slug`, `is_public`, `user_role` are also phantom fields) | Confirmed, not hypothetical | Work item 0 rewrites the whole `CompositionResponse` type from the Pydantic model rather than patching field by field; typed per-section functions make the next drift a compile error |
| Pointer-event drag is more code than HTML5 DnD and can break on scroll containers, especially inside the scrolling lyrics box | Medium | `setPointerCapture`, hit-test against live element bounds rather than cached ones, and treat the keyboard path as the correctness baseline the drag path must match |
| The keyboard path is quietly dropped as "polish" under time pressure | Medium | It is an AGENTS.md accessibility requirement and an in-scope deliverable; both paths share one function, so the keyboard path is the cheaper of the two to finish, not the expensive one |
| Scope creep from "lyrics editor" into full lyrics text editing (sections, reordering, formatting) | Medium | This change assigns chords to existing lyrics text; free-form lyrics text editing is a separate change |
| **New:** `layout.css` selectors collide with `bundle.css` and silently override component styling | Medium | A unit test asserting the two stylesheets' top-level selector sets are disjoint; in scope, and it turns the failure mode from a visual bug into a red build |
| **New:** "match the PDF" drifts into pixel-chasing without a stopping rule | High | The acceptance bar is structural fidelity — same regions, same controls, same information per region — not pixel diffing. The PDF is drawn at one desktop width and is not a spec for every viewport |
| **New:** Hardcoded colors or radii creep into `layout.css` to hit a shade the tokens do not have | Medium | AGENTS.md rule 2; the auth hero was verified to map one-to-one onto existing tokens (§7.3), so the most likely offender is already clear. A review check on `layout.css` for literal hex/px color values |
| **New:** Rendering PDF metadata (bpm, tonalidad, status) with placeholder values before D6 is approved, making a missing feature look finished | Medium | Omit the affordance rather than fake it; the dashboard card ships without the metadata line until D6 lands |
| **New:** Adding `vue-router` changes the deploy shape — client-side routes need a Vercel SPA rewrite or every deep link 404s | Medium | Named now rather than discovered after deploy; the rewrite rule is part of the routing slice, and public share links (`/c/{slug}`) are precisely the deep links that must work for logged-out visitors |
| **New:** Restructuring `CompositionsView.vue` and `CompositionDetailView.vue` at the same time as rewiring their API collides slice 0 with slices 4–5 | High | Slice 0 lands the corrected API against the *existing* markup first; the restructure consumes an already-correct data layer. The two never move in the same commit |
| The combined work exceeds the 400-line review budget | **High — materially higher after this amendment** | Nine slices, listed below. `sdd-tasks` MUST forecast chained PRs; `single-pr` is not a viable delivery strategy for this change |
| Hosting cost | None | Frontend interaction, a document-shape change, and one frontend routing dependency; no new service, no new storage class. Stays inside `erato/constraints/free-hosting` |

### Revised slice plan

Nine slices, in dependency order. Each has a clear start, a clear finish, and an independent revert.

| # | Slice | Gated on | Notes |
|---|---|---|---|
| 0 | API contract reconciliation + tests | — | Against existing markup. Must land first |
| 1 | `layout.css` foundation + inline-style removal + modal/backdrop classes + the disjointness test | D10 | Makes today's screens look intentional; no IA change yet |
| 2 | Routing: `vue-router`, the four shells, the Vercel SPA rewrite | D5 | No visual change beyond URLs; pure plumbing |
| 3 | Auth split-screen hero (login + register) | D11 | Fully independent of the backend; could land any time after slice 1 |
| 4 | Composition metadata: schema, API, tests | **D6 (rule 1 gate)** | Backend-only. Nothing renders it yet |
| 5 | Dashboard page: top bar, filter strip, card grid, new-song card, full-page create flow | D5, D6, D7 | The largest frontend slice; may itself split in two |
| 6 | Composition page: header, section strip, stacked panels, chord grid | D5, D6, D9 | Consumes slice 0's data layer |
| 7 | Compartir modal to PDF page 5 | D7, D8 | Backend member projection travels with it |
| 8 | `tabs` schema + endpoint + multi-tab UI | **D1 (rule 1 gate)**, D2 | Formerly slice 1 |
| 9 | Lyrics chord editor | D4 | Formerly slice 2 |

Slices 1, 2 and 3 depend on no unresolved product decision except D10/D5/D11 and are the natural
place to start while D6, D7 and D8 are with the author.

## Rollback Plan

Per slice, each independently revertible:

- **Slice 0 (API reconciliation)**: `git revert` the commit. This restores the *broken* prior state,
  so it is a rollback of last resort — the pre-change behavior is worse than the post-change
  behavior. No data is touched.
- **Slice 1 (`layout.css`)**: remove the import from `main.ts` and delete the file. The application
  returns to today's unstyled state; nothing else depends on it. The cheapest revert in the change.
  Reverting after slices 5–7 is *not* safe, because they assume the classes exist — revert those
  first.
- **Slice 2 (routing)**: revert the commit and `npm uninstall vue-router`. `App.vue` returns to the
  `ref`-based switch. Any bookmarked deep link stops working, which is why this should not be
  reverted after share links are published.
- **Slice 3 (auth hero)**: revert the commit. CSS and markup only; no data, no API.
- **Slice 4 (metadata schema)**: revert the schema commit. Documents written with the new fields keep
  them in Mongo as unread extra keys — Pydantic ignores them on read, so nothing breaks and no data
  is lost. Re-applying the slice recovers them.
- **Slices 5–7 (dashboard, composition page, Compartir)**: revert the commit. Each restores the
  previous page for that route; because slice 2 established the routes, a reverted page is a missing
  page rather than a broken shell.
- **Slice 8 (`tabs` schema + endpoint + UI)**: revert the commit to restore
  `TablatureSection { strings, content }`. Because the Mongo key stays `tablature` and the
  repository's `$set` is generic, no index, collection or repository change needs undoing. Any
  documents written with the new shape would then be read by the old model as an empty section; if
  data exists at that point, dump `tablature` for affected `_id`s before reverting. With D1
  confirmed (no data), the revert is clean.
- **Slice 9 (lyrics chord editor)**: revert the commit. `lyrics.content` is unchanged in format —
  bracket markup written by the editor is the same markup a human would type — so lyrics authored
  with the editor remain fully readable by `ErLyricsViewer` after the revert. Nothing to undo in
  the data.
- **D4 design-system states**: CSS-only addition; removing the classes degrades the drag affordance
  visually without breaking either interaction path.

## Dependencies

- **Author approval of D1** before any backend schema code is written (AGENTS.md rule 1, hard gate).
- **Author approval of D6** before any composition metadata field is added (AGENTS.md rule 1, hard
  gate). The dashboard and composition header cannot be built as drawn until it lands.
- **Author approval of D4** before the drag-ghost / drop-target styles are added to
  `erato-design-system/` (AGENTS.md rule 2).
- **Author approval of D5** before `vue-router` is added — a new runtime dependency and a deploy-shape
  change (AGENTS.md rule 3, architecture decision).
- **Author approval of D10** before `frontend/src/styles/layout.css` is created — folder structure is
  explicitly an author decision under AGENTS.md rule 3.
- **Author answers to D7 and D8** before the Compartir modal and the create form's visibility control.
- Slice 0 (API reconciliation) must land before the page restructuring slices and before slices 8–9;
  all of them build on the corrected data wiring.
- Slice 1 (`layout.css`) must land before slices 5, 6 and 7.
- `vue-router` is the only new runtime dependency in the whole change. No new backend package, no new
  external service.

## Success Criteria

- [ ] A composition stores two or more named tablatures, and each survives a save/reload round trip
      with its title, string count and columns intact.
- [ ] Add, rename, delete and reorder of tablatures all persist through `PUT /tablature`.
- [ ] `CompositionDetailView.vue` reads and saves chords, tablature, lyrics and todos against the
      real backend — verified by a round trip, not by the absence of a console error.
- [ ] Editors see the save control; viewers do not — and the backend rejects a viewer's write
      regardless of what the UI shows.
- [ ] A chord dragged onto a syllable with a mouse, with a finger on a touch device, and placed with
      the keyboard alone all produce byte-identical `lyrics.content`.
- [ ] `ErLyricsViewer.vue` and `parseLine()` are unmodified, and lyrics authored in the editor render
      correctly in the viewer, including auto-scroll and maximized mode.
- [ ] Every new interactive element is a real `<button>` with a visible focus ring, in both Noche and
      Matiné, at 4.5:1 contrast or better.
- [ ] Backend permission tests still pass unchanged; new tests cover the multi-tab round trip and the
      shared chord-markup edit function.
- [ ] No hardcoded colors, sizes or radii introduced; no new design-system component added without
      author approval.
- [ ] **New:** Every `er-*` class referenced anywhere under `frontend/src/` resolves to a rule in
      either `bundle.css` or `layout.css`. Verified by a test, not by eye.
- [ ] **New:** `layout.css` contains no literal color, no literal font family and no literal radius —
      every such value is a `var(--token)` reference. Verified by a test.
- [ ] **New:** `layout.css` and `bundle.css` share no top-level selector.
- [ ] **New:** No inline `style="…"` attribute remains in any file under `frontend/src/features/`.
- [ ] **New:** The three modals (`CompositionCreate`, `Sharing`, `DemoUpload`) render as overlays —
      backdrop, centered, above page content — and dismiss on backdrop click and on `Escape`.
- [ ] **New:** `docker compose up` yields the dashboard at `/`, a composition page at its own URL,
      and the split-screen auth screen — each structurally recognisable as its PDF page: same
      regions, same controls, same information per region.
- [ ] **New:** The auth hero renders with no image request in the network tab, and recolors correctly
      when the theme is switched to Matiné.
- [ ] **New:** `ErTabEditor`, `ErDemoPlayer`, `ErChordEditor`, `ErLyricsViewer`, `ErTodoList`,
      `ErSideNav` and `ErSegmented` are unmodified by scope item 7 — the frames changed, not the
      instruments.
- [ ] **New:** No PDF affordance deferred under D11, and no metadata field pending under D6, is
      rendered as a placeholder or a dead control.
