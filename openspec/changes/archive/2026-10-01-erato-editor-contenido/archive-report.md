# Archive Report: erato-editor-contenido

**Change**: erato-editor-contenido
**Archive location**: `openspec/changes/archive/2026-10-01-erato-editor-contenido/`
**Archived**: 2026-10-01
**Status**: COMPLETE WITH KNOWN GAPS (see "Open Findings")

## Summary

The content-editor change (page-shell layout, router, auth split-screen, composition metadata, dashboard,
detail view with chord grid, sharing modal with viewer role, multi-tab tablature and the drag-and-drop
lyrics chord editor) is implemented, verified and archived. Delta specs were composed into the canonical
specs. Delivery used the feature-branch-chain strategy.

## Artifacts Archived

| Artifact | Status |
|----------|--------|
| exploration.md | Present |
| proposal.md | Present |
| design.md | Present |
| tasks.md | Present (all tasks 1.1-11.5 checked) |
| verify-report.md | Present (PASS WITH WARNINGS; written to engram as obs #122) |
| specs/ (5 domains) | Present |

Not present: `apply-progress` (never persisted; see Open Findings).

## Specs Merged to Main

Composition ran through the native `gentle-ai sdd-archive-compose` command (exit 0 each) for domains that
already had a canonical spec, and a mechanical `cp` with an empty `diff -r` for new domains.

| Domain | Method | Result |
|--------|--------|--------|
| design-system-port | `sdd-archive-compose` | Merged (+48 lines, ADDED requirements) |
| sharing-and-visibility | `sdd-archive-compose` | Merged: 1 RENAMED + 1 MODIFIED + 3 ADDED; canonical now has 7 requirements |
| app-shell-and-navigation | mechanical copy, `diff -r` empty | Created |
| composition-content | mechanical copy, `diff -r` empty | Created |
| lyrics-chord-assignment | mechanical copy, `diff -r` empty | Created |

Delta correction made at archive time: the sharing-and-visibility delta used MODIFIED for
"Only invited editor-role users MUST be able to edit a public composition", a name that did not exist in the
canonical spec (it was "Only invited users MUST be able to edit a public composition"). The first compose
attempt refused and wrote nothing. A `## RENAMED Requirements` block (old -> new, with Reason and Migration)
was added to the delta before the MODIFIED block and the compose then succeeded. A partial canonical edit left
by the failed attempt in `design-system-port/spec.md` was reverted with `git checkout` before the retry.

Archive move: `git mv openspec/changes/erato-editor-contenido openspec/changes/archive/2026-10-01-erato-editor-contenido`,
verified against a pre-move recursive snapshot with `diff -r` (output empty).

## Final-State Facts (outrank the verify-report snapshot)

- Verify verdict was PASS WITH WARNINGS: 0 critical, 4 warnings.
- Warning 1 (`/c/:ref` id-first probe missing): FIXED in `dc83999`
  `feat(frontend): resuelve /c/:ref probando id y luego slug` (route param `:ref`, `resolveCompositionRef.ts`,
  `HttpError` carrying the status).
- Warning 2 (emoji in UI): FIXED in `acb5d73` `fix(frontend): quita emoji de los botones de tablatura`. The
  check/cross glyphs in `SharingModal.vue` and the "quitar" chip were left on purpose (spec-defined text glyphs,
  not emoji).
- Two runtime bugs reported after verify were also fixed:
  - `d1b431b` removed the broken `<link>` tags in `frontend/index.html` (design-system CSS served as
    `text/html` by the Vite dev server under Docker; `main.ts` already imports both files).
  - `28c828a` `saveAll()` now calls the typed section endpoints and surfaces errors. Before, it hit
    `/sections/{type}` routes that the backend does not expose and swallowed every failure.
- Test evidence: frontend `npm run test:unit` 40 files / 199 tests passed; `npm run build` OK. Backend was not
  touched after verify; its last full run was 78 passed. It was NOT re-run after the fixes (MongoDB was not
  running locally: 36 passed, 42 setup errors).

## Open Findings (not resolved, recorded honestly)

- Warning 3: no `apply-progress` artifact exists, so the strict-TDD RED/GREEN evidence table cannot be audited.
  The fix-up commits above were done RED-first by their writer, but the original 10 slices have no persisted
  evidence table.
- Warning 4: task 11.5 (manual accessibility and theme audit) has no recorded evidence.
- Backend suite not re-run after the final fixes (see above).
- Suggestion carried over: a ~126k-line PDF (`Erato — pantallas.pdf`) is part of the branch diff; consider keeping
  it out of the repository history.
- Suggestion carried over: the jump nav uses plain `#sec-*` anchors; scroll offset and focus handling are open.

## Delivery

Strategy: feature-branch-chain. Tracker branch `feature/erato-editor-contenido` (PR #10 -> main). Ten slice PRs
(#11-#20), each opened against its parent branch and re-targeted to the tracker before being merged with a merge
commit. Every slice exceeded the 400-line review budget (366 to 1658 changed lines, tests and docs included);
`size:exception` was recommended in each PR body. The archive commit travels in the tracker PR, not as a direct
push to main.

## Traceability

Engram: verify-report obs #122; ODD fix-up tracker obs #123 (`odd/erato-fix-verify-warnings/tasks`).
Other SDD artifacts were read from the openspec folder, not from engram.

## Addendum (post-archive, browser findings)

After the archive commit the author exercised the app in the browser (Docker) and reported two more defects.
Both were fixed on the tracker branch before the merge to main, with RED-first tests:

- `ed250cc` `fix(frontend): estiliza los links de migas, jump nav y sidebar`: `.er-crumb a`, `.er-sectionnav a` and
  `.er-sidebar-foot a` had no rules, so the browser-default blue showed. Token-only rules added in `layout.css`.
- `27e4093` `feat(lyrics): permite escribir el texto de la letra`: SCOPE CHANGE approved by the author on
  2026-10-01. The canonical `lyrics-chord-assignment` spec states that free-form lyrics text editing is out of
  scope, which left no way to type lyrics in the UI. `LyricsSection` now has an "Editar letra" text mode with a
  `<textarea class="er-textarea">` (new token-only variant in `layout.css`, same look as `.er-input` with free
  height), saved through the existing typed lyrics endpoint. No data-model change. The canonical spec text was NOT
  updated to reflect this; a follow-up spec delta is recommended.
- Test evidence after these fixes: frontend `npm run test:unit` 40 files / 213 tests passed; `npm run build` OK.
  These two fixes were not checked in a browser by the agent that wrote them.
