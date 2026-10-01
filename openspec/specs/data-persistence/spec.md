# Data Persistence Specification

## Purpose

Defines the connection and operational contract between Erato's backend and MongoDB Atlas M0
(confirmed decision 2) under a serverless execution model. This spec is explicitly about
*connection behavior*, not the data model: collections, field names, indexes, and relationships
are out of scope and require a separate, explicit author approval per AGENTS.md rule 1.

## Requirements

### Requirement: The backend MUST reuse a single database client across warm serverless invocations

Vercel serverless functions may reuse a "warm" process across invocations. MongoDB Atlas M0 caps
concurrent connections at approximately 500. The backend MUST NOT open a new database connection
on every invocation; it MUST reuse a module-level (or equivalent warm-scope) client when the
runtime is warm, opening a new connection only on a cold start.

This requirement exists to keep the solution within Atlas M0's perpetual free tier: exhausting the
500-connection cap would force an upgrade to a paid tier, violating the zero-recurring-cost
constraint.

#### Scenario: Consecutive requests on a warm instance reuse the same connection

- GIVEN the serverless instance has already handled at least one request and is warm
- WHEN another request requiring database access arrives on that same warm instance
- THEN the backend MUST reuse the existing database client/connection
- AND MUST NOT establish a new connection for that request

#### Scenario: A cold start establishes exactly one new connection

- GIVEN a serverless instance is starting cold (no existing client in scope)
- WHEN the first request requiring database access arrives
- THEN the backend MUST establish a new database connection
- AND MUST store it in warm-reusable scope for subsequent invocations on that instance

### Requirement: Database operations MUST fail explicitly and structurally on connection failure

Given Atlas M0's auto-pause behavior and connection/op-rate limits, the backend MUST handle
connection or query failures as recoverable, structured errors rather than crashing the process or
returning an ambiguous response.

#### Scenario: A database connection failure returns a structured error

- GIVEN the database is unreachable (e.g. paused, network failure, or connection limit reached)
- WHEN a handler attempts a database operation
- THEN the backend MUST catch the failure and return a structured 5xx error to the client
- AND MUST NOT leak raw driver exception internals in the response body

#### Scenario: A paused Atlas M0 cluster resumes on the next request without manual intervention

- GIVEN the Atlas M0 cluster has auto-paused due to 30 days of inactivity
- WHEN a new request requiring database access arrives
- THEN the connection attempt MUST trigger the cluster's auto-resume behavior (Atlas-native) and
  either succeed once resumed, or return a structured "temporarily unavailable" error if resume
  has not completed within the handler's execution budget

### Requirement: Audio binary data MUST NOT be stored in MongoDB

Per the demo-audio decision (decision 4), audio files are stored in an external media provider
(Cloudinary). MongoDB MUST only ever store references/metadata pointing at externally hosted
audio, never the binary audio data itself.

This requirement exists because Atlas M0's 512MB storage cap would be exhausted almost immediately
by audio binaries, breaking the zero-recurring-cost constraint by forcing a paid tier upgrade.

#### Scenario: Storing a demo reference does not include binary audio content

- GIVEN a demo audio file has been uploaded to the external media provider
- WHEN the backend persists a record referencing that demo
- THEN the persisted document MUST contain only reference/metadata fields (e.g. external URL or
  identifier, duration, uploader, timestamps)
- AND MUST NOT contain the raw audio binary or a base64-encoded copy of it

### Requirement: This specification MUST NOT define collections, fields, or indexes

Per AGENTS.md rule 1, the MongoDB schema (collections, field names, types, indexes, relationships,
validation rules) requires a separate, explicit author-approved proposal. This spec describes
connection and operational behavior only.

#### Scenario: Implementation work referencing this spec defers schema design

- GIVEN a developer or agent implements the connection-reuse behavior described above
- WHEN they need to persist or query actual composition/demo/user data
- THEN they MUST reference a separately approved schema proposal for field/collection design
- AND MUST NOT invent or lock in schema structure based on this spec alone
