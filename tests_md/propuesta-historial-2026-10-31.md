# Additional test proposals — history page, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `frontend/src/pages/HistoryView.spec.ts`, `frontend/src/components/organisms/CompositionHeader.spec.ts`, `frontend/src/router.spec.ts` and `frontend/src/pages/CompositionView.spec.ts`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| HVW-001 | Open a song as a member | The tabs include Historial, linked to `/historial` |
| HVW-002 | Open a public song without a session | No Historial tab |
| HVW-003 | Open `/canciones/:id/historial` without a session | Redirects to the login |
| HVW-004 | Open the page for a song with revisions in several sections | Shows `Historial · title` and one list across all sections, newest first |
| HVW-005 | Two sections hold the same version number | Both rows appear |
| HVW-006 | Press Ver on a row | Reads that row's section and version, and shows its snapshot |
| HVW-007 | Press Restaurar as an editor | Restores that row's section with its current base version, reloads the song and the list |
| HVW-008 | Restore a stale section | Shows the outdated section message, and the list stays |
| HVW-009 | Open the page as a reader | Rows show Ver but not Restaurar |
| HVW-010 | One section request fails | Shows the error, and no partial list |
| HVW-011 | Song with no revisions | Shows `Aún no hay cambios.` |
| HVW-012 | Open the Letra page | History is no longer shown there |
