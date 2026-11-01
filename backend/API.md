# Backend API

Paths are relative to the backend; production mounts it at `/api`.
Interactive OpenAPI documentation is available at `/docs` and `/openapi.json`.
Bodies and responses use JSON; successful `204` responses are empty.

## Routes

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| GET | `/health` | — | `200 {status: "ok"}` |
| POST | `/auth/register` | `email`, `username`, `display_name`, `password` | `201 {user: {username, display_name}, access_token?}`, `Set-Cookie` refresh token |
| POST | `/auth/login` | `email`, `password` | `200 {access_token}`, `Set-Cookie` refresh token |
| POST | `/auth/refresh` | — (refresh cookie) | `200 {access_token}`, `Set-Cookie` rotated refresh token |
| POST | `/auth/logout` | — | `204`, clears the refresh cookie |
| GET | `/me` | — | `200 {username, display_name, email}` |
| PATCH | `/me` | `username` and/or `display_name` | `200` own-user projection |
| PATCH | `/me/email` | `email`, `current_password` | `200` own-user projection |
| PATCH | `/me/password` | `current_password`, `new_password` | `204` |
| GET | `/me/sessions` | — | `200 [{id, device, last_access_at, created_at, current}]` |
| DELETE | `/me/sessions/{id}` | — | `204` |

All `/me` routes and logout require `Authorization: Bearer <access_token>` and
`X-Device-Id`. Register, login and refresh require `X-Device-Id` without Bearer.
The refresh token never appears in a JSON body. Register (when Maestro is
available), login and refresh set cookie `refresh_token` with `HttpOnly`, `Secure`,
`SameSite=Strict`, `Path=/api/auth` (the browser-visible mount, not the backend-relative
`/auth`) and `Max-Age` of 7 days; refresh reads it and logout clears it. A missing cookie
on refresh is `401 not_authenticated`. Calling the backend directly without the `/api`
prefix (for example `localhost:8000`) does not send the cookie.
The opaque device ID is forwarded unchanged to Maestro; it is not persisted.
Session IDs are MongoDB ObjectIds serialized as strings; dates use UTC ISO 8601.
Only `username` and `display_name` are exposed by `public_user()` to other users.

## Behavior

- Email and username are lowercased. Display names are trimmed, 1–60 Unicode
  code points. Username: 3–30 ASCII lowercase letters, digits and single internal
  hyphens. Password: 8–128 code points, no composition rules, Argon2id storage.
- Registration succeeds without tokens when Maestro is unavailable. No session
  is created in that case. Login uses a dummy Argon2id verification for unknown email.
- Maestro requests have a 3-second timeout and no automatic retries. Every call
  sends `X-Api-Key`. `/validate` returns the `userId` and `sessionId` used to find
  the session row. Refresh rotates the same session and never extends it: it ends
  7 days after login, and a replaced access token works until it expires.
- Logout and closing the current session revoke in Maestro with the current access
  token, then delete the row. Maestro revokes only by token and Erato stores none,
  so closing another device deletes its row: Erato rejects that device at once,
  while its Maestro session stays alive until it expires, at most 7 days.
- A 401 from Maestro about Erato's own API key answers `502 session_upstream_error`.
  Maestro limits each API key to `MAESTRO_RATE_LIMIT_PER_MINUTE` calls, 600 by default,
  and every authenticated request costs one `/validate`; over the limit, Erato answers 502.
- Tabs of one browser serialize `/auth/refresh` with `navigator.locks`, because Maestro
  treats overlapping refreshes as reuse and ends the session.
- Password change deletes all other sessions before changing the hash. The current
  session and other users' sessions remain intact.
- Five failed credentials checks for the same normalized email + IP within 15
  minutes block subsequent login/email/password changes, with `Retry-After` in
  seconds. The fifth failure is still `401`. A successful mint clears that pair's
  attempts; correct current-password checks do not. TTL is not relied on for expiry.
