# Design: Composition content editing and PDF-faithful screens

> Upstream artifacts: `openspec/changes/erato-editor-contenido/proposal.md` (Engram
> `sdd/erato-editor-contenido/proposal`, obs #117) and
> `openspec/changes/erato-editor-contenido/exploration.md` (obs #116).
> All eleven decisions **D1–D11 are confirmed by the author** (Engram
> `sdd/erato-editor-contenido/decisions-resolved`, obs #118), with **D7 resolved to two
> visibility options**, not three. This document designs *how* to implement that approved scope.
> It does not re-open scope and contains **no application code**.
>
> Base architecture: `openspec/changes/archive/2026-10-01-erato-arquitectura-inicial/design.md`.
> Everything below extends that design — layered backend, authorization as a parameterised
> FastAPI dependency, `db/repositories/` as the only Mongo-aware package, the Vue port emitting
> the reference `er-*` classes. Where this change touches one of those boundaries, the extension
> is named explicitly and the original rule is restated so the two can be read together.

---

## Technical Approach

The change has one spine and four tributaries.

**The spine is the contract.** `frontend/src/api/compositions.ts` describes a backend that does not
exist, and three features are built on top of that description. Every screen in this change reads or
writes composition data, so the corrected contract has to land before anything else is built on it.
That means the first slice is not a feature — it is the TypeScript type regenerated from the Pydantic
model, the four typed per-section functions that replace `updateSection()`, and the two *additional*
drifted modules this design found while reading (`api/sharing.ts` sends `{is_public}` where the
backend reads `{visibility}`, and `createInvite()` sends no body to an endpoint whose body is
required). Nothing downstream is correct until that is.

**Tributary 1 — the stored shape grows two ways.** `TablatureSection` becomes `{ tabs: [...] }` so a
song can hold its riff and its solo at once (D1/D2), and the composition document gains five optional
metadata fields plus a per-section inclusion record (D6). Both are embedded, both are written through
the repository's existing generic `update_section` / `$set` path, and neither needs a new collection,
a new index, or a migration.

**Tributary 2 — the response grows three computed fields.** `user_role`, resolved member identity,
and list-level counts are all *derived server-side from state the request already loaded*. None of
them is stored. This is deliberate: the alternative — deriving the caller's role in the browser from
`owner_id` and `members[]` — would put authorization logic on the client, which AGENTS.md's "los
permisos se validan en el backend en cada petición" exists to prevent. The backend already computes
the answer in `resolve_role()`; it should say it rather than make the client guess.

**Tributary 3 — the application gains an address space.** `App.vue` switches views on a `ref`, which
cannot express a share link. `vue-router` is added (the single new runtime dependency), the PDF's four
shells become four route groups, and a composition acquires a real URL. The public share link
(`/c/{slug}`) is the exact case that must work with no account, so route guarding is designed around
*that* path being open rather than around everything being closed.

**Tributary 4 — the pages gain a stylesheet.** `frontend/src/styles/layout.css` (D10) supplies every
page-shell, grid, modal and hero class the feature components already reference and that resolves to
nothing today. It is built only from `tokens.css` custom properties, it owns a selector set provably
disjoint from `bundle.css`, and the ~20 inline `style="…"` attributes currently standing in for it are
deleted as it lands.

The two interaction features — the multi-tab tablature container and the lyrics chord editor — sit on
top of all four and are the smallest part of the work by volume. Both are *frames around existing
instruments*: `ErTabEditor`, `ErChordEditor`, `ErLyricsViewer`, `ErDemoPlayer`, `ErTodoList`,
`ErSideNav` and `ErSegmented` are not modified.

---

## Architecture Decisions

### Decision: `tabs` is a whole-array `PUT`, and the Mongo key stays `tablature`

**Choice**: `TablatureSection { tabs: List[TabEntry] }` with `TabEntry { id, title, strings, columns }`,
stored under the unchanged top-level `tablature` key, written through the existing
`GET/PUT /api/compositions/{id}/tablature` with the whole array as the body.

**Alternatives considered**: per-tab sub-resources (`POST /tablature`, `PUT /tablature/{tab_id}`,
`DELETE /tablature/{tab_id}`, a reorder route); renaming the Mongo key to `tabs`.

**Rationale**: settled in the proposal (D1/D2) and confirmed. The implementation consequence worth
restating here is that `CompositionsRepository.update_section` needs **no change at all** — it is a
generic `$set` of `{section_name: content}`, and a list of dicts is as valid a value as the dict it
stores today. Per-tab routes would have forced positional `$`/`arrayFilters` operators into that
method and four new permission-dependency mounts, buying concurrency the application cannot express
(there is no optimistic locking, no `If-Match`, no presence anywhere in Erato). Keeping the Mongo key
also keeps `create_composition`'s `"tablature": None` initializer valid, so no repository line changes.

### Decision: composition metadata is six optional top-level fields, not a nested `meta` object

**Choice**: add `key`, `bpm`, `time_signature`, `style_tags`, `status`, and `sections_enabled` as
top-level fields on the composition document.

**Alternatives considered**: a nested `meta: { … }` sub-document; deriving `sections_enabled` from
whether each section is non-null instead of storing it.

**Rationale**: the composition document is already flat — `title`, `visibility`, `share_slug` are
siblings, not members of a `meta` bag — and the access record `deps.py` loads once per request is this
same document, so flat fields stay free to read. A nested object would add a path segment to every
`$set` and every projection for no gain at this size.

`sections_enabled` is stored rather than derived because the two states are genuinely different: PDF
page 2 lets the author say "this song will have a tablature" *before* writing one, and page 2's own
copy promises "Puedes activar más secciones cuando las necesites". Derivation from non-null sections
cannot represent "included but still empty", which is precisely the state a freshly created
composition is in for every section the author ticked.

`status` stores English tokens (`idea`, `in_progress`, `ready`) rather than the PDF's Spanish labels.
The precedent is `visibility: "public" | "private"`, already stored in English next to a UI that reads
"Pública"/"Privada". Stored vocabulary is data; the Spanish labels are presentation and live in the
frontend. Mixing the two conventions inside one document would be the worse outcome.

### Decision: `user_role` and resolved member identity are computed in the response, never stored

**Choice**: `_to_response(doc, role)` gains a `user_role` field populated from the role the permission
dependency already resolved; `MemberItem` gains `display_name` and `initials` resolved through one
batched `users` lookup. Neither is written to Mongo.

**Alternatives considered**: denormalising `display_name` into `compositions.members[]`; deriving the
role client-side from `owner_id` + `members[]`; omitting `user_role` and letting the UI attempt a write
to discover whether it is allowed.

**Rationale**: denormalising a display name into every composition that references a user creates a
fan-out update on rename and a silent-drift bug when that update is missed. Client-side role derivation
duplicates authorization logic in the browser, which is exactly what AGENTS.md's backend-validation
rule forbids; the field is advisory UI state — the backend still enforces on every request — but
advisory state should come from the one place that already knows the answer. Discovering editability by
attempting a write is user-hostile and produces a 403 toast instead of a hidden button.

The cost is one extra Atlas read per composition detail response when `members` is non-empty, which is
bounded: a single `find({_id: {$in: […]}})` over a list the author expects to hold a handful of band
members, skipped entirely when the list is empty. The dashboard **list** endpoint does not resolve
members at all (see the next decision), so the common high-volume path pays nothing.

### Decision: member **email** is never on `CompositionResponse`; it has its own owner-gated endpoint

**Choice**: `CompositionResponse.members[]` carries `user_id`, `role`, `display_name`, `initials` —
enough for the header's collaborator avatars. Full member detail including `email` and pending
invitations lives behind `GET /api/compositions/{id}/members`, mounted with
`Depends(require(Action.MANAGE_SHARING))`.

**Alternatives considered**: putting the full PDF-page-5 projection on `CompositionResponse`.

**Rationale**: `_to_response` is also what `GET /compositions/by-slug/{slug}` returns — to an
**anonymous visitor** who merely holds a public link. Putting `email` on that response would publish
the band's email addresses to anyone with the URL. The Compartir modal that needs those emails is an
owner-only surface by construction (PDF page 5 is reached from the owner's `Compartir` button and every
control in it is a sharing-management control), so the data follows the surface: `manage_sharing`
authority for identity, `view` authority for avatars. Pending invitations are returned by the same
endpoint because they live in the `invitations` collection, not on the composition, and only the owner
has any use for them.

### Decision: the `viewer` invite role needs **one line** of backend change

**Choice**: widen `CreateInviteRequest.role`'s pattern from `^(editor)$` to `^(editor|viewer)$`.

**Alternatives considered**: adding a `Role.VIEWER` branch to `resolve_role`; adding a viewer entry to
`_PERMISSIONS`; a separate "read-only invite" token type.

**Rationale**: verified by reading, not assumed. `app/core/permissions.py:66-67` already maps a
`members[].role == "viewer"` entry to `Role.VIEWER`, `_PERMISSIONS[Role.VIEWER]` is already `{VIEW}`,
and `SharingService.redeem_invite` (`sharing_service.py:89-92`) already passes
`invitation.get("role", "editor")` through to `add_member`. The entire path from invite to enforcement
exists; the only thing rejecting a viewer invite is the request-schema pattern. This is the cheapest
item in the change and it should not be budgeted as a permission-model change — it is a validation
change, and the permission model is already correct.

The behavioural consequence to test rather than assume: a `viewer` member on a **private** composition
resolves to `Role.VIEWER` and can therefore `view` — which is the intended meaning of the PDF's
`solo ver` on a private song, and is *not* the same as the anonymous-public viewer case.

### Decision: one route for a composition, addressed by id **or** slug, with an id-first probe

**Choice**: a single route `/c/:ref`. The loader tries `GET /compositions/{ref}` when `ref` matches
`^[0-9a-f]{24}$`, and falls back to `GET /compositions/by-slug/{ref}` on `404`; a `ref` that does not
match the ObjectId shape goes straight to the by-slug endpoint.

**Alternatives considered**: two routes (`/compositions/:id` for members, `/c/:slug` for share links);
a query parameter discriminator; always calling by-slug.

**Rationale**: the PDF's own read link is `erato.app/c/noche-de-otono-7f3k`, so `/c/…` is the shape the
author drew and the shape that will be pasted into a chat. Two routes for one page would mean the same
composition has two URLs, and a member who copies the URL from their address bar would hand out a link
that 404s for the recipient — the single most likely way a share feature breaks in practice. The
id-first probe costs one extra request only in the rare case where a 24-hex-character share slug
exists, which `generate_share_slug()`'s 128-bit URL-safe output effectively never produces; making the
fallback explicit rather than relying on that improbability keeps the behaviour correct by construction
instead of by luck.

### Decision: the route guard waits on one silent-refresh bootstrap before it redirects

**Choice**: `main.ts` starts a single `authReady` promise at boot — one `POST /api/auth/refresh`
attempt against the `HttpOnly` cookie — and `router.beforeEach` awaits it before deciding whether an
unauthenticated caller must be sent to `/login`.

**Alternatives considered**: guarding on `getAccessToken() !== null` directly; persisting the access
token to `localStorage` so it survives a reload.

**Rationale**: the base design deliberately keeps the access token **in memory only** so an XSS payload
cannot exfiltrate it, with the refresh token in an `HttpOnly; SameSite=Lax` cookie. The direct
consequence is that immediately after any hard refresh the app *is* unauthenticated until a refresh
round trip completes. A guard that reads the token synchronously would therefore bounce every
authenticated deep link to `/login` — which is the same bug as having no deep links at all, arriving
by a different route. Moving the token to `localStorage` would fix the symptom by discarding the
decision that produced it. One awaited promise, created once and shared, fixes it without touching the
token strategy.

### Decision: `vercel.json` needs **no change** for client-side routing

**Choice**: ship the routing slice against the existing `vercel.json`.

**Alternatives considered**: adding an SPA-specific rewrite; adding a `cleanUrls`/`trailingSlash`
block.

**Rationale**: verified by reading the file. `vercel.json` already declares
`{"source": "/(.*)", "destination": "/index.html"}` *after* `{"source": "/api/(.*)", …}`. API paths win
by order, Vercel applies rewrites only after static-file matching so hashed build assets still serve
themselves, and every other path — including `/c/{slug}` on a cold deep link — lands on `index.html`
where the router takes over. The proposal listed "adding `vue-router` changes the deploy shape" as a
medium risk; reading the file retires it. The deploy shape was already correct, which also means the
free-hosting constraint (`erato/constraints/free-hosting`) is untouched: no new function, no new
route, no new build step, and `vue-router` is ~25 kB of client JavaScript served from the same static
bundle.

### Decision: `layout.css` owns page shells; `bundle.css` keeps owning components

**Choice**: one app-level `frontend/src/styles/layout.css`, imported third in `main.ts` after
`tokens.css` and `bundle.css`. Its rules may only have **key selectors it owns** — a rule whose
rightmost compound selector contains a class defined by `bundle.css` is forbidden and is caught by a
test.

**Alternatives considered**: scoped `<style>` blocks per component (rejected in the proposal's §7.1 and
by D10); CSS Modules; leaving the inline styles in place.

**Rationale**: D10 settled *where*. What this design adds is *what "disjoint" means*, because the
honest risk the proposal named — "a selector that collides with `bundle.css` silently overrides it" —
needs an operational definition before a test can assert it. "The two files never mention the same
class" is too strict: `<div class="er-modal er-panel">` legitimately puts a layout class and a
component class on one element. "The two files never define an identical selector string" is too loose:
`.er-modal .er-panel { padding: 0 }` would silently restyle every panel inside every modal and pass.

The rule that draws the line in the right place is the **key selector**: for each rule, split the
selector list on commas, take the rightmost compound of each, and collect its classes. That set is what
the stylesheet *styles*. `.er-modal` styles `er-modal`; `.er-modal .er-panel` styles `er-panel` and is
therefore rejected. Co-styling one element by putting two classes on it remains legal and is how layout
composes with components; reaching into a component's internals does not. Because `layout.css` loads
last, the cascade would let it win any such conflict silently — which is exactly why the constraint is
a test and not a convention.

### Decision: the modal is an application component, not a design-system primitive

**Choice**: `frontend/src/shared/AppModal.vue` plus `frontend/src/shared/useFocusTrap.ts`, composed
from `er-panel` and `layout.css` classes, used by `CompositionCreateModal` (which becomes a page — see
below), `SharingModal` and `DemoUploadModal`. Nothing is added to `erato-design-system/` for it.

**Alternatives considered**: an `ErModal.vue` under `frontend/src/design-system/components/`; a new
`Modal` in `erato-design-system/`; leaving each modal to implement its own overlay.

**Rationale**: AGENTS.md rule 2 and the proposal's Out of Scope both say a genuinely new
*design-system component* stops and asks the author. This one does not need to: it introduces no new
visual language — the dialog surface is `er-panel`, the buttons are `ErButton`, the eyebrow is
`er-label` — and contributes only positioning, stacking, focus management and dismissal, which is
application chrome rather than design vocabulary. Putting it under `design-system/` would imply a
reference counterpart in `erato-design-system/components/` that does not exist and would make the
port's 1:1 mapping untrue. If it later earns promotion, moving it is a copy plus an author
conversation, which is cheaper than asking for approval now for something the approved D10 scope
("page shell, grids, and shared chrome live in `layout.css`") already covers.

Three files implementing the same overlay independently is the status quo and is what produced three
non-modals; one component is the point of the fix.

### Decision: the chord-markup edit operates on plain-text offsets, not raw-markup offsets

**Choice**: one pure function in `frontend/src/design-system/core/lyrics.ts` that decomposes a line into
`(plainText, marks)`, applies insert/replace/remove at a **plain-text** character offset, and
recomposes the bracket markup.

**Alternatives considered**: editing the raw string by regex at a raw-string index; storing chords in a
parallel structure alongside the lyrics text.

**Rationale**: a drop target is a syllable the user can see, and what the user sees is the line with
the `[…]` markers removed. Raw-string indices shift every time a marker is inserted ahead of them, so a
raw-offset API would make the caller responsible for bookkeeping that the function is better placed to
do — and would make the drag path and the keyboard path compute the same correction twice, which is the
exact place they would diverge. Decomposing first makes the operation's invariant statable and
testable: `compose(decompose(x)) === x`, and the output for a given `(line, offset, chord)` is
byte-identical regardless of which input path produced it. That invariant is the success criterion
"a chord dragged with a mouse, with a finger, and placed with the keyboard alone all produce
byte-identical `lyrics.content`", reduced to a unit test.

A parallel chord structure was rejected outright: it would stop `ErLyricsViewer` and `parseLine()` from
being the read path, and keeping them untouched is a stated design goal, not an omission.

### Decision: pointer events with live hit-testing, and removal expressed as an armed sentinel

**Choice**: `pointerdown`/`pointermove`/`pointerup` with `setPointerCapture`, hit-testing via
`document.elementFromPoint(...).closest('[data-chord-target]')` evaluated on every move. The palette
includes a `✕ quitar` chip that arms the sentinel "no chord"; dropping or committing it on a target
removes that target's chord.

**Alternatives considered**: HTML5 Drag and Drop; caching `getBoundingClientRect()` for all targets at
`pointerdown`; making "activate a target with nothing armed" mean "remove".

**Rationale**: HTML5 DnD has no reliable touch support and AGENTS.md's rehearsal scenario names tablets
explicitly; this was settled in exploration. Caching bounds at drag start is the tempting optimisation
and it is wrong here specifically: the lyrics surface is a scrolling box (`er-lyrics-scroll` is
`overflow-y: auto`), so any scroll during a drag — including the autoscroll a user may have left
running — invalidates every cached rectangle and lands the chord on the wrong syllable.
`elementFromPoint` is evaluated against live layout by definition. Note that pointer capture redirects
*events* to the captured element but does not affect hit-testing, so `elementFromPoint` keeps reporting
the element actually under the pointer, which is what makes this combination work.

Removal via an armed sentinel rather than "activate with nothing armed" keeps both paths on one
mechanism and avoids a destructive action triggered by pressing `Enter` on a focused syllable — which
is something a keyboard user does while navigating, not only while editing.

### Decision: `ErTabEditor` is remounted per tab via `:key`, not re-fed via props

**Choice**: the multi-tab container renders `<ErTabEditor :key="activeId" :model-value="activeTab.columns" …>`.

**Alternatives considered**: a single persistent `ErTabEditor` instance updated by changing
`:model-value`; adding a `watch` on `props.modelValue` inside `ErTabEditor`.

**Rationale**: verified by reading `ErTabEditor.vue:104-105` — it snapshots its input once
(`const cols = ref(initialCols.slice())`) and never watches the prop afterwards. Feeding it a new
array on tab switch would therefore change nothing on screen and the user would edit tab A while
looking at tab B's label. Adding a `watch` would modify a component the proposal lists as
**Unchanged**, and would introduce an emit/watch feedback loop that needs guarding. A `:key` is one
attribute, is the idiomatic Vue answer to "this child owns state that belongs to the item", and keeps
the component untouched. The handler must bind the tab id at call time
(`cols => updateTab(activeId.value, cols)`) because remounting fires one `update:modelValue` on mount.

### Decision: the section strip is a jump nav of real anchors (D9)

**Choice**: `letra · acordes N · tablatura N · demos N · tareas N/M` rendered as real `<a href="#sec-…">`
links over sections stacked down one scrolling page, with `vue-router`'s `scrollBehavior` handling the
hash. `ErSegmented` is kept for the three places that genuinely switch: the dashboard filter strip, the
tablature tab strip, and `ErChordEditor`'s `guitarra · piano` toggle.

**Alternatives considered**: `ErSegmented` as a section switcher (the original brief); `<button>`s
calling `scrollIntoView`; an `IntersectionObserver`-driven active state on the strip.

**Rationale**: D9, confirmed. The implementation consequence is that real anchors get keyboard
activation, middle-click, "copy link to section" and browser-back for free, where buttons calling
`scrollIntoView` would reimplement the first and lose the rest. The counts are the strip's purpose —
they tell you what the song has before you scroll — so they are rendered from the loaded composition,
not from a separate request. An active-section highlight is deliberately **not** built: the PDF does
not show one, and an `IntersectionObserver` for a decoration the author did not draw is work with no
acceptance criterion.

---

## Data Flow

### Composition page load, member and public-link paths side by side

```
  Browser                 router guard            /api                    deps.py / Mongo
     │                         │                    │                          │
  /c/{ref}  ──────────────────►│                    │                          │
     │               await authReady (one          │                          │
     │               silent refresh at boot)       │                          │
     │                         │                    │                          │
     │   ref is 24-hex?  ──── yes ──► GET /compositions/{ref} ───────────────► │
     │                         │                    │  require(VIEW)           │
     │                         │                    │  resolve_role(uid, doc)  │
     │                         │                    │  404 if role is None     │
     │                         │                    │  batch users lookup for  │
     │                         │                    │    members[] names       │
     │   ◄─── CompositionResponse { …, user_role, members[name,initials] } ────┤
     │                         │                    │                          │
     │   404, or not 24-hex ──► GET /compositions/by-slug/{ref} ─────────────► │
     │                         │   current_user_optional (no 401 if absent)    │
     │                         │   repo filters visibility == "public"          │
     │                         │   resolve_role(uid|None, doc) → user_role      │
     │   ◄─── 200 for anyone with the link; 404 if private or unknown ─────────┤
```

An invited **editor** who opens the public link therefore still receives `user_role: "editor"` and
still sees the save control — the role is resolved against identity, not against which endpoint was
used to arrive.

### Saving a section (unchanged routes, corrected client)

```
  CompositionDetailView                 api/compositions.ts              /api
       │  dirty flag per section              │                           │
       │  "Guardar cambios" ─────────────────►│                           │
       │                         updateChords(id, ChordsSection) ───────► PUT /{id}/chords
       │                         updateTablature(id, {tabs}) ──────────► PUT /{id}/tablature
       │                         updateLyrics(id, {content}) ──────────► PUT /{id}/lyrics
       │                         updateTodos(id, TodoItem[]) ──────────► PUT /{id}/todos
       │                                      │                require(EDIT) on each
       │                                      │                403 for a viewer regardless
       │                                      │                of what the UI rendered
       │  ◄──── per-section result; save state → "guardado" ─────────────┤
```

Four typed functions instead of one `updateSection(id, type, {content})` means the next drift between
these shapes is a `vue-tsc` error in `npm run build`, not a 404 discovered by a band member.

### Chord assignment — two input paths, one write

```
   palette chip (ErButton)                    syllable target (<button data-chord-target>)
        │                                                     │
   pointerdown ──► setPointerCapture, ghost follows pointer    │
        │          pointermove ──► elementFromPoint(x,y)       │
        │                          .closest('[data-chord-target]')
        │                          → highlight (live bounds)   │
        │          pointerup ─────────────────────────────────►│
        │                                                      │
   Enter/Space ──► armed = chord (aria-pressed, aria-live)     │
        │          Escape ──► disarm                           │
        │          Enter/Space on target ─────────────────────►│
        │                                                      ▼
        └──────────────────────────────► setChordAt(content, {line, offset}, chord | null)
                                                     │   core/lyrics.ts — pure
                                                     ▼
                                          lyrics.content (bracket markup)
                                                     │
                                          parseLine() / ErLyricsViewer — unchanged read path
```

### Dashboard load

```
  GET /api/compositions ──► list_by_user (one query, full documents already)
                              │
                              ├─ metadata: key, bpm, time_signature, style_tags, status
                              ├─ counts computed in the router from the same document:
                              │    chords.entries | tablature.tabs | demos | todos done/total
                              └─ chord_names: first 4 of chords.entries[].name
  ◄── CompositionListItem[]   no extra query, no member resolution on this path
```

---

## Interfaces / Contracts

Shapes and signatures. No implementation.

### Backend — `app/schemas/compositions.py`

```python
# ── Tablature (D1, as approved) ───────────────────────────────────────────
TabColumn = Union[List[str], Literal["|"]]       # six fret/technique strings, or a barline

class TabEntry(BaseModel):
    id: str                                       # client-generated, unique within the composition
    title: str = Field(..., min_length=1, max_length=80)
    strings: int = 6
    columns: List[TabColumn] = []

class TablatureSection(BaseModel):
    tabs: List[TabEntry] = []

# ── Composition metadata (D6) ─────────────────────────────────────────────
class SectionsEnabled(BaseModel):
    chords: bool = True
    tablature: bool = False
    lyrics: bool = True
    demos: bool = True
    todos: bool = True

STATUS = Literal["idea", "in_progress", "ready"]

# added to CreateCompositionRequest (all optional), UpdateCompositionRequest (all optional),
# CompositionResponse and CompositionListItem:
#   key:            Optional[str]        max_length=8      e.g. "Am", "F#", "Bb"      None = "Sin definir"
#   bpm:            Optional[int]        ge=20, le=300
#   time_signature: Optional[str]        pattern=r"^\d{1,2}/\d{1,2}$"                 e.g. "4/4", "6/8"
#   style_tags:     List[str] = []       max_length=6 items, each 1..24 chars, trimmed, de-duplicated
#   status:         STATUS = "idea"
#   sections_enabled: SectionsEnabled = SectionsEnabled()

# ── Member identity (D8) ──────────────────────────────────────────────────
class MemberItem(BaseModel):            # on CompositionResponse — NO email
    user_id: str
    role: str = "editor"                # "editor" | "viewer"
    display_name: Optional[str] = None  # resolved; None if the user record is missing
    initials: Optional[str] = None      # derived from display_name, 1–2 uppercase chars

class MemberDetail(BaseModel):          # GET /{id}/members only — owner-gated
    user_id: Optional[str] = None       # None for a pending invitation
    invite_id: Optional[str] = None     # set only for a pending invitation
    display_name: Optional[str] = None
    email: Optional[str] = None
    initials: Optional[str] = None
    role: str                           # "owner" | "editor" | "viewer"
    pending: bool = False

# ── Response additions ────────────────────────────────────────────────────
# CompositionResponse.user_role: Optional[Literal["owner","editor","viewer"]] = None
# CompositionListItem gains the six metadata fields plus:
#   chord_names: List[str] = []         # first 4 of chords.entries[].name
#   counts: CompositionCounts           # { chords, tabs, demos, todos_done, todos_total }

# ── Invite role (D8) ──────────────────────────────────────────────────────
# CreateInviteRequest.role: str = Field("editor", pattern="^(editor|viewer)$")
```

Stored document delta — **this is the full Mongo schema change in this design**, under AGENTS.md rule 1
and approved as D1 + D6:

```json
{
  "tablature": { "tabs": [ { "id": "t1", "title": "Riff intro", "strings": 6,
                            "columns": [ ["","","","2","",""], "|", ["0","","","","",""] ] } ] },

  "key": "Am",
  "bpm": 72,
  "time_signature": "4/4",
  "style_tags": ["balada", "bossa"],
  "status": "in_progress",
  "sections_enabled": { "chords": true, "tablature": true,
                        "lyrics": true, "demos": true, "todos": true }
}
```

No new collection. No new index — `status` and `key` are filtered client-side over a list the user
already owns, and adding indexes for a band's catalogue would spend Atlas M0 storage on a sort that
runs over tens of documents. No field is required: `create_composition` writes defaults, and every
metadata field is nullable so "Lo demás lo puedes completar después" is literally true.

### Backend — routers

| Route | Change | Authorization |
|---|---|---|
| `GET/PUT /api/compositions/{id}/tablature` | body/response adopt `TablatureSection { tabs }` | unchanged (`VIEW` / `EDIT`) |
| `POST /api/compositions` | accepts the six metadata fields | unchanged |
| `PATCH /api/compositions/{id}` | accepts the six metadata fields | unchanged (`EDIT`) |
| `GET /api/compositions` | returns metadata + counts + `chord_names` | unchanged |
| `GET /api/compositions/{id}` | returns `user_role` + resolved `members[]` | unchanged (`VIEW`) |
| `GET /api/compositions/by-slug/{slug}` | gains `current_user_optional`, returns `user_role` | **still anonymous-readable** |
| `GET /api/compositions/{id}/members` | **new** — `List[MemberDetail]` incl. pending invites | `require(Action.MANAGE_SHARING)` |
| `POST /api/compositions/{id}/invites` | `role` accepts `viewer` | unchanged (`MANAGE_SHARING`) |

`_to_response(doc, role=None)` gains a second parameter. Its four current call sites supply it:
`get_composition` and `update_composition` from `auth.role`; `create_composition` from `Role.OWNER`;
`get_by_slug` by calling `resolve_role(user_id, doc)` with the optional identity. `app/routers/sharing.py`
imports the same helper and passes `auth.role`.

`app/db/repositories/compositions.py` — **no change**. `update_section`'s generic `$set` already
accepts the new tablature value, `update_title` is joined by a sibling `update_metadata` only if the
router cannot express the metadata patch through the existing path; preferred form is extending
`update_title` into `update_fields(composition_id, **fields)` with an allow-list, keeping one
`find_one_and_update` rather than growing a method per field.

### Frontend — `frontend/src/api/compositions.ts` (rewritten)

```ts
export type Visibility = 'public' | 'private'
export type CompositionStatus = 'idea' | 'in_progress' | 'ready'
export type UserRole = 'owner' | 'editor' | 'viewer'
export type TabColumn = string[] | '|'

export interface TabEntry   { id: string; title: string; strings: number; columns: TabColumn[] }
export interface TablatureSection { tabs: TabEntry[] }
export interface ChordEntry { bar: number; notes: number[]; name: string }
export interface ChordsSection { instrument: string; entries: ChordEntry[] }
export interface LyricsSection { content: string }
export interface TodoItem   { text: string; done: boolean }
export interface MemberItem { user_id: string; role: 'editor' | 'viewer'
                              display_name?: string | null; initials?: string | null }
export interface SectionsEnabled { chords: boolean; tablature: boolean
                                   lyrics: boolean; demos: boolean; todos: boolean }

export interface CompositionResponse {
  id: string; owner_id: string; title: string
  visibility: Visibility
  share_slug?: string | null
  key?: string | null; bpm?: number | null; time_signature?: string | null
  style_tags: string[]; status: CompositionStatus; sections_enabled: SectionsEnabled
  chords?: ChordsSection | null
  tablature?: TablatureSection | null
  lyrics?: LyricsSection | null
  todos: TodoItem[]
  demos: DemoItem[]
  members: MemberItem[]
  user_role?: UserRole | null
  created_at: string; updated_at: string
}

// updateSection() is deleted. Four typed replacements:
updateChords   (id: string, body: ChordsSection):    Promise<ChordsSection>
updateTablature(id: string, body: TablatureSection): Promise<TablatureSection>
updateLyrics   (id: string, body: LyricsSection):    Promise<LyricsSection>
updateTodos    (id: string, body: TodoItem[]):       Promise<TodoItem[]>
```

Three deletions that matter as much as the additions: `slug`, `is_public` and
`sections: Record<string, any>` are removed outright rather than aliased, so every consumer of a
phantom field becomes a compile error instead of a silent `undefined`. `CompositionsView.vue`'s
`c.is_public ? 'Pública' : 'Privada'` and `CompositionDetailView.vue`'s four
`composition.sections?.…` reads are precisely those errors.

### Frontend — `frontend/src/api/sharing.ts` (two defects found while reading, fixed in the same slice)

```ts
// today: body { is_public }            backend reads UpdateVisibilityRequest { visibility }
setVisibility(id: string, visibility: Visibility): Promise<CompositionResponse>

// today: POST with no body at all      CreateInviteRequest is a required body → 422
createInvite(id: string, body: { invited_email?: string
                                 role: 'editor' | 'viewer' }): Promise<InviteResponse>

// InviteResponse: drop `created_at` and `token` (never returned); keep `invite_url`,
// `invited_email`, `role`, `expires_at`, `used_at`
listMembers(id: string): Promise<MemberDetail[]>     // new, owner-gated
```

`SharingModal.vue` currently builds its invite URL from `res.token`, which the backend never sends; it
reads `res.invite_url`, which it does. Both are the same class of defect as `updateSection` and are
cheapest to fix while the contract is being regenerated.

### Frontend — `frontend/src/design-system/core/lyrics.ts` (addition; `parseLine` untouched)

```ts
export interface ChordMark { offset: number; chord: string }   // offset into the plain text

/** Split a raw markup line into its visible text and the chord marks over it. */
export function decomposeLine(line: string): { text: string; marks: ChordMark[] }

/** Inverse of decomposeLine. compose(decompose(x)) === x for every x. */
export function composeLine(text: string, marks: ChordMark[]): string

/**
 * The single write path. Both the pointer-drag and the keyboard path call this and nothing else.
 *   chord: string → insert, or replace an existing mark at that exact offset
 *   chord: null   → remove the mark at that offset (no-op when there is none)
 * Total: an out-of-range line or offset returns `content` unchanged rather than throwing.
 * Preserves every other line and the trailing-newline shape byte-for-byte.
 */
export function setChordAt(
  content: string,
  target: { line: number; offset: number },
  chord: string | null,
): string
```

Invariants the unit tests assert directly: `compose ∘ decompose === identity`; two marks can never
share an offset (insert at an occupied offset replaces); `setChordAt` output is independent of input
path; a `# Coro` section line and an empty line are safe inputs; `parseLine()` of any `setChordAt`
output segments exactly as it did before the edit for every untouched segment.

### Frontend — `frontend/src/design-system/core/tab.ts` (addition; `tabToText` untouched)

```ts
export interface TabEntry { id: string; title: string; strings: number; columns: TabColumn[] }
export function newTabId(): string            // crypto.randomUUID() with a counter fallback
export function newTabEntry(index: number): TabEntry   // title "Tablatura {index+1}", blankTab(16)
```

---

## File Changes

### Backend

| File | Action | Description |
|---|---|---|
| `app/schemas/compositions.py` | Modify | `TabColumn`, `TabEntry`, `TablatureSection { tabs }`; six metadata fields on create/update/response/list; `MemberItem` + `display_name`/`initials`; new `MemberDetail`, `CompositionCounts`, `SectionsEnabled`; `user_role` on `CompositionResponse`; invite `role` pattern widened to `^(editor\|viewer)$` |
| `app/routers/compositions.py` | Modify | `_to_response(doc, role)`; metadata on create/patch; counts + `chord_names` on the list; `get_by_slug` gains `current_user_optional` and resolves its own role; batched member-name resolution |
| `app/routers/sections.py` | Modify | `/tablature` GET/PUT adopt the new section shape — body/response types only, handler logic unchanged |
| `app/routers/sharing.py` | Modify | New `GET /{id}/members` returning `MemberDetail[]` incl. pending invites; `_to_response` call sites pass `auth.role` |
| `app/services/composition_service.py` | Modify | `update_composition` accepts the metadata field set; `create_composition` persists metadata defaults |
| `app/services/sharing_service.py` | Modify | Member-detail assembly: batch `users` lookup + unredeemed, unexpired invitations for the composition |
| `app/db/repositories/compositions.py` | Modify (small) | `update_title` generalised to `update_fields(id, **allow-listed fields)`; no new method per field; `create_composition` writes metadata defaults |
| `app/db/repositories/users.py` | Modify | `get_many_by_ids(ids) -> List[dict]` — one `$in` query for member-name resolution |
| `app/core/permissions.py` | **Unchanged** | `resolve_role` already maps a `viewer` member and `_PERMISSIONS[VIEWER]` is already `{VIEW}` — verified by reading, not assumed |
| `app/deps.py` | **Unchanged** | `require(action)` already covers every new route by prefix |
| `tests/test_sections_router.py` | Modify | Multi-tab round trip replaces the single-string tablature case |
| `tests/test_compositions_router.py` | Modify | `user_role`, metadata validation, list counts |
| `tests/test_sharing_router.py` | Modify | Viewer-role invite, member projection authorization, email non-exposure |
| `vercel.json` | **Unchanged** | The SPA catch-all rewrite already exists and already ranks below `/api/(.*)` |

### Frontend — plumbing

| File | Action | Description |
|---|---|---|
| `frontend/package.json` | Modify | `+ vue-router ^4` — the only new runtime dependency in this change |
| `frontend/src/main.ts` | Modify | Third stylesheet import `./styles/layout.css`; `app.use(router)`; start the `authReady` bootstrap refresh |
| `frontend/src/router/index.ts` | **New** | Route table, guard, `scrollBehavior` |
| `frontend/src/router/authReady.ts` | **New** | The single shared bootstrap-refresh promise |
| `frontend/src/styles/layout.css` | **New** | Every page-shell, grid, modal and hero class; token-only (see the next section) |
| `frontend/src/api/compositions.ts` | **Rewritten** | Real flat types; four typed section functions |
| `frontend/src/api/sharing.ts` | Modify | `setVisibility` body, `createInvite` body, `InviteResponse` shape, `listMembers` |
| `frontend/src/shared/AppModal.vue` | **New** | Teleported overlay: backdrop, centering, focus trap, Escape, scroll lock |
| `frontend/src/shared/useFocusTrap.ts` | **New** | Live focusable query, Tab cycling, focus restore |
| `frontend/src/App.vue` | **Rewritten** | Becomes `<RouterView>` + theme attribute only; the `ref` view switch, the nav `ErSegmented` and four inline `style` attributes are deleted |

### Frontend — pages

| File | Action | Description |
|---|---|---|
| `frontend/src/features/compositions/DashboardView.vue` | **New** (replaces `CompositionsView.vue`'s role) | Top app bar, hero headline, `ErSegmented` filter strip, result count, card grid, dashed new-song card |
| `frontend/src/features/compositions/CompositionCard.vue` | **New** | Index, status `ErTag`, title, chord-name line, counts line, footer |
| `frontend/src/features/compositions/CompositionsView.vue` | **Delete** | Its sidebar+detail shell becomes the composition page; its list becomes the dashboard |
| `frontend/src/features/compositions/CompositionDetailView.vue` | **Restructured** | Sidebar shell, PDF header, section jump nav, stacked sections; hosts the tablature container and the lyrics editor |
| `frontend/src/features/compositions/CompositionCreateView.vue` | **New** | Full page, PDF page 2 minus the band option; **2 visibility options (D7)** |
| `frontend/src/features/compositions/CompositionCreateModal.vue` | **Delete** | Superseded by the full-page flow |
| `frontend/src/features/compositions/ChordGrid.vue` | **New** | Responsive grid of one `ErChordEditor` per `chords.entries[]`, plus add/remove |
| `frontend/src/features/compositions/TablatureSection.vue` | **New** | Multi-tab container around `ErTabEditor` (see below) |
| `frontend/src/features/compositions/LyricsSection.vue` | **New** | Switches between `ErLyricsViewer` (read) and the chord editor (edit) |
| `frontend/src/features/auth/AuthView.vue` | **Restructured** | Split screen; the CSS-only hero; the mode `ErSegmented` is replaced by routes |
| `frontend/src/features/auth/LoginForm.vue` | Modify | PDF copy, `mostrar` toggle, `router-link` cross-link; **no** Google button, **no** password-reset link (D11) |
| `frontend/src/features/auth/RegisterForm.vue` | Modify | PDF copy; **no** Banda field, **no** Google button, **no** terms links (D11) |
| `frontend/src/features/sharing/SharingModal.vue` | **Restructured** | PDF page 5 via `AppModal`: visibility radio cards, read link + Copiar, permission checklist, invite + role, member list |
| `frontend/src/features/demos/DemosSection.vue` | Modify | Frame only; inline styles removed; `ErDemoPlayer` unchanged |
| `frontend/src/features/demos/DemoUploadModal.vue` | Modify | Wrapped in `AppModal`; inline styles removed |

### Frontend — design system

| File | Action | Description |
|---|---|---|
| `frontend/src/design-system/core/lyrics.ts` | Modify | `decomposeLine`, `composeLine`, `setChordAt`; `parseLine` untouched |
| `frontend/src/design-system/core/tab.ts` | Modify | `TabEntry`, `newTabId`, `newTabEntry`; `tabToText`, `blankTab`, `TECH` untouched |
| `frontend/src/design-system/components/ErLyricsChordEditor.vue` | **New** | Editable surface: chord palette + `<button>` drop targets |
| `frontend/src/design-system/components/ErChordPalette.vue` | **New** | `ErButton` chips from `chords.entries[].name` + the `✕ quitar` sentinel chip |
| `frontend/src/design-system/components/index.ts` | Modify | Barrel exports for the two new components |
| `ErTabEditor`, `ErLyricsViewer`, `ErDemoPlayer`, `ErChordEditor`, `ErTodoList`, `ErSideNav`, `ErSegmented`, `ErButton`, `ErTag` | **Unchanged** | Stated as an acceptance criterion, not an aspiration |
| `erato-design-system/components/bundle.css` | Modify (D4) | `+ .er-drag-ghost`, `+ .er-drop-target` with `.is-armed` / `.is-over`. The **only** mutation of `erato-design-system/` in this change |

### Tests

| File | Action | Description |
|---|---|---|
| `frontend/tests/design-system/lyrics.spec.ts` | Modify | Table-driven `setChordAt` + the compose/decompose round trip |
| `frontend/tests/design-system/tab.spec.ts` | Modify | `newTabEntry`, id uniqueness |
| `frontend/tests/features/tablature-section.spec.ts` | **New** | Add / rename / delete / reorder / switch-remount |
| `frontend/tests/features/lyrics-chord-editor.spec.ts` | **New** | Keyboard path end to end; drag path via synthesised `PointerEvent`s; byte-identity between the two |
| `frontend/tests/styles/layout-css.spec.ts` | **New** | Key-selector disjointness, no literal colors/fonts/radii, every referenced `er-*` resolves |
| `frontend/tests/shared/app-modal.spec.ts` | **New** | Escape, backdrop click, focus trap, focus restore, stacking |
| `frontend/tests/router/guard.spec.ts` | **New** | `authReady` gating, public-route exemptions, `/c/:ref` id-vs-slug resolution |

---

## The Page-Shell Stylesheet

`frontend/src/styles/layout.css`, imported third. Every value is a `var(--token)` reference; the only
literal numbers permitted are structural ones with no token equivalent (grid track counts, `0`, `1fr`,
`100%`, `50%`, `z-index` integers, `1px` hairlines matching `bundle.css`'s own convention).

| Region | Classes it defines | What it does |
|---|---|---|
| App shell | `er-app`, `er-app-main` | Min-height viewport column, background `--bg-100`, main grows |
| Dashboard | `er-topbar`, `er-topbar-brand`, `er-avatar`, `er-dash`, `er-dash-hero`, `er-dash-headline`, `er-filterbar`, `er-dash-count`, `er-comp-grid`, `er-card`, `er-card-head`, `er-card-index`, `er-card-title`, `er-card-chords`, `er-card-counts`, `er-card-foot`, `er-card-new` | Top bar with brand / action / avatar; display-serif headline; filter row; 3-column `repeat(auto-fill, minmax(…, 1fr))` card grid; the dashed "Empieza una canción nueva" card |
| Composition shell | `er-layout`, `er-layout--noside`, `er-sidebar`, `er-sidebar-foot`, `er-main` | `grid-template-columns: 248px 1fr` matching `.er-nav`'s own width; `--noside` collapses to one column for a logged-out public visitor; `er-sidebar-foot` holds the `← todas las composiciones` link that `ErSideNav` does not render |
| Composition page | `er-comp-detail`, `er-crumb`, `er-savestate`, `er-comp-header`, `er-comp-title`, `er-comp-meta`, `er-comp-tags`, `er-avatars`, `er-sectionnav`, `er-section`, `er-section-head`, `er-comp-columns`, `er-comp-column`, `er-role-tag`, `er-save-btn` | Breadcrumb + save state row; display-serif title; metadata chip row; avatar cluster; the underlined jump-nav row; stacked section blocks with scroll-margin for hash landing; the letra/tareas two-column band |
| Create page | `er-createshell`, `er-createbar`, `er-form-card`, `er-field`, `er-field-row`, `er-field-grid`, `er-hint`, `er-usecards`, `er-usecard`, `er-checkbox-label` | Minimal bar with brand + Cancelar; centered form card; the three-up Tonalidad/Tempo/Compás row; the five include-toggle cards as real `<button aria-pressed>` |
| Auth | `er-auth-split`, `er-auth-hero`, `er-auth-bars`, `er-auth-bar`, `er-auth-pill`, `er-auth-rules`, `er-auth-wordmark`, `er-auth-tagline`, `er-auth-pane`, `er-auth-view`, `er-auth-header`, `er-auth-form`, `er-auth-error`, `er-auth-links` | 50/50 grid; the hero drawn with `--amber`, `--key-ivory`, `--wine`, `--ember` bars at `--radius-md`/`--radius-lg`, the `--moss` pill at `--radius-pill`, `repeating-linear-gradient` rules in `--line`, and a `radial-gradient` glow using `--lamp` over `--bg-000`. **No image asset, no asset pipeline, no licensing question** |
| Modal | `er-modal-backdrop`, `er-modal`, `er-modal-head`, `er-modal-body`, `er-modal-foot` | `position: fixed; inset: 0; z-index: 60` — above `bundle.css`'s `.er-lyrics--max { z-index: 50 }`, which is the only stacking context in the design system and therefore the number the modal has to clear |
| Sharing | `er-share-cards`, `er-share-card`, `er-share-link`, `er-perm-list`, `er-invite-row`, `er-invites-block`, `er-invite-created`, `er-invites-list`, `er-member`, `er-member-id`, `er-member-role` | Two visibility radio cards (D7); read-link row with Copiar; the mono ✓/✕ permission checklist; member rows with avatar, name/email, role label |
| Editors | `er-tabs-strip`, `er-tab-actions`, `er-chord-grid`, `er-chord-palette`, `er-chord-chip`, `er-lyrics-edit`, `er-lyrics-line` | Horizontally scrollable tab strip; chord-card grid; the palette row with `touch-action: none` on chips so a touch drag does not scroll the page |
| Utility | `er-loading`, `er-empty`, `er-demos-section` | Shared states the features already reference |

**Three tests guard the file**, all in `frontend/tests/styles/layout-css.spec.ts`, reading both
stylesheets from disk as text:

1. **Key-selector disjointness.** For each rule in each file, split the selector list on commas, take
   the rightmost compound of each, extract its `er-*` classes. Assert the two resulting sets intersect
   in nothing. This rejects both an exact duplicate (`.er-panel` redefined) and the subtler
   `.er-modal .er-panel` form that would silently restyle a component's internals, while permitting
   `<div class="er-modal er-panel">` co-styling, which is how layout composes with components.
2. **No literal design values in `layout.css`.** Assert no `#rrggbb`/`#rgb` literal, no `rgb(`/`hsl(`,
   no `font-family` whose value is not a `var(--font-…)`, and no `border-radius` whose value is not a
   `var(--radius-…)`, `0`, or `50%`. This is the mechanical form of AGENTS.md rule 2 and the direct
   mitigation of the proposal's "hardcoded colors creep in to hit a shade the tokens do not have" risk.
3. **Every referenced `er-*` resolves.** Scan every `.vue` and `.ts` file under `frontend/src/` for
   complete literal `er-[a-z0-9-]+` tokens and assert each is defined by `bundle.css` or `layout.css`.
   The scanner collects literals only; dynamically composed names need an explicit, documented
   allowlist in the test file, which currently holds exactly three entries: `er-btn--*` and `er-tag--*`
   (built by template literal from a prop) and `er-lyrics--max` (toggled by `useAutoScroll`).

   One known exception belongs in that allowlist with its reason recorded: **`er-btn--quiet` has no
   rule in `bundle.css`**, and `ErButton`'s default variant is `quiet`. Verified against the reference —
   `erato-design-system/components/bundle.js:74` emits `"er-btn--" + variant` for the React original
   too, so an inert `er-btn--quiet` class is reference-faithful behaviour, not a port defect, and the
   quiet look is the base `.er-btn` rule. Adding a `.er-btn--quiet` rule to `layout.css` would restyle a
   component class (rejected by test 1); adding it to `bundle.css` would be an unapproved design-system
   change under AGENTS.md rule 2. Listing it makes the exception visible instead of silent.

---

## Page Designs

### Dashboard — `/`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ● Erato                                      [+ Nueva composición] (MK)  │  er-topbar
├──────────────────────────────────────────────────────────────────────────┤
│ // LA BANDA                                                               │
│ Todo lo que la banda escribió.                                            │  er-dash-hero
│ Acordes, tablaturas, letras y demos de cada canción, en un mismo lugar.    │
│                                                                           │
│ [ todas | en progreso | listas | ideas ]        6 composiciones · recientes│  ErSegmented
│                                                                           │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐                                  │
│ │ 00  ●en  │  │ 01 ●lista│  │ 02 ●en   │   ← CompositionCard               │  er-comp-grid
│ │ Noche…   │  │ Humo azul│  │ La últi… │                                   │
│ │ Am7·D9·… │  │ Dm9·G13… │  │ G·Em7·…  │                                   │
│ │ 8 acordes│  │ 6 acordes│  │ 5 acordes│                                   │
│ │ hace 2 d │  │ hace 1 s │  │ Am·72bpm │                                   │
│ └──────────┘  └──────────┘  └──────────┘                                  │
│ ┌ ─ ─ ─ ─ ┐                                                                │
│ │    +    │  Empieza una canción nueva  → router-link /new                 │  er-card-new
│ └ ─ ─ ─ ─ ┘                                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

The filter strip **is** an `ErSegmented` — PDF page 1 draws it as a bordered group with a highlighted
active option, which is exactly that component. (D9's "not a switcher" ruling applies to the
*composition page's section strip*, which is a different control.) Filtering is client-side over the
already-loaded list: `todas` / `in_progress` / `ready` / `idea`.

`CompositionCard` is a `router-link` to `/c/{id}` wrapping: the zero-padded index (`pad2` from
`core/format`, the same helper `ErSideNav` uses), a status `ErTag` with `dot` — `in_progress` → `amber`,
`ready` → `moss`, `idea` → neutral, matching the PDF's amber/moss/plain pills — the display-serif title,
the chord-name line from `chord_names`, the counts line from `counts`, and a footer with the relative
`updated_at` on the left and `key · bpm` on the right.

**Two PDF affordances are deliberately not built.** The search box is excluded by D11. The card footer's
actor name ("Ana editó hace 2 días") needs a `last_edited_by` field that D6 does **not** include, so the
footer renders `editada hace 2 días` from `updated_at` alone — the time is true, the attribution would
be invented. The `orden: recientes` label is rendered as static text describing the single ordering the
backend actually applies (`sort("updated_at", -1)`), not as a dropdown with one option.

### Composition page — `/c/:ref`

```
┌────────────┬─────────────────────────────────────────────────────────────┐
│ ● Erato    │ composiciones / noche de otoño            ● guardado         │ er-crumb
│  cancionero│ // COMPOSICIÓN 00                                            │
│            │ Noche de otoño                                               │ er-comp-title
│ // COMPOS. │ ●en progreso  [Am · 72 bpm · 4/4]  [balada][bossa]           │ er-comp-meta
│ 00 Noche Am│                               (AN)(TO)(LE)  [⇱ Compartir]    │ er-avatars
│ 01 Humo  Dm│─────────────────────────────────────────────────────────────│
│ 02 La ú.  G│ letra · acordes 6 · tablatura 1 · demos 3 · tareas 2/4       │ er-sectionnav
│ 03 Farol Eb│─────────────────────────────────────────────────────────────│
│ 04 Vals   F│ // LETRA                      │ // TAREAS                    │ er-comp-columns
│ 05 Sin t.  │ [ErLyricsViewer / editor]     │ [ErTodoList]                 │
│            │                                                              │
│ ← todas las│ // ACORDES DE LA CANCIÓN            [+ Agregar acorde]        │
│  composici.│ [ErChordEditor][ErChordEditor][ErChordEditor]                 │ er-chord-grid
│            │ // TABLATURA   [Riff intro|Solo]  [+][✎][🗑][◀▶]              │ er-tabs-strip
│  er-sidebar│ [ErTabEditor]                                                 │
│            │ // DEMOS                            [+ Subir audio]           │
│            │ [ErDemoPlayer]                                                │
└────────────┴─────────────────────────────────────────────────────────────┘
```

The sidebar is `ErSideNav` **used as it is** — `er-nav*` is fully styled in `bundle.css` and its
248px width is what `er-layout`'s grid track matches. `SideNavItem.meta` carries the composition's
`key`, matching the PDF's per-row key letter (today it carries a phantom `is_public`). The
`← todas las composiciones` link sits in `er-sidebar-foot`, below the component, because adding a slot
to `ErSideNav` would modify a component the proposal lists as Unchanged.

For an **unauthenticated visitor on a public link** there is no composition list to show, so the shell
renders `er-layout er-layout--noside` and the main column spans full width. Sections render read-only,
and the `Compartir` button is hidden (`user_role !== 'owner'`).

The section nav is five `<a href="#sec-…">` anchors with counts derived client-side from the loaded
composition — `chords.entries.length`, `tablature.tabs.length`, `demos.length`, and
`todos.filter(done).length / todos.length`. `vue-router`'s `scrollBehavior` resolves the hash
(`{ el: to.hash, behavior: 'smooth' }`), and each `er-section` carries `scroll-margin-top` so a landed
section is not hidden under the header. Sections whose `sections_enabled` flag is false are omitted from
both the nav and the page.

The save state next to the breadcrumb is derived from a per-section dirty flag:
`sin guardar` → `guardando…` → `guardado`. The explicit `Guardar cambios` control is kept — the whole
composition is held in memory behind one save, which is the model the whole-array `PUT` decision
depends on. The PDF's `…` overflow menu is **not** built: no menu contents are specified anywhere, and
the one real candidate (delete composition) has no approved placement. It is listed as an open
question rather than invented.

### New composition — `/new`

Full page, per PDF page 2, in `er-createshell`: a minimal bar with the brand and `Cancelar`, the
`// NUEVA COMPOSICIÓN` eyebrow, the display-serif headline, and a centered `er-form-card` holding —
Título (`er-input`); a three-up `er-field-grid` of Tonalidad (`er-select`, default "Sin definir"),
Tempo (number + `bpm` suffix) and Compás (`er-select`); Estilo (comma-separated text, hinted
"Se muestran como tags en la lista"); the five `er-usecard` include toggles (real `<button
aria-pressed>`, label + `incluida` / `no por ahora`); **Quién la ve** as an `ErSegmented` with exactly
**two** options — `con enlace` → `public`, `solo yo` → `private` — per **D7**; then Cancelar /
Crear composición.

The PDF's third option `la banda` is **not rendered**. D7 resolved the mockup's self-contradiction in
favour of the two values the backend has and the Compartir modal already offers; a third category would
need a band entity, which D11 defers. The hint line under the control states what each choice actually
does, consistent with the Compartir modal's wording so the same decision reads the same in both places.

On submit: `POST /compositions` with title, visibility, metadata and `sections_enabled`, then
`router.replace('/c/' + created.id)` — `replace`, not `push`, so the browser back button returns to the
dashboard rather than to a form that has already been submitted.

### Auth — `/login` and `/register`

```
┌───────────────────────────────┬──────────────────────────────────────────┐
│  ▓▓▓   ░░░                    │  // INICIAR SESIÓN                        │
│  ▓▓▓  ▓▓▓▓  ▓▓▓▓              │  Qué bueno verte de nuevo.                │
│  ▓▓▓  ▓▓▓▓  ▓▓▓▓              │  La banda dejó comentarios en tus demos.  │
│  ═══  ════  ════   ← rules    │                                           │
│  ▓▓▓  ▓▓▓▓  ▓▓▓▓              │  Correo    [ ................... ]        │
│   ▬  ← moss pill              │  Contraseña[ .......... ]  mostrar        │
│                               │  [        Entrar         ]                │
│  Erato                        │                                           │
│  Las canciones de la banda,   │  ¿Primera vez en Erato? Crea tu cuenta    │
│  bajo luz cálida.             │  ¿Te pasaron un enlace? Puedes abrirlo    │
│  er-auth-hero (CSS only)      │  sin cuenta, en modo solo lectura.        │
└───────────────────────────────┴──────────────────────────────────────────┘
```

The hero is `background`, `border-radius` and `radial-gradient` over existing custom properties:
`--amber`, `--key-ivory` for the cream block, `--wine` for the pink, `--ember` for the orange, `--moss`
for the pill, `--line` for the rules via `repeating-linear-gradient`, and `--lamp` for the glow over
`--bg-000`. It therefore rethemes to Matiné for free and issues **no image request**, which is a stated
acceptance criterion and is directly observable in the network tab.

Login and register are two routes sharing the hero, not one view with an `ErSegmented` mode toggle;
they cross-link with `router-link`. Removed per **D11**: `Continuar con Google` and its `o` divider
(the divider exists only to separate it), `¿La olvidaste?`, the register form's optional `Banda` field,
and the `términos`/`política de privacidad` line. Kept because each is real and needs no backend: the
`mostrar` password toggle, the cross-links, and the footer note about opening a shared link without an
account — which is a true statement about the system, not a control.

### Compartir modal — PDF page 5

Rendered through `AppModal`: the `// COMPARTIR` eyebrow and the composition title; **Quién puede
abrirla** as two `er-share-card` radio cards (`Con enlace` / `Privada`, D7) with the PDF's descriptive
copy; **Enlace de lectura** as a read-only `er-input` holding `{origin}/c/{share_slug}` plus a `Copiar`
button, shown only when the composition is public; the mono permission checklist (`✓ ver letra y
acordes · ✓ escuchar demos · ✕ editar sin cuenta · ✕ comentar sin cuenta`) rendered from the actual
permission matrix rather than hardcoded strings, so it cannot drift from `_PERMISSIONS`; **Invitar a
editar** as email + role `er-select` (`puede editar` / `solo ver`) + Invitar; and the member list from
`GET /{id}/members` — avatar initials, name or email, role label, and `invitación pendiente` for
unredeemed invites.

The whole modal is owner-only (`user_role === 'owner'`), which is what makes the email-bearing endpoint
safe to call from it.

---

## Component Designs

### `TablatureSection.vue` — the multi-tab container

```
┌─ // TABLATURA ────────────────────────────────────────────────────────────┐
│ [ Riff intro │ Solo │ Puente ]   [+ Agregar] [✎ Renombrar] [🗑] [◀] [▶]   │  ErSegmented + ErButtons
├───────────────────────────────────────────────────────────────────────────┤
│ <ErTabEditor :key="activeId" :model-value="activeTab.columns" />           │
│   e|---------5-----  … (unchanged component, keyboard legend included)     │
└───────────────────────────────────────────────────────────────────────────┘
```

| Operation | Behaviour |
|---|---|
| Switch | `ErSegmented` sets `activeId`; the `:key` remounts `ErTabEditor` with that tab's columns |
| Add | `newTabEntry(tabs.length)` appended, becomes active, focus moves to the grid |
| Rename | The strip swaps for an `er-input` + Guardar / Cancelar inline; no modal for a one-field edit |
| Delete | Two-step inline confirm (`🗑` → `¿Borrar? Sí / No`) rather than `window.confirm`; deleting the last tab leaves `tabs: []` and the section shows its empty state |
| Reorder | `◀ ▶` `er-iconbtn`s move the active tab one position. Drag-reorder was rejected: a second pointer-drag implementation for a rare operation, and arrow buttons are keyboard-accessible by construction |
| Save | The parent's single `Guardar cambios` sends the whole `{ tabs }` through `updateTablature` |

Read tolerance: a response whose `tablature` lacks `tabs` is normalised to `{ tabs: [] }` on load. Per
D1 no such data exists, so this is defensive normalisation, not a migration path.

### `ErLyricsChordEditor.vue` + `ErChordPalette.vue`

The editor renders the same structure the viewer does — `er-lyric`, `er-seg-lyr`, `er-seg-chord` — but
each syllable segment is a real `<button data-chord-target data-line data-offset>` instead of a span,
and the autoscroll/maximize toolbar is absent. `ErLyricsViewer.vue` and `parseLine()` are untouched;
`LyricsSection.vue` chooses between them on `canEdit`.

The palette is `ErButton` chips built from `chords.entries[].name` (de-duplicated, order preserved)
plus a trailing `✕ quitar` chip that arms the removal sentinel. `ErTag` is deliberately **not** used:
it renders a `<span>`, and giving a span a click handler would fail AGENTS.md's "controles reales"
requirement and lose the design-system focus ring.

| Path | Sequence |
|---|---|
| Pointer | `pointerdown` on a chip → `setPointerCapture(pointerId)`, render `er-drag-ghost` at the pointer → `pointermove` updates the ghost and runs `elementFromPoint(x, y).closest('[data-chord-target]')`, toggling `er-drop-target.is-over` → `pointerup` commits on the target under the pointer, releases capture, clears the ghost → `pointercancel` clears without committing |
| Keyboard | `Enter`/`Space` on a chip arms it (`aria-pressed="true"`, announced through an `aria-live="polite"` region) → `Tab`/arrows move through the targets, each showing `er-drop-target.is-armed` → `Enter`/`Space` on a target commits → `Escape` disarms |
| Shared | Both converge on `setChordAt(content, { line, offset }, chord \| null)` and nothing else writes the string |

`touch-action: none` on `er-chord-chip` prevents a touch drag from scrolling the page instead of
dragging. Hit-testing is re-evaluated on every move rather than cached at `pointerdown`, because the
lyrics surface scrolls.

Two token-derived state classes go into `erato-design-system/components/bundle.css` under the approved
**D4**: `.er-drag-ghost` (the floating chip following the pointer) and `.er-drop-target` with `.is-armed`
and `.is-over`. These are states, not components, and they are the only change to `erato-design-system/`
anywhere in this design.

### `AppModal.vue`

| Concern | Design |
|---|---|
| Stacking | `<Teleport to="body">`, `er-modal-backdrop` at `position: fixed; inset: 0; z-index: 60` — above `bundle.css`'s `.er-lyrics--max { z-index: 50 }`, the only other stacking context in the design system |
| Surface | `<div class="er-modal er-panel" role="dialog" aria-modal="true" :aria-labelledby>` — two classes on one element, which is why the key-selector rule permits it |
| Dismiss | Backdrop `@click.self`, and `Escape` on the dialog root (focus is trapped inside, so a document listener is unnecessary) |
| Focus trap | `useFocusTrap` records `document.activeElement` on mount, focuses the first focusable (or the dialog at `tabindex="-1"`), cycles `Tab`/`Shift+Tab` over a **live** query of focusables, and restores focus on unmount. The query is live because modal content loads asynchronously — `SharingModal` fetches its member list after mount |
| Scroll lock | `document.body` overflow hidden, guarded by a module-level open-count so a future nested modal cannot unlock early |

`CompositionCreateModal.vue` does **not** adopt it — it is deleted and replaced by the full-page
`/new` flow per the PDF. `SharingModal` and `DemoUploadModal` do.

---

## Routing

`frontend/src/router/index.ts`, `createWebHistory`.

| Path | Component | `meta.public` | Notes |
|---|---|---|---|
| `/` | `DashboardView` | no | Redirects to `/login` only after `authReady` resolves |
| `/new` | `CompositionCreateView` | no | |
| `/c/:ref` | `CompositionDetailView` | **yes** | id-or-slug; a public composition renders for an anonymous visitor |
| `/login` | `AuthView` (login) | yes | Already-authenticated → `/` |
| `/register` | `AuthView` (register) | yes | Already-authenticated → `/` |
| `/invite/:token` | `InviteRedeemView` | yes | See below |
| `/:pathMatch(.*)*` | `NotFoundView` | yes | |

```
  beforeEach(to):
    await authReady                       ← one shared bootstrap POST /api/auth/refresh
    if (to.meta.public) → allow
    if (isAuthenticated) → allow
    → redirect '/login' with { query: { next: to.fullPath } }
```

`scrollBehavior(to, from, saved)` returns `saved` on a back/forward navigation,
`{ el: to.hash, behavior: 'smooth' }` when a hash is present (the section jump nav), and
`{ top: 0 }` otherwise.

`/invite/:token` is included because `SharingModal` already mints
`${window.location.origin}/invite/${token}` and `vercel.json`'s catch-all will now serve `index.html`
for it — without a route, an invite link would silently render the dashboard and consume nothing. The
minimal behaviour matches the base design's already-approved flow: if authenticated, `POST
/auth/redeem-invite` and `router.replace('/c/' + composition_id)`; if not, stash the token and redirect
to `/login`, replaying the redemption after sign-in. This is listed in Open Questions as a small scope
addition rather than assumed silently.

**Deploy shape**: unchanged. `vercel.json` already rewrites `/(.*)` → `/index.html` below
`/api/(.*)` → `api/index.py`, Vercel applies rewrites after static-file matching so hashed assets still
serve, and the catch-all is exactly what a history-mode SPA needs. No new function, no new cron, no new
build step — `erato/constraints/free-hosting` is untouched, and `vue-router` ships inside the existing
static bundle.

---

## Testing Strategy

Strict TDD is enabled for this change. Every row below is a RED test written before its production
change.

| Layer | What to test | Approach |
|---|---|---|
| Unit (backend) | `TabEntry` validation: empty title rejected, `columns` accepts a mixed `List[str] \| "\|"` array, `strings` defaults to 6 | pytest over the Pydantic model |
| Unit (backend) | Metadata validation: `bpm` out of 20–300 rejected, `time_signature` pattern, `style_tags` cap and trimming, `status` enum, every field omittable | pytest |
| Unit (backend) | `resolve_role` with a `viewer` member on a **private** composition → `Role.VIEWER`, can `view`, cannot `edit` | pytest, pure — extends the existing matrix test |
| Integration (backend) | Tablature round trip: `PUT` three named tabs → `GET` returns all three with titles, string counts and columns intact | `httpx.ASGITransport` + the compose Mongo |
| Integration (backend) | Tablature reorder and delete persist through a whole-array `PUT` | same |
| Integration (backend) | `user_role` is `owner`/`editor`/`viewer`/absent for the four caller classes, including anonymous-via-slug | same |
| Integration (backend) | A `viewer` member receives `403` on every section `PUT` **regardless of `user_role`** — the UI hint does not relax enforcement | same |
| Integration (backend) | `GET /{id}/members` returns `403` to an editor and `200` with emails + pending invites to the owner | same |
| Integration (backend) | `CompositionResponse` **never** contains an email, including on the anonymous by-slug path | assert on the serialized payload keys |
| Integration (backend) | `POST /invites` accepts `role: "viewer"`, rejects `role: "admin"`; redemption grants the invited role | same |
| Integration (backend) | List counts and `chord_names` match the stored document and cost no additional query | same, with a query counter |
| Unit (frontend) | `setChordAt`: insert at 0, insert mid-line, replace an existing mark, remove, out-of-range no-op, multi-line isolation, trailing-newline preservation | Vitest, table-driven |
| Unit (frontend) | `composeLine(decomposeLine(x)) === x` over a fixture set including `# Coro`, empty lines, adjacent marks, and markup with no chords | Vitest |
| Unit (frontend) | `parseLine()` output is unchanged for every untouched segment of a `setChordAt` result | Vitest, cross-checking the untouched read path |
| Unit (frontend) | `newTabId` uniqueness; `newTabEntry` title and blank grid | Vitest |
| Component (frontend) | Tablature container: add, rename, delete, reorder, and **switching tabs shows the switched tab's columns** (the `:key` remount) | Vue Test Utils |
| Component (frontend) | Lyrics editor keyboard path: arm, commit, disarm; the `✕ quitar` sentinel removes | Vue Test Utils + keyboard events |
| Component (frontend) | Lyrics editor drag path via synthesised `PointerEvent`s, asserting **byte-identical** output to the keyboard path for the same target | Vue Test Utils, `elementFromPoint` stubbed to the target |
| Component (frontend) | `AppModal`: Escape closes, backdrop click closes, inner click does not, Tab cycles within, focus restores on close | Vue Test Utils + jsdom |
| Component (frontend) | Save control renders for `owner`/`editor` and not for `viewer`; the public read-only shell drops the sidebar | Vue Test Utils |
| Stylesheet (frontend) | Key-selector disjointness between `layout.css` and `bundle.css` | Vitest, reading both files as text |
| Stylesheet (frontend) | `layout.css` holds no literal color, font family, or radius | Vitest regex assertions |
| Stylesheet (frontend) | Every literal `er-*` referenced under `frontend/src/` resolves, modulo a documented three-entry allowlist | Vitest, source scan |
| Stylesheet (frontend) | No inline `style="…"` attribute remains under `frontend/src/features/` | Vitest, source scan |
| Router (frontend) | The guard waits on `authReady` before redirecting; `/c/:ref` is reachable logged out; `/` is not | Vitest with a memory history |
| Router (frontend) | `/c/:ref` resolves a 24-hex ref by id and falls back to by-slug on `404`; a non-hex ref goes straight to by-slug | Vitest with a mocked client |
| Manual | Both themes on every new screen: focus ring visible, 4.5:1 text contrast, the auth hero recolors for Matiné and issues no image request | Checklist against the PDF's regions and controls |

The acceptance bar for "matches the PDF" is **structural fidelity** — same regions, same controls, same
information per region — not pixel diffing. The PDF is drawn at one desktop width and is not a spec for
every viewport; responsive breakpoints beyond what the component CSS already does are out of scope.

---

## Threat Matrix

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | `requirements.txt`, `CMakeLists.txt`, executable Markdown/MDX, `README.sh` | **N/A** — the change classifies no file as executable and runs no file by extension or content | — | — |
| Git repository selection | `git -C`, relative paths, absolute paths | **N/A** — no VCS operation, no repository or cwd selector anywhere in the change | — | — |
| Commit state | staged, `commit -a`, empty index | **N/A** — no index or worktree interaction | — | — |
| Push state | tracking branch, first push, explicit refspec | **N/A** — no push, no ref resolution | — | — |
| PR commands | explicit `--head`, environment prefix, composed commands | **N/A** — no PR automation and no composed shell command | — | — |

The "routing" this change introduces is **URL routing inside a browser SPA and HTTP routing inside one
ASGI application** — not command routing, not repository-selector routing, and not process integration.
It spawns no subprocess and composes no shell command, so the matrix above is not applicable row by row
rather than partially applicable.

It does introduce three real adversarial surfaces, which are covered by named tests in the strategy
above rather than by this matrix:

1. **Route-parameter interpolation.** `:ref` and `:token` are attacker-controlled and are interpolated
   into API paths. They are encoded with `encodeURIComponent` at the call site, the by-id branch is
   gated behind a strict `^[0-9a-f]{24}$` match, and the backend validates with `ObjectId.is_valid`
   before querying (`compositions.py:72-74`), so a malformed ref produces a `404`, never a query.
2. **Member-identity exposure.** Emails are reachable only through an endpoint mounted with
   `require(Action.MANAGE_SHARING)`, and a test asserts no email appears on `CompositionResponse`,
   including on the anonymous by-slug path.
3. **`user_role` as an authorization hint.** It is advisory UI state. A test asserts a `viewer` is
   rejected with `403` on every section write regardless of what the response's `user_role` said, so
   the hint can never become the enforcement.

---

## Migration / Rollout

**No data migration.** D1 confirms no deployed database and no production data; `create_composition`
writes `"tablature": None` today, so there is nothing holding the old `{strings, content}` shape to
backfill. If a local development document does carry a non-null `tablature.content`, the recommendation
stands from the proposal: reset that local data rather than write an ASCII→columns parser, because
re-parsing rendered ASCII is lossy and a parser written for throwaway data is a permanent maintenance
liability.

**Metadata fields are additive and nullable**, so existing documents read correctly without a backfill:
Pydantic supplies the defaults on read and the fields materialise in Mongo on the first write.

Rollout follows the proposal's nine-slice plan, with two corrections this design produces:

| # | Slice | Correction from this design |
|---|---|---|
| 0 | API contract reconciliation + tests | **Widened**: also fixes `api/sharing.ts`'s `setVisibility` body, `createInvite`'s missing body, and `InviteResponse`'s phantom `token`/`created_at` |
| 1 | `layout.css` + inline-style removal + modal classes + the disjointness test | Adds `AppModal.vue` / `useFocusTrap.ts`, since the classes alone do not make a modal |
| 2 | Routing: `vue-router`, the four shells, the Vercel rewrite | **Narrowed**: `vercel.json` needs no change. Adds `authReady` and `/invite/:token` |
| 3 | Auth split-screen hero | Unchanged |
| 4 | Composition metadata: schema, API, tests | Unchanged — backend only, nothing renders it yet |
| 5 | Dashboard + full-page create flow | Unchanged — the largest frontend slice, may split in two |
| 6 | Composition page: header, section nav, stacked panels, chord grid | Unchanged |
| 7 | Compartir modal + member projection + viewer invite role | **Narrowed**: the viewer role is a one-line schema-pattern change; `permissions.py` is untouched |
| 8 | `tabs` schema + endpoint + multi-tab UI | Unchanged |
| 9 | Lyrics chord editor | Unchanged |

Per-slice rollback is unchanged from the proposal. Two notes this design adds: reverting slice 1 after
slices 5–7 is unsafe because they assume the classes exist (revert those first), and reverting slice 2
after a share link has been published breaks every bookmarked URL, which is why slices 5–7 should not
ship before slice 2 is considered permanent.

**Review budget.** Nine slices, chained PRs mandatory. `single-pr` is not a viable delivery strategy
for this change, and slices 5 and 6 each individually approach the 400-line budget — `sdd-tasks` should
forecast both as candidates for a further split.

---

## Open Questions — resolved 2026-10-01

- [x] **`frontend/src/shared/` as a new folder.** Approved by the author, same decision species as
      `frontend/src/styles/` (D10). `AppModal.vue` and `useFocusTrap.ts` live there.
- [x] **`/invite/:token` route.** Approved — travels with slice 2 (routing). `SharingModal`'s minted
      URL resolves correctly instead of silently rendering the dashboard.
- [x] **The composition header's `…` overflow menu.** Author confirmed: render no `…` for this change,
      per the original recommendation. "Eliminar composición" stays unplaced UI, to be addressed in a
      future change together with `DELETE /api/compositions/{id}`.
- [x] **Dashboard card attribution.** Author confirmed the omission: the card footer renders
      `editada hace 2 días` from `updated_at` alone, with no editor name. No `last_edited_by` field is
      added.
- [x] **`sections_enabled`.** Approved as a new schema field (AGENTS.md rule 1), alongside the five D6
      metadata fields (key, bpm, time_signature, style_tags, status) — stores which optional sections
      (chords/tablature/lyrics/demos/todos) a composition has enabled, so the dashboard card can render
      counts/badges per section without inferring presence from content. Joins D6 as a single approved
      schema delta for `sdd-tasks`.
- [ ] **`er-btn--quiet` has no rule in `bundle.css`.** Not raised with the author — reference-faithful
      (the React original emits it too) and allowlisted in the class-resolution test rather than
      defined. No action needed unless a distinct quiet treatment is wanted later (rule 2, own change).
