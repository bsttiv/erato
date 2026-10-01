# Exploration: Multi-tab tablature + drag-and-drop chord-on-lyrics editor

> Backfilled from Engram `sdd/erato-editor-contenido/explore` (observation #116). The explore phase
> could not write this file due to a tool-access limit in that run; this copy restores hybrid-store
> consistency. Engram remains the authoritative copy.

## Current State

**Tablature today (end-to-end trace):**

- Backend source of truth: `app/schemas/compositions.py` `TablatureSection { strings: int = 6, content: str = "" }` — a single embedded object stored as a flat ASCII string (compatible with `tabToText()` in `frontend/src/design-system/core/tab.ts`, which renders `TabColumn[]` → ASCII text, names-first).
- `app/db/repositories/compositions.py::create_composition` initializes `doc["tablature"] = None`; `update_section(id, "tablature", content)` does a `$set` on the top-level `tablature` field (generic for any section name).
- `app/routers/sections.py` exposes typed, wired endpoints: `GET/PUT /api/compositions/{id}/tablature` (body/response = `TablatureSection`), plus `/chords`, `/lyrics`, `/todos`. These ARE the live, routed endpoints (registered in `app/main.py`).
- `app/routers/compositions.py::_to_response` returns `CompositionResponse` with **flat top-level fields** `chords`, `tablature`, `lyrics`, `todos`, `demos`, `members` — there is **no `sections` wrapper** in the real API response.
- Design-system component `ErTabEditor.vue` operates on `TabColumn[]` (array of 6-string columns or `"|"` barlines), fully keyboard-driven (`useTabKeyboard`), not a plain string.

**Confirmed inconsistency (important finding):** `frontend/src/features/compositions/CompositionDetailView.vue` and `frontend/src/api/compositions.ts` do NOT match the real backend. They read `props.composition.sections?.tab?.columns`, `sections?.chords?.frets`, `sections?.lyrics?.text`, `sections?.todos?.items` — a `sections` wrapper with field names (`tab`, `frets`, `text`, `items`) that do not exist anywhere in `CompositionResponse`/`TablatureSection`/`ChordsSection`/`LyricsSection`/`TodoItem`. `updateSection()` in `api/compositions.ts` also PUTs to a generic `/compositions/{id}/sections/{sectionType}` path with body `{content}`, which does not match the real typed per-section routes (`/chords`, `/tablature`, `/lyrics`, `/todos`) in `sections.py`. This view IS mounted (`CompositionsView.vue` imports and renders `CompositionDetailView`), so the current detail view cannot correctly read or save tablature/chords/lyrics/todos against the real API today — this is pre-existing drift, not introduced by this exploration.

**Chords section (relevant to drag source):** `ChordsSection { instrument: str = "guitar", entries: List[ChordEntry] }`, `ChordEntry { bar: int, notes: List[int], name: str }`. `ChordEntry.name` already carries the detected chord name (e.g. `Am7`), so the palette can source from `sections.chords.entries[].name` with no schema change.

**Lyrics viewer:** `ErLyricsViewer.vue` is read-only today (confirmed). It renders via `parseLine()` (`frontend/src/design-system/core/lyrics.ts`), parsing bracket markup `[Am7]texto` into `{chord, text}` segments (`/\[([^\]]+)\]/g`). `# Coro` marks section headers. `LyricsSection.content: str` already stores this bracket-markup string server-side.

**Visual tab-strip pattern already in the design system:** `ErSegmented.vue` is a plain button-group (`role="group"`, `aria-pressed`, `update:modelValue`/`change`), used today in `ErChordEditor.vue` for guitar/piano toggles. The PDF mockup page 3 shows the composition top nav as exactly this pattern: `letra · acordes 6 · tablatura 1 · demos 3 · tareas 2/4`. This confirms `ErSegmented` (or a nested instance) is the right primitive to reuse for a secondary tab strip inside the tablatura panel, per AGENTS.md rule 2.

## Affected Areas

- `app/schemas/compositions.py` — `TablatureSection` must become `tabs: List[TabEntry]` (`TabEntry = {id, title, columns}`), replacing flat `content: str` with structured column data (bigger than a rename: changes serialization from ASCII string to structured array).
- `app/routers/sections.py` — `/tablature` GET/PUT body shape changes; decide single whole-array endpoint vs. sub-resource endpoints per tab.
- `app/db/repositories/compositions.py::update_section` — generic `$set`, no structural change needed, but callers send the new shape.
- `frontend/src/design-system/components/ErTabEditor.vue` — needs a wrapping multi-tab container holding `tabs[]`, an `ErSegmented` switcher, one `ErTabEditor` per active tab.
- `frontend/src/design-system/core/tab.ts` — add `TabEntry` type + id generator.
- `frontend/src/features/compositions/CompositionDetailView.vue` / `frontend/src/api/compositions.ts` — already broken against the real backend; must be reconciled as part of or alongside this change.
- `frontend/src/design-system/components/ErLyricsViewer.vue` — read-only today; needs an editable sibling/mode to host the drop target with real focusable controls.
- `frontend/src/design-system/core/lyrics.ts` (`parseLine`) — must remain the serialization target so the viewer stays unchanged.
- `erato-design-system/` — reuse `ErSegmented` for tabs (no new primitive); propose a new chip/drop-target primitive for the drag affordance per AGENTS.md rule 2.

## Approaches

**A. Multi-tab UI: nested `ErSegmented` strip inside tablatura panel** — reuse existing primitive, mirrors PDF's `+ Agregar acorde` pattern for add/rename/delete. Pros: no new component, matches approved visual language. Cons: `ErSegmented` needs thin additions for rename/delete affordances. Effort: Low–Medium. **Recommended.**

**B. Dropdown/select for tab switching** — scales to many tabs but diverges from the segmented-tab visual language used elsewhere in the same mockup; not justified given expected low tab cardinality. Effort: Low–Medium.

**C. Native HTML5 Drag and Drop API** (`draggable`, `dragstart/dragover/drop`) — simplest for desktop mouse, but confirmed to have no reliable touch/mobile support, conflicting with AGENTS.md's tablet/phone rehearsal use case, and provides no inherent keyboard alternative (violates AGENTS.md accessibility rule on its own). Effort: Low + mandatory fallback work.

**D. Pointer-event-based custom drag-drop** (`pointerdown/pointermove/pointerup`) — unified mouse/touch/pen handling, full control over drop-target highlighting and syllable hit-testing. Pros: works on tablets per AGENTS.md use case. Cons: more code (manual ghost element, hit-testing, scroll handling). Effort: Medium. **Recommended over C** because native DnD's lack of touch support is disqualifying given the explicit AGENTS.md rehearsal-on-tablet scenario.

**Keyboard fallback (needed regardless of C or D):** "select chord, then select target syllable" — each chord-palette entry and syllable/word becomes a real focusable `<button>`; `Enter`/`Space` arms a chord, `Enter`/`Space` on a target commits the same insert-bracket-before-text operation the drag path uses. Both paths converge on one shared function editing `lyrics.content`, keeping `[Chord]texto` bracket serialization and `parseLine`/`ErLyricsViewer` unchanged.

## Recommendation

1. Reuse `ErSegmented` for the tab strip with thin add/rename/delete affordances (Approach A).
2. Use pointer-events custom drag (Approach D), not native HTML5 DnD, plus a mandatory parallel keyboard select-chord/select-syllable fallback — both writing through one shared bracket-string-edit function so `ErLyricsViewer`/`parseLine` need no changes.
3. Source the chord palette from existing `sections.chords.entries[].name` — no schema change needed there.
4. Explicitly scope, in the coming proposal, whether to fix the confirmed `CompositionDetailView.vue`/`api/compositions.ts` drift against the real flat `CompositionResponse` API as part of this change, since building multi-tab UI atop already-broken data wiring would compound the bug.
5. The `TablatureSection` → `tabs` schema change is larger than pluralization (ASCII string → structured columns) and still requires the author's explicit data-model approval per AGENTS.md rule 1, distinct from the shape decision already recorded in Engram obs #114.

## Risks

- Pre-existing `CompositionDetailView.vue` drift means the current detail view cannot actually persist tablature/chords/lyrics/todos correctly against the real API; must be addressed explicitly, not silently carried forward.
- `TablatureSection.content: str` → `tabs: [...]` is a breaking schema change for any existing non-null `tablature.content` documents; needs a migration/backfill plan or explicit "no production data yet" confirmation, per AGENTS.md rule 1.
- A drag-only interaction without the keyboard/touch fallback would violate AGENTS.md's accessibility rule and fail on tablets used in rehearsal — not optional polish, a hard requirement.
- No hosting-cost implication: pure frontend interaction plus a MongoDB document-shape change; stays within the approved free-hosting constraint (Engram `erato/constraints/free-hosting`).

## Ready for Proposal

Yes. Both named decisions (tabs-array shape, drag-and-drop interaction) are already approved and not re-litigated here. The proposal phase should additionally scope: (a) whether to fix the `CompositionDetailView`/`api/compositions.ts` drift as part of this change, (b) the exact new `TablatureSection`/`tabs` Pydantic shape and migration plan for existing documents (needs author approval per AGENTS.md rule 1), and (c) whether the lyrics drop-target/chord-chip visuals need a new design-system primitive proposal.