- Session lists exclude expired records even before TTL removal. Successful
  authenticated requests update only their session, at most once per minute.
- Errors use `{code, detail}`; code and HTTP status are stable, detail is not.
  Validation errors never echo submitted values. The approved catalog is in
  `app/errors.py` and decision 07 section 6.

## Local choices and limits

Unspecified success-envelope details use the shapes above. Unknown User-Agent
uses the approved label `Dispositivo desconocido`; common browsers/platforms use
`{browser} en {system}`. The first `X-Forwarded-For` address is used, falling back
to the connection peer when absent. Production must verify that the trusted edge
replaces client-supplied XFF; otherwise rate limiting can be bypassed.

The clock is injectable through `create_app(clock=...)`. MongoDB dates are
UTC-aware and only approved indexes are
created, idempotently at startup. No MongoDB validators are installed.

Tests use real isolated MongoDB and the existing controlled Maestro HTTP mock,
not the live provider. Original `tests_md/` case rows were intentionally omitted
from this repository (decision 14). Tests only claim individually recoverable IDs:
AUTH-027 (both documented mint-failure modes), AUTH-028, SES-021, SES-026,
SES-036, USR-024, PERF-010, PERF-030 and INFRA-011–014. Other ID-to-behavior
mappings remain unavailable; none are guessed. PQ and P11-deferred cases are not
implemented. Broader security checks are verification probes, not new approved
regression tests. The client and the mock follow `bsttiv/maestro` at `9bb371f`;
MAE cases are in `tests/test_maestro.py`.

## Songs and workspaces (T4)

All `/songs` routes require the same Bearer + `X-Device-Id` session as `/me`.
Only `GET /c/{slug}` is anonymous. IDs are strings in JSON and ObjectIds in MongoDB,
including embedded section IDs (A2). No collections or persisted fields were added
beyond decision 05. The approved songs and revisions indexes are created at startup.

| Method | Path | Body / query | Success |
| --- | --- | --- | --- |
| POST | `/songs` | `title`; optional metadata; `owner_type: "band", owner_id` for a band | `201` song |
| GET | `/songs` | `workspace=personal\|shared\|all\|band`; `band_id` with `band` | `200` songs with `origin` |
| GET | `/songs/{id}` | — | `200` full song |
| PUT | `/songs/{id}/sections` | `sections`, `base_versions` | `200 {song, saved, conflicts, key_reset}` |
| PATCH | `/songs/{id}/visibility` | `visibility: "private"\|"public"` | `200` song |
| DELETE | `/songs/{id}` | — | `204` |
| POST | `/songs/{id}/chord-name` | chord input (below) | `200 {name}`; no writes |
| GET | `/songs/{id}/revisions/{section}` | — | `200` latest 50 snapshots, newest first |
| GET | `/songs/{id}/revisions/{section}/{version}` | — | `200` snapshot |
| POST | `/songs/{id}/revisions/{section}/{version}/restore` | `base_version` | Same envelope as section save |
| GET | `/c/{slug}` | — | `200` public read projection |

Songs include derived `key_candidates`, never persisted. A section save reports
`key_reset` when the detector resets an existing selection. Personal listings contain
only owned songs; shared listings contain song memberships excluding owned songs and
songs in the user's bands; all listings add band songs without duplicates. Origins are
`own`, `shared`, or `band`. Listings are ordered by descending `updated_at`.
Band membership/ownership is read directly from `memberships` and `bands`; T5 owns
membership writes. Creating a song in a band requires membership or band ownership.

### Explicit saves

```json
{
  "sections": {
    "meta": {"title": "Under the lamp", "tempo": 92},
    "tasks": [{"title": "Record bass", "done": false}]
  },
  "base_versions": {"meta": 1, "tasks": 1}
}
```

