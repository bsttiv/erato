# Additional test proposals — song details, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `frontend/src/components/organisms/SongDetailsModal.spec.ts`, `frontend/src/pages/CompositionsView.spec.ts` and `frontend/src/pages/CompositionView.spec.ts`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| DET-001 | List songs with each status | Each row shows its status badge |
| DET-002 | Open the details modal | Shows the current status, visibility, tempo and time signature |
| DET-003 | Change status, tempo and time signature, and save | Only those `meta` fields are sent, and the modal closes |
| DET-004 | Empty the tempo and save | `tempo: null` is sent |
| DET-005 | Save without changes | No request is sent, and the modal closes |
| DET-006 | Owner changes the visibility | `PATCH /visibility` is sent with the new value, and the page shows it |
| DET-007 | Editor who is not the owner opens the modal | No visibility control, and no `PATCH` on save |
| DET-008 | The `meta` save fails or conflicts | The modal closes, the page shows the problem, and no `PATCH` is sent |
| DET-009 | The visibility change fails | The modal closes and the page shows the error |
| DET-010 | Song with a time signature outside the usual list | It stays selected, and saving does not change it |
| DET-011 | Reader opens the song | No `Editar detalles` button |
