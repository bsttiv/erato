# Frontend test proposals — 2026-10-30

Pending author approval. These proposals are not implemented as regression tests.
Approved decision 09 keyboard/grammar and lyric-placement rules are implemented as
`EDT-rule`/`LYR-rule` tests, and approved SONG/REV/PERM/RUTA area rules keep their
provenance in each spec. The original numbered rows are absent from this checkout;
no numeric ID-to-behavior mapping was invented.

| Proposal | Preconditions / action | Expected |
| --- | --- | --- |
| API failure during creation | Create succeeds, publishing fails, retry publication | One song, no duplicate POST, visible publication error; navigation uses server ID |
| Stale route responses | Open song A, switch to B while A loads | Only B can populate its state; no A draft or capability leaks |
| Stale chord-name responses | Change notes twice; responses arrive in reverse | Only the current notes' server name is displayed |
| Clipboard failure | Clipboard rejects or is unavailable | No false “Copiado”; manual copy remains possible |
| Draft preservation | Edit lyrics/tasks/tabs/chord/key; save another section | Unsaved draft survives; conflicted bases are not silently advanced |
| Actor capabilities | Open owned, band, shared-editor and shared-reader songs | Controls follow server-derived edit/manage capabilities; backend enforces writes |
| In-flight saves | Type more lyrics/tasks/tab notes while a save waits | Only submitted content is acknowledged; newer local edits remain visible |
| In-flight visibility | Publish A, navigate to B, then resolve A | B remains on screen with its own link |
| Logout cache | Load a private song, logout, open same URL | Cached private data and controls are cleared |
| Keyboard lifecycle | Mount/unmount stage, toggle playback/speed | No remaining timer; scroll pauses and resumes without changing song data |

## Integration limitation

The current full-song API exposes no actor capabilities, and `/me` exposes no
internal user ID. Frontend therefore infers only known ownership/band editing from
`GET /songs?workspace=all` origins. Shared editor/reader roles use the documented `/songs/{id}/members` public
username projection matched to `/me`. If unavailable, shared controls fail closed.
Band visibility management stays hidden unless a future response supplies
`permissions: {edit, manage}`. No write is sent to probe permission and no token is
decoded as authority. A backend capability projection is needed to complete band-owner
management controls; this frontend task deliberately does not change `backend/`.

Public links use `/c/{share_slug}`; authenticated app links use `/c/{id}` because
private songs do not have a share slug. Optional sections begin empty, as specified
by the API. New-song section toggles preview possible content, not persisted flags.
Band/invitation/demos UI is deferred as requested. Key-reset notices reuse existing
card styles (A7), not a new snackbar.