Each submitted section requires its base version. `meta` is a patch of `title`,
`status`, `tempo`, `time_signature`, `key`, `key_mode`; other sections replace the
whole section. `tabs` maps to the song's `tablatures` field. Empty lists remove
all elements, and `lyrics: null` removes lyrics. Unknown input fields are rejected.

- New chords/tabs/tasks omit `id`; the server assigns it. Existing elements retain
  their IDs. Clients cannot import an ID from another section or song. IDs of new
  chords are obtained from a successful save before placing them in lyrics.
- Chords: `{id?, instrument, notes, frets?, strings?}`. Names are server-calculated;
  input `name` is rejected. Guitar notes must match standard tuning and its parallel
  fret/string arrays; piano uses null fret/string arrays.
- Tabs: `{id?, title?, tuning?, columns}`. Default title is the approved
  `Tablatura N`, default tuning is `E4 B3 G3 D3 A2 E2`. Cells strictly follow
  decision 09; a bar occupies all six strings. No editor normalization is done here.
- Lyrics: `{lines: [{section?, text, chords: [{col, chord_id}]}]}`. Columns are nonnegative,
  unique per line, and may extend beyond text. IDs must belong to the song.
  `section` is trimmed to 1–40 characters and names a song part; that line must
  have empty `text` and no chords.
- Tasks: `{id?, title, done?}`. Title is trimmed to 1–200 characters; omitted
  `done` defaults to false and supplied `done` must be boolean.
- Unchanged normalized content produces no new version/revision. Every changed
  section gets a full snapshot with authenticated `author_id` and a server-written
  `summary` of up to 120 characters; revisions older than that field return
  `summary: null`. Key/name changes
  and deleted-chord lyric cleanup version their affected sections in the same
  transaction; implicit dependencies use the transaction's current snapshot.
- Stale sections are not saved. Independent sections still save, returning
  `saved: [{section, version}]`, `conflicts: [{section, current_version}]`.
  Dependencies that would modify an explicitly conflicted section are also held
  back. If all submitted sections conflict, `409` returns `{code:
  "version_conflict", detail, saved: [], conflicts}` and changes nothing.
- Invalid input returns `422 validation_error` without saving any section.
- Restore requires the current base and creates a new revision, even for an equal
  snapshot. Historical embedded IDs are retained; historical references/keys must
  still be valid against the current other sections, otherwise `422` (local choice).
  Expired or missing revisions return `404`. Retention is per section, last 50.

### Access and visibility

The permissions module resolves view/edit/manage on **every request**, without
caching: personal owner, band owner, band member, then song editor/viewer. Public
visibility does not grant access through an internal ID. No session is `401`;
no own access is `404`; own view access without action rights is `403`.
Only owners manage visibility or delete. Editors cannot smuggle visibility into
`meta` (`403`); owners must use the separate visibility route (`422` inside meta).
Readers can read revisions, but only editors restore. Revision authors and public
demo authors expose only `username` and `display_name`.

Public reads require a current public slug and recursively omit `_id`, `owner_id`,
`uploaded_by`, `author_id`, `cloudinary_public_id`, and `format`. Embedded chord IDs remain so lyrics can
resolve their shapes. No writes or history exist under `/c/`. Publishing creates a
22-character URL-safe slug; privatizing clears it; republishing creates a new one.
Other edits preserve the slug. Visibility does not version metadata.

Deleting a song physically removes its demo objects, comments, revisions,
invitations, memberships, and song document. Cloudinary deletes precede the MongoDB
transaction; a storage failure leaves DB metadata intact, but MongoDB and Cloudinary
cannot commit atomically. A failure after deleting some objects can leave their
metadata referencing missing objects; no new persistence/retry schema was invented.

### Test provenance and verification

