# Preview Deployment Specification

Repo: both (`erato` and `erato-cloud`). Everything is Vercel Preview only; production and the
production database are untouched.

## Purpose

Defines how the preview environment is assembled and isolated: branches, Vercel projects,
environment separation, index bootstrap and the guards that keep free Pro out of production.

## Requirements

### Requirement: Each repository MUST have a long-lived preview branch

`erato` and `erato-cloud` MUST each have a `preview` integration branch. `main` in both MUST NOT
receive this change's work. `erato-cloud`'s submodule MUST track `erato`'s `preview` branch.

#### Scenario: Main untouched

- GIVEN the change is fully applied
- WHEN `main` of both repos is compared with its pre-change state
- THEN they MUST be identical

#### Scenario: Pointer rule

- GIVEN the preview is about to be tested
- WHEN the submodule pointer is compared with `erato` `preview` HEAD
- THEN they MUST be equal, as a documented runbook check

### Requirement: App and API MUST deploy as one Vercel project from erato-cloud

The full preview (frontend and API) MUST be served by a Vercel project built from `erato-cloud`'s
`preview` branch, with `api/index.py` exposing the extended app. Cloud CI MUST check out submodules
recursively and run its tests (with a MongoDB service) against the pinned submodule.

#### Scenario: Extended app

- GIVEN the deployed preview
- WHEN a cloud route and a core route are requested
- THEN both MUST be served by the same application

#### Scenario: CI uses the pinned core

- GIVEN a pull request in `erato-cloud`
- WHEN CI runs
- THEN it MUST fetch the submodule at the pinned commit and run the cloud tests

### Requirement: Preview environment variables MUST isolate data and secrets

Preview-scoped variables in the `erato-cloud` project MUST set: database name `erato_preview` on the
same cluster, its own `JWT_SECRET`, media folder prefix `erato-preview`, `APP_BASE_URL` equal to the
stable alias of that project's `preview` branch, and `FREE_PRO_ENABLED`. Each repository's
`.env.example` MUST document every variable and which repo owns it, without real values. The preview
database MUST start empty.

#### Scenario: Data isolation

- GIVEN the preview deployment
- WHEN it writes data
- THEN writes MUST go to `erato_preview` only

#### Scenario: Separate signing key

- GIVEN a token signed with the production secret
- WHEN presented to the preview
- THEN it MUST be rejected

#### Scenario: Media prefix

- GIVEN a demo uploaded in preview
- WHEN its storage path is inspected
- THEN it MUST be under the `erato-preview` prefix

#### Scenario: Invite links

- GIVEN a band invitation created in preview
- WHEN the link is inspected
- THEN it MUST start with the configured `APP_BASE_URL`

### Requirement: The landing MUST deploy as its own Vercel project from erato

The landing MUST be a separate Vercel project built from `erato` (`preview` branch for this change),
with its own `landing/vercel.json`; the root `vercel.json` of `erato` and its test MUST remain
unchanged. `VITE_APP_URL` MUST point to the `erato-cloud` preview alias. The build MUST be able to
read the design system and frontend sources outside its root directory.

#### Scenario: Landing build

- GIVEN the landing project settings
- WHEN it builds on Vercel
- THEN it MUST succeed resolving sources outside `landing/`

#### Scenario: Root config unchanged

- GIVEN the final diff
- WHEN the root `vercel.json` and its test are inspected
- THEN neither MUST be modified

### Requirement: Preview deployments MUST allow anonymous access and be non-indexable

Deployment Protection MUST be disabled for the preview of the app project and the landing project so
anonymous public links and the landing work. Preview responses MUST carry `noindex`.

#### Scenario: Anonymous public link

- GIVEN a public composition in preview
- WHEN an anonymous visitor opens its link
- THEN it MUST render without a Vercel login wall

#### Scenario: Noindex

- GIVEN any preview page
- WHEN its headers or meta tags are inspected
- THEN `noindex` MUST be present

### Requirement: Indexes MUST be bootstrapped for core and cloud collections

Core indexes MUST be created by `erato`'s index script (including bands, composition band id,
invitation target, section revisions) and cloud indexes by `erato-cloud`'s own bootstrap, both
against the preview database name. Both MUST be idempotent. The core script MUST provide a matching
rollback drop list.

#### Scenario: Core indexes

- GIVEN an empty preview database
- WHEN the core script runs
- THEN the approved indexes MUST exist

#### Scenario: Rollback

- GIVEN indexes created by the scripts
- WHEN the drop list is applied
- THEN the indexes added by this change MUST be removed

### Requirement: Free Pro MUST NOT be reachable in production

Production configuration MUST NOT enable free Pro. A runbook checklist MUST verify
`FREE_PRO_ENABLED` is scoped to Preview only, and the free provider's production guard MUST hold
regardless.

#### Scenario: Wrong scope

- GIVEN the flag is mistakenly set in Production scope
- WHEN a user activates
- THEN the free provider MUST refuse because of the `VERCEL_ENV` guard

#### Scenario: Unset means disabled

- GIVEN the flag is unset
- WHEN the app starts
- THEN free Pro MUST be disabled

### Requirement: Promotion and rollback MUST be documented, not executed

A runbook MUST document promotion order (`erato` to `main`, then `erato-cloud` with the pointer
bump), the table of variables per Vercel project, the guard for the existing production project, and
rollback (drop the preview database and rerun bootstraps; unset the flag; revert the pointer bump).
This change MUST NOT perform promotion or production migration.

#### Scenario: Runbook content

- GIVEN the runbook
- WHEN reviewed
- THEN it MUST contain the promotion order, the variable table, the pointer check and the rollback steps

#### Scenario: Core works without cloud

- GIVEN `erato-cloud` is paused or deleted
- WHEN `erato` is deployed alone
- THEN it MUST run with `UnlimitedPlanPolicy` and all features available
