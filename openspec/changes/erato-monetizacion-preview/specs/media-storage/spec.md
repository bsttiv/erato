# Delta for Media Storage

Repo: `erato`. The limit values come from `PlanPolicy`; under the default policy there is no quota.

## ADDED Requirements

### Requirement: Upload credentials MUST be refused when the demo count quota is reached

Before issuing an upload credential the backend MUST ask `PlanPolicy` for the demo limit of the
composition. When the composition's current demo count is at or above a non-null limit, the backend
MUST respond 403 with a machine-readable demo-limit code and MUST NOT issue a credential. A null
limit means no quota. The quota is per composition and counts existing demos only.

#### Scenario: Below the limit

- GIVEN a limit of 20 and a composition with 19 demos
- WHEN an editor requests an upload credential
- THEN the credential MUST be issued

#### Scenario: At the limit

- GIVEN a limit of 1 and a composition with 1 demo
- WHEN an editor requests an upload credential
- THEN the backend MUST respond 403 with the demo-limit code and issue nothing

#### Scenario: Unlimited default

- GIVEN `UnlimitedPlanPolicy`
- WHEN an editor requests a credential on a composition with many demos
- THEN it MUST be issued

#### Scenario: Authorization precedes the quota

- GIVEN a user with no edit rights and a composition over quota
- WHEN they request a credential
- THEN the response MUST be the authorization failure, not the quota code

#### Scenario: Audio stays on Cloudinary under the preview prefix

- GIVEN the preview environment
- WHEN an upload credential is issued
- THEN it MUST target Cloudinary with the configured preview folder prefix
