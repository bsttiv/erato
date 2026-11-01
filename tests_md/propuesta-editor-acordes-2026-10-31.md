# Additional test proposals — chord editor and song status, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `frontend/src/components/molecules/LyricPlacer.spec.ts`, `frontend/src/components/molecules/LyricSheet.spec.ts`, `frontend/src/components/atoms/SongStatus.spec.ts` and `frontend/src/pages/CompositionView.spec.ts`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| CHE-001 | Song with two forms of `C` | One `C` chip with `1/2`, and previous and next form buttons |
| CHE-002 | Song with one form of a chord | No form buttons and no counter |
| CHE-003 | Press next form on the last form | Returns to the first form, and the counter shows `1/2` |
| CHE-004 | Select form 2 and drop the chip on a line | The placed `chord_id` is form 2 |
| CHE-005 | Hover or focus a palette chip | The figure of the selected form is shown |
| CHE-006 | Press a form button, then move the pointer away | The figure disappears |
| CHE-007 | Press the X of a placed chord | That chord is removed and the others stay |
| CHE-008 | Press and release a placed chord without moving it | Nothing changes |
| CHE-009 | Hover or focus a chord in the lyrics | The figure is shown, and it disappears on leave or blur |
| CHE-010 | Open the lyrics editor | No instrumental button and no placement form; the label mentions `#` |
| STA-001 | Song with status `idea`, `in_progress` and `ready` | Shows Idea in purple, En progreso in yellow and Lista in green |
| STA-002 | Song with an unknown or missing status | Nothing is shown |
