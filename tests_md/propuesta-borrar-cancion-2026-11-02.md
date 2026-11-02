# Test proposals — delete a song, 2026-11-02

Approved by the author on 2026-11-02 and implemented in `frontend/src/components/organisms/SongDetailsModal.spec.ts`.

The backend already implements `DELETE /songs/{song_id}` (`manage` right; cascades demos in Cloudinary, comments, revisions, links and song memberships). This proposal covers only the frontend control.

## Proposed UI

- At the bottom of the `Editar detalles` modal (`SongDetailsModal.vue`), shown only to whoever can manage the song: a `Borrar composición` button (`btn-ghost btn-sm`).
- Two-step confirmation, the same pattern as `DemoDetail.vue` and `BandView.vue`: the first click replaces it with `Confirmar: borrar composición, demos y comentarios` (`btn-primary btn-sm`) and `Cancelar`, plus the text «No se puede deshacer».
- On confirm: `DELETE /songs/{id}`, then navigate to `/canciones`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| DET-020 | Owner opens the modal | Shows `Borrar composición`; no `DELETE` is sent yet |
| DET-021 | Editor who cannot manage opens the modal | No `Borrar composición` control |
| DET-022 | Owner clicks `Borrar composición` | Shows `Confirmar: borrar composición, demos y comentarios`, `Cancelar` and «No se puede deshacer»; no `DELETE` is sent |
| DET-023 | Owner clicks `Cancelar` | Back to `Borrar composición`; no `DELETE` is sent |
| DET-024 | Owner confirms | `DELETE /songs/{id}` is sent once and the app navigates to `/canciones` |
| DET-025 | The delete fails | The modal closes, the page shows the error, there is no navigation and the song is unchanged |
| DET-026 | Owner changes status and visibility, then confirms the delete | Only `DELETE` is sent: no `meta`, visibility or move request (the existing DET-003 to DET-019 still pass) |

## Open questions

- None.