T4 tests use exact recoverable IDs `PERM-017`, `PERM-061`, `PERM-062`, `CHD-017`,
`CHD-018`, `KEY-002`–`KEY-005`. Other approved rules use descriptive prefix + `rule`
names with decision/section provenance, not invented numeric IDs (decision 14,
A10). The permission matrix is parametrized over owner type, visibility, actor,
and action. Error tests snapshot the database; concurrency checks assert that only
the winner changes the song and creates its revision. Original numbered rows
remain unavailable. Unapproved edge-case ideas are proposals only in
`tests_md/propuesta-2026-10-30.md`.

## Bands, invitations and memberships (T5)

All routes below require Bearer + `X-Device-Id`. Band owners have implicit access;
there is no band reader role and no owner membership until ownership is transferred.
Band rename and deletion remain out of scope (A9).

| Method | Path | Body / query | Success |
| --- | --- | --- | --- |
| POST | `/bands` | `name` | `201` band |
| GET | `/bands` | — | `200` owned and joined bands |
| GET | `/bands/{id}` | — | `200` band, members/owner only |
| POST | `/invitations` | `target_type: song\|band`, `target_id`, `role` | `201` metadata + `token`, `url` |
| GET | `/invitations` | `target_type`, `target_id` | `200` metadata, editors only |
| DELETE | `/invitations/{id}` | — | `204`, creator or target owner |
| POST | `/invitations/{token}/use` | — | `201` membership |
| GET | `/bands/{id}/members` | — | `200 [{username, display_name, role}]` |
| GET | `/songs/{id}/members` | — | Same public-user projection |
| DELETE | `/bands/{id}/members/{username}` | — | `204`, owner only; `me` leaves |
| DELETE | `/songs/{id}/members/{username}` | — | `204`, owner only; `me` leaves |
| PATCH | `/songs/{id}/members/{username}` | `role: editor\|viewer` | `200 {username, display_name, role}`, owner only |
| POST | `/bands/{id}/transfer` | `username` | `200` band, current owner only |
| POST | `/songs/{id}/move` | `band_id` | `200` song, personal owner only |

Song invitation roles are required and non-null; band roles are null or omitted.
Server fields and unknown fields are rejected (`422`). Tokens are revealed only
by creation, with relative frontend URL `/i/{token}`; only SHA-256 hashes are
stored. Metadata lists omit both token and hash. `created_by` is authenticated.
Tokens allow unlimited users until `now >= expires_at`; expired, missing and
orphaned tokens return `404`. TTL cleanup is not the validity check.
`INVITATION_TTL` retains the existing positive whole-day format (`7d` default),
validated at startup. The approved unique/lookup/TTL indexes are created at startup.

Using a link with existing access returns `409 already_member`, without upgrading
or changing a membership. This includes implicit owner and band access. Concurrent
uses by one user produce one membership; distinct users can all join. Revocation
or expiry never removes existing memberships. Song links never join the band.
Only members and owners can read internal targets, even for public songs.

Membership removal, editor demotion and cascading link deletion are transactional.
Band leave/removal deletes that user's links to the band and its songs, preserving
other creators, other destinations and existing memberships. Direct song access
survives band removal. Removing/demoting a redundant song membership does not
revoke links while band access still makes that user an editor. Target writes
serialize link creation and membership changes so retries recheck permissions.
Owners cannot leave a band (`409 owner_must_transfer`); removing a nonexistent
membership (including an implicit owner) is `404`. Transfer requires an existing
band member (`422` otherwise), atomically swaps implicit ownership for an outgoing
owner membership, and preserves links. The former owner is an ordinary member.

Move supports personal to band only. Destination must be an accessible band;
nonowner callers get `403`, inaccessible bands `404`, band-source songs `422`.
Redundant direct memberships of destination-band members (including its owner)
are removed. Outsider memberships, links, visibility, slug, sections, comments and
revisions are preserved. The destination quota sums embedded demo `size_bytes`;
excess is `422 quota_exceeded` with no writes.

