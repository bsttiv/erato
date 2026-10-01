# Backend Platform Specification

## Purpose

Defines the behavioral contract for Erato's Python backend running as serverless functions on
Vercel (FastAPI, per confirmed decision 1). This spec covers request/response handling, environment
configuration, execution-time budget, and the standing requirement that authorization is enforced
server-side on every request. It does not define any specific feature endpoint (compositions, demos,
etc.) — those belong to their own future changes — nor any MongoDB schema (AGENTS.md rule 1).

## Requirements

### Requirement: Backend requests MUST return a structured, typed response

The backend MUST expose HTTP endpoints that validate incoming request data against a declared
schema before executing any handler logic, and MUST return a structured response (success payload
or structured error) rather than an unhandled exception or raw stack trace.

#### Scenario: Valid request is accepted

- GIVEN a client sends a request whose body matches the endpoint's declared schema
- WHEN the backend receives the request
- THEN the handler executes and returns a structured success response with an appropriate HTTP
  status code

#### Scenario: Invalid request is rejected before handler logic runs

- GIVEN a client sends a request whose body does not match the endpoint's declared schema (e.g.
  missing required field, wrong type)
- WHEN the backend receives the request
- THEN the backend MUST reject the request with a 4xx status code and a structured error body
  describing the validation failure
- AND the handler's business logic MUST NOT execute

#### Scenario: Unhandled server error does not leak internals

- GIVEN a request triggers an unexpected server-side error
- WHEN the backend returns a response
- THEN the response MUST be a structured 5xx error body
- AND the response MUST NOT include a raw stack trace, internal file paths, or internal exception
  messages

### Requirement: Every authorization-sensitive endpoint MUST validate permissions server-side

Per AGENTS.md ("Compartir"): permissions and visibility rules MUST be validated in the backend on
every request that reads or mutates composition data. The frontend MAY hide controls for
convenience, but MUST NOT be the sole enforcement point.

#### Scenario: Backend rejects an unauthorized mutation regardless of frontend state

- GIVEN a request attempts to modify a resource the requester is not authorized to edit
- WHEN the backend processes the request, independent of any frontend-side button visibility
- THEN the backend MUST reject the request with a 403 (or equivalent) status code
- AND no data MUST be modified

#### Scenario: Backend rejects an unauthorized read of a private resource

- GIVEN a request attempts to read a resource marked private
- WHEN the requester is not an invited user and is not authenticated as one
- THEN the backend MUST reject the request with a 403 or 404 status code
- AND the response body MUST NOT include the resource's data

### Requirement: Handlers MUST respect the serverless execution-time budget

The deploy platform (Vercel Hobby tier) enforces a hard execution cap per invocation. Every handler
MUST be designed to complete, or to fail fast, well within that cap, and MUST NOT perform
synchronous, long-running work (e.g. media transcoding, bulk processing) in-process.

This requirement exists to fit the zero-recurring-cost constraint: the Hobby tier is the only
perpetual free compute option, and it enforces this cap unconditionally.

#### Scenario: A handler performing only data CRUD completes well inside the budget

- GIVEN a request to create, read, update, or delete a composition-related resource
- WHEN the handler executes
- THEN the handler MUST complete (success or structured error) without relying on synchronous
  processing of large payloads (e.g. transcoding an uploaded audio file in-process)

#### Scenario: A handler never defers heavy media processing into a Vercel function

- GIVEN a feature requires audio processing (e.g. transcoding, waveform generation)
- WHEN that feature is implemented
- THEN the processing MUST occur outside the Vercel function (e.g. in the external media provider)
  rather than synchronously inside the handler

### Requirement: Environment configuration MUST be externalized, never hardcoded or committed

Per AGENTS.md rule 4, credentials, connection strings, and keys MUST be read from environment
variables and MUST be documented in `.env.example` without real values.

#### Scenario: Backend reads required configuration from environment variables

- GIVEN the backend needs a secret (e.g. database connection string, JWT signing key, media
  provider credentials)
- WHEN the application starts or the relevant handler runs
- THEN the value MUST be read from an environment variable
- AND no real secret value MUST appear in source code or version control

#### Scenario: Missing required configuration fails fast with a clear error

- GIVEN a required environment variable is absent at startup or first use
- WHEN the backend attempts to use it
- THEN the backend MUST fail with a clear, structured error identifying the missing configuration
  rather than failing silently or with an unrelated error later
