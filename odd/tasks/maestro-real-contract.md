Objective: make Erato work against the deployed Maestro, and publish this repository in `bsttiv/erato`.
Branch: feat/maestro-real-contract. Delivery: ask-on-risk. Runner: `make test`.
Large because implementation waits on the author's test approval (AGENTS.md, rule 3).

## Specs

- S1: "arregla la implementación de maestro": Erato's client and mock follow `bsttiv/maestro` at 9bb371f: `/api/v1/maestro` prefix, `X-Api-Key`, `/validate` returning `{userId, sessionId}`, 401 for invalid tokens, `/refresh` with `{refresh, fingerprint}`, `/revoke` with `{token}`, and access tokens without `jti`.
- S2: `sessions.jti` becomes `sessions.sid` (string, unique index), approved 2026-11-01. The old `jti_1` index is removed.
- S3: logout revokes in Maestro with the current access token. Other devices close by deleting their Erato row, approved 2026-11-01 as "Cierre local".
- S4: tests follow `tests_md/propuesta-maestro-real-2026-11-01.md` once approved.
- S5: "quiero literalmente poner este directorio dentro de github.com/bsttiv/erato". The author chose "Sin historia" and "Rama y PR".

## Tasks

- T1 [S4] inline: done, approved 2026-11-01
- T2 [S1, S2, S3] inline: done, 71c5eca and 970efe3; both verifier blockers rechecked as fixed. Risk: items 1, 2 and 3
- T3 [S1] inline: update `archivos/arquitectura.md`, `archivos/esquema_mongodb.md`, `backend/API.md`, `.env.example`, compose files and `tests_md/README.md`. Done, 6149fd8 for `.env.example`
- T4 [S5] inline: pushed as `feat/erato-rewrite` (3ac578d) with a PR; merge is the author's, after configuring Vercel

Route evidence: every task is inline. One behaviour with dependent parts, so the Writer trigger does not apply.

## Log

- L1 (2026-11-01, author): "vuelve a revisar como funciona maestro, ahora el proyecto está corriendo sobre https://161.153.57.235.sslip.io/ cambiaron algunas cosas de la api asi que verifica además, quiero agregar todo esto a github.com/bsttiv/maestro".
- L2 (2026-11-01, author): "arregla la implementación de maestro con lo último, me refiero a que quiero literalmente poner este directorio dentro de github.com/bsttiv/erato".
- L3 (2026-11-01): checked without credentials: `/health` 200, the four session routes 401 `Missing API Key`, `/mint` at the root 404, `/docs` 404. Authenticated flows are unverified: no API key is authorized and `maestro-ssh/.env` was not read.
- L4 (2026-11-01, author): chose "Cierre local (Recomendado)", approving `sid`. A revoked device stays alive inside Maestro until it expires, at most 7 days, but cannot be used through Erato.
- L5 (2026-11-01): `erato_v2` holds a unique `jti_1` index if the app's indexes were created there, and rows without `jti` would collide on it, so index creation must drop it (MAE-041).
- L6 (2026-11-01): `bsttiv/erato` is public, holds the old app with its history, branches, LICENSE and CLA. Its local clone is `proyectos/erato`; this repository's origin is `bsttiv/erato-rewrite`.
- L7 (2026-11-01, author): "apruebo", for the test proposal.
- L8 (2026-11-01): the mock must keep old access tokens valid after a refresh, as Maestro does, because it has no per-token revocation. SES-021 now expects `200` for the old token up to its expiry. The proposal notes this; it was not in the approved text.
- L9 (2026-11-01): reading `.env.example` is denied by this session's permissions and was not worked around. `MAESTRO_API_KEY` must be added there by the author, which fixes INFRA-032. RDD is off, so native review is skipped; an independent verifier runs because the Risk line names items 1, 2 and 3.
- L10 (2026-11-01): verifier on 71c5eca: S1, S3, S4 pass; S2 fails. Blocker 1: two old rows without `sid` collide on the new unique index and stop startup. Blocker 2: two tabs refreshing together make Maestro see reuse and revoke the session, 30 of 30 trials. Backend at 6149fd8: 594 passed. It also read one line of `.env.example`, `MAESTRO_URL` without the prefix, against its instructions; its scratch copy was removed. Corrections proposed as MAE-042 to MAE-046, pending approval.
- L11 (2026-11-01, author): "apruebo, explica tambien lo del limite de maestro", for MAE-042 to MAE-046 and the SES-021 change. RED: MAE-042, 043, 044 and 046 failed; MAE-045 already held.
- L12 (2026-11-01): corrections in 970efe3. `make test`: backend 597 passed, frontend 194 passed and 1 skipped; `vue-tsc` passed. Recheck: blocker 1 fixed with real uvicorn on three cases, blocker 2 fixed for tabs of one browser, with the Web Locks API under Node and simulated cookies, not a real browser. Open: overlap outside the lock still ends the session; a row without `sid` is deleted on every start, as approved in MAE-042; authenticated flows against the real Maestro are unverified. Risk: items 1, 2 and 3.
- L13 (2026-11-01, author): chose "Sin historia", then "Rama y PR (Recomendado)".
- L14 (2026-11-01): `bsttiv/erato` deploys through Vercel to `erato-alpha.vercel.app`, so `main` was not touched. One commit, 3ac578d, on top of its old main with the tree of this branch; the private history was not pushed. The snapshot scan found no credentials or personal email addresses, excluding `.env.example`, which this session cannot read. `.github/` and the CLA workflow leave with the merge.
- L15 (2026-11-01, author): pasted the Vercel error "[MULTIPLE_FRAMEWORKS_SERVICE] Multiple frameworks detected in project root: Vite, Container. Specify "framework" explicitly in services." Both service roots hold a Dockerfile for local compose, so `vercel.json` now pins `vite` and `fastapi`.