Local choices where sources are silent: band names are trimmed and nonempty with
no invented maximum; band/link lists sort by descending date then ID; member lists
sort by username and include the implicit owner (song role `editor`, band role null).
Member management and transfer use public usernames, not user IDs. Link metadata
listing is editor-only. The 2 GB quota is interpreted as 2 × 1024³ bytes. Coordination
updates the existing target's `updated_at` (strictly increasing by at least one
millisecond for fixed-clock concurrent operations); it creates no revision.
No new collection, field, index or MongoDB validator was introduced beyond file 05.

Tests use recoverable `INV-060`, `INV-122`, `INV-129` mappings plus descriptive
INV/PERM rule names for approved decision 06/11/14 areas where original numbered
rows are unavailable. Error assertions compare all database collections. Atomicity
checks inject failures inside real replica-set transactions; no live Maestro or
external credentials are used.

## Demos and comments (T6)

Decisions 05, 06 and 10. The audio never passes through the backend. Compression is
paused (decisions 03 and 10; author, L19): demos are stored **without transcoding**.
Confirm reads the asset from Cloudinary: `format`, `size_bytes` and `duration_s` come
from there (a client value is ignored), and `mime_type` is derived from the format
(mp3, wav, ogg, opus, flac, aac, m4a, mp4, webm). `cloudinary_public_id` and `format` never
appear in a response.

| Route | Who | Result |
| --- | --- | --- |
| `POST /songs/{id}/demos/upload-url` | editor | `{upload_url, fields}`; `fields` hold the signed values for a multipart `POST` to Cloudinary, for `erato/songs/<song_id>/<user_id>/<uuid>` |
| `POST /songs/{id}/demos` `{public_id, title?}` | editor | `201` demo. `public_id` must belong to the caller and the song, exist, and not be in use (else `404`). Not audio, over 100 MB, over 20 min or an unknown format: `422 validation_error`. Over quota: `422 quota_exceeded`. Rejected assets are destroyed |
| `PATCH /songs/{id}/demos/{demo_id}` `{title}` | editor | `200` demo; empty title `422`; the asset and revisions untouched |
| `DELETE /songs/{id}/demos/{demo_id}` | editor | `204`; deletes the Cloudinary asset first, then the demo and its comments |
| `GET /songs/{id}/demos/{demo_id}/url` | any viewer | `{url, expires_in}`; `private_download_url`, 15 minutes |
| `GET /c/{slug}/demos/{demo_id}/url` | anyone, public song only | same; `404` when the song is private |
| `GET /songs/{id}/demos/{demo_id}/comments` | any viewer | ordered by `timestamp_s` ascending |
| `GET /c/{slug}/demos/{demo_id}/comments` | anyone, public song only | authors expose only `username` and `display_name` |
| `POST /songs/{id}/demos/{demo_id}/comments` `{timestamp_s, text}` | editor | `201`; `author_id` is always the caller (a client value is ignored) |
| `PATCH .../comments/{comment_id}` | author only | `403` for anyone else; `updated_at` changes |
| `DELETE .../comments/{comment_id}` | author or owner (band owner in band songs) | `204` |

`timestamp_s` must be within `0..duration_s` inclusive; `text` is trimmed to 1..2000
characters (`422` otherwise). `demo_comments.demo_id` is an `ObjectId` (L17) serialized
as a string. The `(song_id, demo_id, timestamp_s)` index of file 05 is created at startup.

Storage is configured with `CLOUDINARY_URL`. Without it the application starts and every
storage operation answers `503 storage_unavailable`, as does any Cloudinary failure.
Audio is a `video` resource with `authenticated` delivery. Playback URLs are not cached
by the CDN and cost double bandwidth; token URLs would need the Advanced plan. Cloudinary
has no lifecycle rule, so an upload that is never confirmed stays stored.


No approved `DEMO-`/`CMT-` case exists in `decisiones/` (only DEMO-004 to DEMO-006,
which need compression), so no tests were added for this area.
