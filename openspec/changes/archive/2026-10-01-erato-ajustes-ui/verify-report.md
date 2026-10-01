# Verify Report: erato-ajustes-ui

Verdict: PASS WITH WARNINGS (Strict TDD active). Verified on `main` (merge a46dafa).

## Executed checks (observed)
- Backend `.venv/bin/pytest -q`: 84 passed.
- Frontend `npm run test:unit`: 286 passed, 46 files.
- `npx vue-tsc --noEmit`: clean (exit 0). `npm run build`: success (1.46s).

## Tasks
- tasks.md: 69 checked, 0 unchecked. Manual QA items are author-confirmed (not machine-verifiable).

## Spec coverage
- app-shell: single Cancelar (CompositionCreateView.vue:170, test composition-create-view.spec.ts); drawer <=768px
  (useDrawer.ts, CompositionDetailView.vue:38-49, use-drawer.spec.ts, layout-css.spec.ts media block); one-column collapse (layout-css.spec.ts).
  Breadcrumb link exists (CompositionDetailView.vue:55-61). Sidebar link first: NOT MET (see W1).
- composition-content: status via ErSegmented + status.ts (status.spec.ts, detail-view spec); Spanish dates with invalid guard
  (design-system/core/format.ts:28, format.spec.ts, ErDemoPlayer.spec.ts).
- design-system-port: ErBrand (6 consumers, ErBrand.spec.ts); field-grid minmax(0,1fr) (layout-css.spec.ts);
  horizontal fretboard (ErChordEditor.spec.ts); carousel (ChordGrid.vue:45-61, chord-grid.spec.ts); small-screen polish (layout-css.spec.ts).
  Some small-screen polish and the sharing-modal-on-phone scenario are visual: manual-only.

## Design decisions
- D1 ErBrand single `label` prop (default 'Erato'): followed. D2 useDrawer in frontend/src/shared: followed.
- D3 backdrop opacity on a separate dim layer (layout.css:757-764 comment), panel not a child: followed.
- D4 single 768px breakpoint: followed. D5 sidebar link first: deviated (W1). D6 formatDate in design-system/core/format + ErSegmented/updateComposition: followed.

## AGENTS.md rules
- No hex/rgb literals or px radii in layout.css or features/shared; no inline `style=` in features/shared. OK.
- Drawer toggle aria-label/aria-controls/aria-expanded (CompositionDetailView.vue:43-45); carousel buttons have aria-label (ChordGrid.vue:52,61). OK.
- No exclamation marks in UI text found by pattern search; Spanish text. Backend diff: none. Design-system diff: bundle.js (+menu icon) and bundle.css (1 line) only.

## Strict TDD evidence
- Artifact: openspec/changes/erato-ajustes-ui/apply-progress.md (added in 257c556, with tasks.md updates).
- WU1-WU5: RED/GREEN table per unit with named test files, failure reason and commit. Reasonable, but self-reported after the fact
  (written in the last commit, 17:42, after all code); RED outputs are one-line summaries, not captured logs.
- Post-apply fix commits (1d2320f, 74dad8e, e32076c, f47c188): marked "PASSED" with no RED. These are not true TDD; thin evidence.

## Findings
CRITICAL: none.
WARNING
- W1: f47c188 removed the "todas las composiciones" sidebar link (CompositionDetailView.vue:17-28 now holds only ErSideNav).
  Spec "Requirement: sidebar link first" and scenario "Link order" are unmet; the earlier WU1 test asserting order was rewritten
  in the same commit. Navigation now relies on header back button (:51) and breadcrumb (:55). Spec and D5 were not updated. Not resolved.
- W2: Unit 5 grew from ~250 est. to ~1000 lines over 6 commits (f934275: 322+/30-; 1d2320f: 242+/107-; 74dad8e: 107+/11-; e32076c: 69+/16-). Exceeds the review budget.
- W3: Post-apply fixes 1d2320f/74dad8e/e32076c touch behavior beyond spec: header layout (space-between), removal of '+' glyphs on add buttons,
  ErTodoList/ErLyricsViewer/ErChordName containment and height homogenization, fretboard enlargement. Visual polish, not specified in the deltas.
- W4: Post-apply fixes lack RED evidence (see TDD section).
SUGGESTION
- S1: Update the delta spec/D5 to reflect the removal, or restore the link, before archive.
- S2: Add a note that carousel/small-screen visual items are manual-only.
