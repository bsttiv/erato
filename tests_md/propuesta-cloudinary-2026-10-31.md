# Additional test proposals — Cloudinary storage, 2026-10-31

Approved by the author on 2026-10-31 and implemented in `backend/tests/test_demos.py`, `backend/tests/test_songs.py` and `frontend/src/api/demos.spec.ts`.

`tests_md/demos.md`, listed in `tests_md/README.md`, does not exist, and `backend/tests/` has no upload, playback or demo deletion tests. These cases therefore define that coverage instead of adapting it.

Cloudinary is always faked in automated tests. The fake records every call and can be forced to fail. Each error case also asserts that MongoDB did not change.

The `public_id` value is `erato/songs/<song_id>/<user_id>/<uuid>`. It replaces the path in the approved sample document because the confirmation rule needs the song and the uploader in the identifier. The schema is unchanged.

## Backend — upload

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-001 | Editor of a song | Request an upload | `200` with the `video/upload` URL and `fields` holding `api_key`, `timestamp`, `signature`, `public_id`, `type: authenticated` and `overwrite: false`; the secret appears nowhere in the response |
| CLD-002 | The response of CLD-001 | Recompute the signature from the returned fields | It matches `signature` |
| CLD-003 | `viewer` of the song | Request an upload | `403`; nothing signed |
| CLD-004 | Uploaded asset; client sends another duration and size | Confirm | `201`; the demo stores `cloudinary_public_id`, `format`, `mime_type`, `size_bytes` and `duration_s` as read from Cloudinary; no `r2_key` |
| CLD-005 | `public_id` of another user or another song | Confirm | `404 not_found`; the asset is not touched |
| CLD-006 | `public_id` that does not exist | Confirm | `404 not_found` |
| CLD-007 | Asset with no audio | Confirm | `422 validation_error`; asset destroyed; no metadata |
| CLD-008 | Asset over 100 MB, or over 20 minutes | Confirm | `422 validation_error`; asset destroyed; no metadata |
| CLD-009 | Audio in a format outside the accepted list | Confirm | `422 validation_error`; asset destroyed; no metadata |
| CLD-010 | Owner at the 2 GB quota, with a member uploading to a band song | Confirm | `422 quota_exceeded`; the band's usage is the one counted; asset destroyed; no metadata |
| CLD-011 | MongoDB fails while saving the demo | Confirm | Error; asset destroyed; no metadata |

## Backend — playback

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-020 | Member of the song | Request the playback URL | `private_download_url` called with `resource_type: video`, `type: authenticated`, the stored `format` and an expiry 900 s away; response has `url` and `expires_in: 900` |
| CLD-021 | Anonymous visitor of a public song | Request the URL through `/c/{slug}` | Same URL shape; the response body has no `cloudinary_public_id` field |
| CLD-022 | Song turned private again | Request the URL through `/c/{slug}` | `404`; no URL issued |
| CLD-023 | Song responses, signed in and public | Read the song | No response includes `cloudinary_public_id` or `format` |

## Backend — deletion

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-030 | Demo with comments | Delete it | `204`; `destroy` called with `resource_type: video` and `type: authenticated` before MongoDB changes; demo and comments removed |
| CLD-031 | Cloudinary fails | Delete the demo | Error; the demo and its comments remain |
| CLD-032 | Song with two demos | Delete the song | Both assets destroyed, then the song removed |
| CLD-033 | Cloudinary fails on the second demo | Delete the song | Error; the song and all its metadata remain |
| CLD-034 | Asset already gone, after a partial failure | Delete again | Cloudinary's `not found` counts as deleted; the operation completes |

## Backend — configuration

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-040 | `CLOUDINARY_URL` not set | Start the application | It starts |
| CLD-041 | `CLOUDINARY_URL` not set | Request an upload or a playback URL | `503 storage_unavailable`; nothing changes |

## Frontend

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-101 | Upload target with `fields` | Upload a file | Multipart `POST` carrying every field plus `file`; progress moves from 0 to 1; the demo is then confirmed with `public_id` |
| CLD-102 | Cloudinary rejects the upload | Upload a file | The existing storage message is shown; no confirmation is sent |
| CLD-103 | Server answers `storage_unavailable` | Request an upload | Shows `Las demos no están disponibles en este momento.` |

## Approved cases that change

| ID | Change | Reason |
| --- | --- | --- |
| INFRA-020 to INFRA-024 | Removed | They test the SeaweedFS bucket, which leaves the stack |
| Song cascade delete in `test_songs.py` | Covered by CLD-032 | It used the local bucket |
| Hidden fields in `test_songs.py` | Check `cloudinary_public_id` instead of `r2_key` | The field was renamed |
| LAPP-012 | Names Cloudinary instead of R2 | The legal page must name the real provider |
| Fixtures in `tests_md/README.md` | `r2` and MinIO replaced by the Cloudinary fake | Automated tests no longer use a local bucket |

## Manual check with a real account

Not automated. It runs once before closing, using credentials from the author:

1. Upload an audio file and read the fields Cloudinary returns.
2. Play it and seek forwards and backwards with a `private_download_url`.
3. Confirm the URL stops working after it expires.
4. Check whether the legacy public assets can move to `authenticated`.

If seeking fails, the playback decision returns to the author.

## Additional cases approved by the author on 2026-10-31

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-013 | `public_id` with a valid prefix that does not end in a UUID, such as `<prefix>/../<uuid>` | Confirm | `404 not_found`; Cloudinary is not called |
| CLD-104 | Server answers `storage_unavailable` | Play, rename or delete a demo | Shows `Las demos no están disponibles en este momento.` |
| CLD-012 | Demo already confirmed | Confirm the same `public_id` again | `404 not_found`; no second demo; the asset is not destroyed |

## Real Admin API metadata — approved by the author on 2026-10-31

The authorized synthetic WAV check showed that `cloudinary.api.resource(..., media_metadata=True)` returns flattened audio fields (`has_audio`, `audio_codec`, `audio_duration`) without an `audio` object. The Upload API response does include `audio`. Using `image_metadata=True` produced the same flattened Admin response. The current fake models the Upload response instead of the Admin response; `valid_audio` consequently rejected the valid real WAV.

Reference: [Cloudinary Admin API](https://cloudinary.com/documentation/admin_api#get_details_of_a_single_resource_by_public_id). No real account identifiers or credentials belong in fixtures.

| ID | Setup | Action | Expected |
| --- | --- | --- | --- |
| CLD-014 | Fake Admin response uses flattened metadata with `has_audio: true`, valid format, bytes and duration, and no `audio` object | Confirm through the API | `201`; demo saved using authoritative format, size and duration; asset preserved |

Approved correction: validate audio presence using Admin's `has_audio` boolean, not Upload's `audio` object. Update the fake and CLD-007's no-audio cases to use `has_audio: false` or a missing `has_audio`; they must still return `422`, destroy the rejected asset and leave MongoDB unchanged. Keep all other approved limits, quota and error behavior unchanged. This changes neither MongoDB fields nor the public API.
