# Additional test proposals — real Maestro contract, 2026-11-01

Approved by the author on 2026-11-01 and implemented in `backend/tests/test_maestro.py`.

Source of the contract: `bsttiv/maestro` at `9bb371f`. Automated tests keep using the mock, never the real service, so the mock must match that contract first.

## Replaced cases

| Existing test | Change |
| --- | --- |
| INFRA-040 to INFRA-049, INFRA-060, INFRA-061 | Rewritten against the contract below; MAE-001 to MAE-012 supersede their old expectations |
| AUTH-027 | Parameter `error_400` becomes `error_503` |
| SES-021 | Asserts that `sid` stays the same instead of `jti` changing. The old access token now answers `200` until it expires, because Maestro has no per-token revocation; found during implementation, not in the approved text |
| SES-026 | Superseded by MAE-029 |
| SES-036 | Compares `sid` instead of `jti` |
| `test_database.py` fixture and unique index assertion | `jti` becomes `sid` |

## Mock contract

All routes live under `/api/v1/maestro`, so local and production differ only in `MAESTRO_URL` and `MAESTRO_API_KEY`.

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| MAE-001 | No `X-Api-Key` | Call each of the four routes | `401` with `Missing API Key` |
| MAE-002 | Wrong `X-Api-Key` | Call each of the four routes | `401` with `Invalid API Key` |
| MAE-003 | Valid key | `POST /mint` | `200`; access claims are `typ`, `iss`, `sub`, `sid`, `ctx`, `iat`, `exp` with no `jti`; refresh claims add `jti`; both share `sid`; `ctx` is not the clear fingerprint |
| MAE-004 | Valid access token | `POST /validate` | `200` with `{userId, sessionId}`, matching the mint input and `sid` |
| MAE-005 | Malformed, expired or revoked token, a refresh token, or another fingerprint | `POST /validate` | `401` for each |
| MAE-006 | Valid pair | `POST /refresh` with `{refresh, fingerprint}` | `200`; same `sid`; new `jti`; refresh `exp` unchanged |
| MAE-007 | Refresh token already used | `POST /refresh` | `401`; the newest pair stops working too |
| MAE-008 | Valid refresh token, another fingerprint | `POST /refresh` | `401`; the session is revoked |
| MAE-009 | Valid access or refresh token | `POST /revoke` with `{token}` | `204`; `/validate` and `/refresh` answer `401` |
| MAE-010 | Invalid token | `POST /revoke` with `{token}` | `401` |
| MAE-011 | `{jti}` or `{refreshToken}` body | Call `/revoke` or `/refresh` | `400` |
| MAE-012 | Forced fault | Call any route with `error_503` or `no_response` | `503`, or no answer within the client timeout |

## Backend — client

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| MAE-020 | Any Maestro call | Inspect the mock's call log | Every call carries `X-Api-Key`; no response body contains the key |
| MAE-021 | `MAESTRO_API_KEY` unset | Start the application | Startup fails naming the missing variable, not its value |
| MAE-022 | Maestro answers `401` to `/validate` | Authenticated request | `401 not_authenticated` |
| MAE-023 | Maestro answers `429` or `503` to `/validate` | Authenticated request | `502 session_upstream_error` |
| MAE-024 | Maestro answers `/validate` without `userId` or `sessionId`, or as a non-object | Authenticated request | `502 session_upstream_error` |

## Backend — sessions

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| MAE-025 | Registered user | Log in | The row stores the access token `sid`, has no `jti`, and `expires_at` equals the refresh `exp` |
| MAE-026 | `/mint` returns a pair with mismatched or missing `sid`, or another `sub` | Log in | `502 session_upstream_error`; no row inserted |
| MAE-027 | Valid session | Authenticated request | The row is found by the `sessionId` and `userId` from `/validate`; the token is not decoded for this |
| MAE-028 | Valid refresh cookie | `POST /auth/refresh` | Maestro gets `{refresh, fingerprint}`; `sid` unchanged; hash replaced; `expires_at` not extended |
| MAE-029 | Valid session | `POST /auth/logout` | Maestro gets `/revoke` with `{token}` holding the current access token; row deleted; cookie cleared |
| MAE-030 | `/revoke` answers `503` | `POST /auth/logout` | `502 session_upstream_error`; row kept |
| MAE-031 | Session on device B, requested from device A | `DELETE /me/sessions/{id}` | `204`; no `/revoke` call; row deleted; device B's access token gets `401`; device B's refresh gets `401` |
| MAE-032 | Current session | `DELETE /me/sessions/{id}` | `204`; `/revoke` called with the current access token; row deleted |
| MAE-033 | Sessions on devices A and B | Change the password from A | `204`; no `/revoke` call; B's row deleted; A keeps working; new hash stored |
| MAE-034 | Two sessions | `GET /me/sessions` | `current` is true only for the row whose `sid` matches the request |

## Backend — schema

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| MAE-040 | Empty database | Create indexes | `sid_1` is unique; no `jti_1` |
| MAE-041 | `sessions` already has the unique `jti_1` index | Create indexes twice | `jti_1` removed, `sid_1` present, no error on either run; two rows with no `jti` can be inserted |

## Addendum after verification

Approved by the author on 2026-11-01, together with the SES-021 change. MAE-044 and MAE-045 are in `frontend/src/api/client.spec.ts`.

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| MAE-042 | Two `sessions` rows with `jti` and no `sid` | Create indexes | No error; those rows are deleted; rows with `sid` stay; `sid_1` is unique |
| MAE-043 | `jti_1` already removed by another instance | Create indexes | No error |
| MAE-044 | Two clients of the same browser, both needing a refresh | Call `refresh()` on both at once | The second `/auth/refresh` starts only after the first ends; both clients hold a session |
| MAE-045 | Browser without `navigator.locks` | Call `refresh()` | Works as today, with no lock |
| MAE-046 | Maestro answers `401` with `Missing API Key` or `Invalid API Key` | Authenticated request and `POST /auth/refresh` | `502 session_upstream_error`, not `401`; the session row is unchanged |
| MAE-047 | Vercel entrypoint `app.asgi` | `GET /api/health`, and `POST /api/auth/login` with an empty body | `200`, and `422 validation_error` instead of `404`; approved 2026-11-01 |
