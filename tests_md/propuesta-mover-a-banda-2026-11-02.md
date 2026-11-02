# Test proposals — move a personal song to a band, 2026-11-02

Approved by the author on 2026-11-02 and implemented in `frontend/src/components/organisms/SongDetailsModal.spec.ts`.

The backend already implements `POST /songs/{song_id}/move` with tests (`backend/tests/test_invitations.py`). This proposal covers only the frontend control in the `Editar detalles` modal (`SongDetailsModal.vue`). Source: `decisiones/06-permisos-y-visibilidad.md` («Mover una canción personal a una banda»).

## Proposed UI

- New field `Mover a una banda` (a `<select>` with `field-input-dark`, like `Compás`), shown only when the song is personal (`owner_type = user`) and the user can manage it.
- First option `No mover` (default); then the user's bands from `GET /bands`, by name.
- Helper text under the field: «Pasa a ser de la banda; no se puede volver a personal».
- On `Guardar`, after `meta` and visibility, if a band is chosen: `POST /songs/{id}/move` with `{ band_id }`.

## Frontend

| ID | Action | Expected |
| --- | --- | --- |
| DET-012 | Owner opens the modal on a personal song | Shows `Mover a una banda` with `No mover` selected and one option per band from `GET /bands` |
| DET-013 | Owner opens the modal on a band song | No `Mover a una banda` control, and `GET /bands` is not requested |
| DET-014 | Editor who is not the owner opens the modal on a personal song | No `Mover a una banda` control, and no `move` on save |
| DET-015 | Owner chooses a band and saves | `POST /songs/{id}/move` is sent with `{ band_id }`, the page shows the returned song, and the modal closes |
| DET-016 | Owner changes visibility and chooses a band, and saves | `PATCH /visibility` is sent first, then `POST /move` |
| DET-017 | Owner saves with `No mover` | No `POST /move` is sent (previous behavior, DET-005 and DET-006, still holds) |
| DET-018 | The move fails (e.g. `422 quota_exceeded`) | The modal closes, the page shows the error message for that `code`, and the song is unchanged |
| DET-019 | Owner has no bands | The control shows only `No mover` and is disabled |

## Open questions

- None.
