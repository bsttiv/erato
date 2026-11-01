# Additional test proposals — lyrics editor, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `backend/tests/test_songs.py`, `frontend/src/lib/lyrics.spec.ts` and `frontend/src/components/molecules/LyricPlacer.spec.ts`. LYR-111 pins the layout classes, because the test environment has no layout engine.

LYR-105 was removed on 2026-10-31 together with the button it covered, at the author's request.

## Backend

| ID | Input | Expected |
| --- | --- | --- |
| LYR-001 | Save `{ section: " Coro ", text: "", chords: [] }` | Stored and returned with `section: "Coro"` |
| LYR-002 | Save a line with `section` and non-empty `text` | `422 validation_error`, nothing written |
| LYR-003 | Save a line with `section` and chords | `422 validation_error`, nothing written |
| LYR-004 | Save `section` empty, only spaces, or 41 characters | `422 validation_error`, nothing written |
| LYR-005 | Save a line without `section` | Stored without a `section` key |
| LYR-006 | Restore a revision saved before `section` existed | Restored unchanged |

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| LYR-101 | Type `#coro` on its own line | Line stored as a section named `coro` |
| LYR-102 | Add `#coro` above a line with chords | Each lyric line keeps its chords |
| LYR-103 | Type `#` alone | Stays as lyric text |
| LYR-104 | Open the editor on saved sections | Text shows `#name`, and retyping changes nothing |
| LYR-106 | Drop a palette chord on a line | Chord placed at the pointer column |
| LYR-107 | Drop a placed chord on another line | Chord moves |
| LYR-108 | Drop a placed chord outside the lyrics | Chord removed |
| LYR-109 | Drop a palette chord outside the lyrics | Nothing changes |
| LYR-110 | Point at a section line | It is not a drop target |
| LYR-111 | Song page with 30 chords at 390px and 1280px wide | Page width equals the viewport; chords scroll inside their card |
