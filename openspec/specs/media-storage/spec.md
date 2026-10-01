# Media Storage Specification

## Purpose

Defines the behavioral contract for storing and delivering demo audio files via Cloudinary's free
tier (confirmed decision 4). This spec covers upload path, reference storage, and delivery — not
the demo/comment feature behavior itself (player, timestamped comments), which belongs to a future
composition-features change, and not the MongoDB schema for demo references (AGENTS.md rule 1).

## Requirements

### Requirement: Audio uploads MUST go directly from the client to the media provider, not through a backend function

Demo audio files MUST be uploaded directly from the client to Cloudinary (e.g. via a
backend-issued signed upload credential), rather than being proxied through a Vercel serverless
function body.

This requirement exists primarily to respect the Vercel Hobby 10-second execution cap: uploading an
audio file through a function would hold that function open for the duration of the transfer,
risking timeout on anything but trivially small files, and would consume function invocation time
against the free tier's usage allowance for no durable benefit.

#### Scenario: Backend issues an upload credential without receiving the file body

- GIVEN an authenticated, authorized user wants to upload a demo audio file
- WHEN the client requests permission to upload
- THEN the backend MUST issue a signed upload credential (or equivalent) scoped to that upload
- AND the backend MUST NOT receive the audio file's binary content in that request

#### Scenario: The audio file is transferred directly to the media provider

- GIVEN the client has obtained a valid upload credential
- WHEN the client uploads the audio file
- THEN the file MUST be transferred directly to Cloudinary
- AND MUST NOT pass through any Vercel serverless function during the transfer

### Requirement: Only references/metadata to externally hosted audio MUST be persisted

After a successful upload, the backend MUST persist only a reference to the externally hosted
audio (e.g. provider-issued public ID or URL, duration, uploader, timestamps) — never the audio
binary itself. This mirrors and reinforces the data-persistence specification's prohibition on
storing binaries in MongoDB.

#### Scenario: A completed upload is recorded as a reference only

- GIVEN a demo audio file has finished uploading to Cloudinary
- WHEN the backend records that the upload completed
- THEN the persisted record MUST contain only reference/metadata fields
- AND MUST NOT contain the audio binary or an encoded copy of it

### Requirement: Audio playback MUST be served without on-the-fly transformations unless explicitly required

Cloudinary's free tier allocates a single pooled credit budget across storage, bandwidth, and
transformations. The system MUST serve stored audio as-is (direct delivery URL) rather than
applying on-the-fly transformations by default, to avoid needlessly consuming the shared credit
pool.

This requirement exists to keep usage within Cloudinary's perpetual 25-credit free allowance,
which directly supports the zero-recurring-cost constraint: unnecessary transformation usage could
exhaust the pooled credits and force a paid upgrade.

#### Scenario: Default playback uses the stored file directly

- GIVEN a demo audio file has been uploaded and stored
- WHEN a user plays that demo
- THEN the system MUST serve the file via its direct delivery URL
- AND MUST NOT invoke an on-the-fly Cloudinary transformation unless a specific, justified feature
  requires it

### Requirement: Upload MUST be rejected for unauthorized or unauthenticated requests

Issuing an upload credential is itself a protected action. Only an authenticated user with edit
rights on the target composition MUST be able to obtain one.

#### Scenario: An unauthenticated request for an upload credential is rejected

- GIVEN a request for an upload credential has no valid JWT
- WHEN the backend processes it
- THEN the backend MUST reject the request with a 401 status code
- AND MUST NOT issue an upload credential

#### Scenario: An authenticated but non-invited user cannot obtain an upload credential for a composition

- GIVEN an authenticated user has no edit rights on the target composition (not invited, or
  viewing a public composition without an invitation)
- WHEN that user requests an upload credential for a demo under that composition
- THEN the backend MUST reject the request with a 403 status code
- AND MUST NOT issue an upload credential
