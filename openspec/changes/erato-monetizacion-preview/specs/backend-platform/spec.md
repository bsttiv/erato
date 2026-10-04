# Delta for Backend Platform

Repo: `erato`.

## ADDED Requirements

### Requirement: New environment settings MUST be documented and fail closed

Every new setting introduced by this change (media folder prefix, base URL for links, and any
feature flag the core reads) MUST be documented in `.env.example` with no real values and with the
owning repo noted. A feature flag that is unset MUST resolve to disabled. A missing required setting
MUST fail with a clear structured error.

#### Scenario: Documented

- GIVEN `.env.example`
- WHEN compared with the settings the code reads
- THEN every setting MUST appear without a real value

#### Scenario: Unset flag

- GIVEN a feature flag is not set
- WHEN the app evaluates it
- THEN the feature MUST be disabled

#### Scenario: Link base missing

- GIVEN the base URL setting is absent and an invitation link is requested
- WHEN the backend builds the link
- THEN it MUST fail with a structured error naming the setting
- AND MUST NOT derive the base from the request host header

### Requirement: The app MUST stay importable as app.main.app and accept host extensions

The application object MUST remain importable as `app.main.app` and MUST allow a host to include
additional routers and install dependency overrides after import, without modifying core files.

#### Scenario: Host extension

- GIVEN a host module that imports `app.main.app`, includes a router and overrides `get_plan_policy`
- WHEN a request hits the new route and a gated core route
- THEN the router MUST respond and the override MUST be honored

#### Scenario: Serverless entry unchanged

- GIVEN `api/index.py`
- WHEN imported
- THEN it MUST expose the same app object as `app.main.app`
