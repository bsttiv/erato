# Archive Report: erato-ajustes-ui

**Change**: erato-ajustes-ui
**Archive location**: `openspec/changes/archive/2026-10-01-erato-ajustes-ui/`
**Archived**: 2026-10-01
**Status**: COMPLETE WITH KNOWN GAPS (see "Open Findings")

## Summary

UI adjustments and phone-friendly layout for Erato: single `ErBrand` logo, create-view fixes, Spanish demo dates,
editable composition status, 768px responsive layout with a drawer sidebar, a horizontal guitar fretboard (added as
point 8 / D6 during planning) and a chord carousel. Frontend only; no backend or data-model change. Delivered with the
feature-branch-chain strategy and merged to `main`.

## Artifacts Archived

proposal.md, design.md, tasks.md (69/69 checked), apply-progress.md (Gemini's TDD evidence table, self-reported),
verify-report.md (PASS WITH WARNINGS) and specs/ (3 domains), all moved with a mechanical `git mv` and an empty
`diff -r` against a pre-move snapshot.

## Specs Merged to Main

All three deltas contained only ADDED requirements and were composed with the native `gentle-ai sdd-archive-compose`
(exit 0 each). Canonical requirement counts after the merge: app-shell-and-navigation 12, composition-content 9,
design-system-port 12.

Delta corrected before archiving (author decision): the requirement about the "todas las composiciones" link said it must
be first in the SIDEBAR (decision D5). During implementation the author asked Gemini to keep that link in the page
HEADER and remove it from the sidebar (commit `f47c188`). The requirement was rewritten to "The header link to all
compositions MUST exist, the sidebar MUST NOT repeat it, and the breadcrumb word MUST be a visible link" and its scenario
to "Link location", so the canonical spec describes the shipped behavior.

## Delivery

Feature-branch-chain. Tracker PR #26 (merge `a46dafa`) with five unit PRs merged into it in order, each retargeted to the
tracker before merging: #27 quick fixes, #28 brand and status, #29 responsive foundation, #30 horizontal fretboard,
#31 chord carousel. The independent index-script PR #25 (merge `b2994b8`) went to main first. Units 2 and 3 slightly
exceeded the 400-line budget (402 and 432 lines) and unit 5 reached ~1000 lines; `size:exception` was recommended in the
PR bodies. This archive travels in its own docs PR instead of a direct push to main.

## Final-State Facts (outrank the verify snapshot)

- Verify verdict: PASS WITH WARNINGS (0 critical). Observed: backend 84 passed, frontend 286 passed (46 files),
  `vue-tsc` clean, build OK.
- W1 (sidebar link removed): RESOLVED by the author's decision above; spec corrected, code unchanged.
- The author's manual QA (360/390/768/1024px, themes Noche and Matine) was done and reported correct; the five manual-QA
  tasks were marked complete.
- Design-system edits stayed minimal: `bundle.js` (+ `menu` icon) and one line of `bundle.css`.

## Open Findings (not resolved, recorded honestly)

- W2: unit 5 grew from ~250 estimated lines to ~1000 across six commits.
- W3: commits `1d2320f`, `74dad8e`, `e32076c` add visual polish outside the written spec (header spacing, removal of "+"
  glyphs on add buttons, height and containment tweaks for todos, lyrics and chord names, a larger fretboard). The author's
  manual QA accepted them; they are not described in the specs.
- W4: TDD evidence is thin: `apply-progress.md` was written after the code with one-line RED summaries, and the four
  post-apply fix commits have no RED recorded.
- S2: carousel feel and the sharing modal at 360px are manual-only checks.
- Carried over from earlier changes: the invitation link is not single-use (author decision), demo playback and timed
  comments have no manual test and signed playback URLs expire (~1 h), and verify warnings 3 and 4 of
  `erato-editor-contenido` remain open.

## Traceability

Engram: proposal #133, spec #134, design #135, tasks #136 (all updated for point 8), verify-report #138.
