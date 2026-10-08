# Erato Preview Deployment Runbook

This runbook documents the configuration, operations, promotion order, and rollback procedures for the `erato` and `erato-cloud` preview deployment environment.

> **CRITICAL**: Promotion and rollback steps are documented here for operational readiness. **They MUST NOT be executed** as part of this change unit.

---

## 1. Branch Strategy & Git Submodule Rules

- **Dedicated `preview` Integration Branches**:
  - `erato` repository: long-lived branch `preview`.
  - `erato-cloud` repository: long-lived branch `preview`.
  - The `main` branch in both repositories must remain untouched until formal promotion.
- **Git Submodule Pointer**:
  - `erato-cloud` includes `erato` as a git submodule at path `erato`.
  - While operating in preview, `erato-cloud`'s submodule MUST track the HEAD of `erato`'s `preview` branch.
  - Verification check before preview testing:
    ```bash
    # Run in erato-cloud after the operator refreshes origin/preview in the submodule.
    git submodule status erato
    git ls-tree HEAD erato
    git -C erato rev-parse HEAD
    git -C erato rev-parse origin/preview
    # All recorded/core HEAD SHAs must equal the refreshed origin/preview SHA.
    ```

- **Preview pointer-bump order**: merge the required public unit into `erato` `preview` first;
  then bump the `erato-cloud` gitlink in its dependent PR, run cloud CI against that pin,
  merge into cloud `preview`, and verify the SHAs before deployment testing.

---

## 2. Vercel Projects Setup

The deployment is split across two Vercel projects:

### Project A: `erato-cloud` (Application & API)
- **Repository**: `erato-cloud`
- **Tracked Branch**: `preview`
- **Root Directory**: `.`
- **Build & Serverless Functions**:
  - Serves the unified SPA and API via `api/index.py` (extended FastAPI app).
  - Pinned core dependencies and cloud router extensions are bundled together.

### Project B: `erato-landing` (Standalone Landing Page)
- **Repository**: `erato`
- **Tracked Branch**: `preview`
- **Root Directory**: `landing`
- **CRITICAL SETTING**: In **Vercel Project Settings > General > Root Directory**, enable the checkbox:
  - **"Include source files outside of the Root Directory in the Build Step"**
  - *Rationale*: The landing build references shared design system tokens and Vue components located in `../erato-design-system` and `../frontend/src/design-system`.
- **Root Configuration Integrity**:
  - The root `vercel.json` and its regression tests (`tests/test_vercel_config.py`) belong exclusively to the main web app and must never be altered for the landing.
  - The landing project uses its own isolated configuration inside `landing/vercel.json`.

---

## 3. Access Control & Search Engine Indexing

- **Deployment Protection**:
  - Must be **DISABLED (OFF)** for Preview deployments in both Vercel projects.
  - *Rationale*: Public compositions and shareable invitation links (`/invite/<token>`) must be accessible to anonymous visitors without hitting a Vercel SSO/authentication wall.
- **Search Engine Isolation (`noindex`)**:
  - All preview deployments must carry `noindex` directives to prevent test URLs from appearing in search engine indexes.
  - Frontend / Landing: Injected `<meta name="robots" content="noindex">` tag via Vite build plugin when `VERCEL_ENV !== 'production'`.
  - Backend API: `X-Robots-Tag: noindex` response headers on preview environments.

---

## 4. Environment Variables Matrix

All variables must isolate preview data from production. No production credentials or databases may be accessed by preview.

| Variable Name | Owning Repository | Preview Setting | Production Setting | Notes |
|---|---|---|---|---|
| `MONGODB_URI` | `erato` | Cluster URI | Cluster URI | Same MongoDB Atlas cluster, isolated DB |
| `MONGODB_DB` | `erato` | `erato_preview` | `erato` | Isolated database instance |
| `JWT_SECRET` | `erato` | Preview-unique secret | Production secret | Separate signing key (rejects prod JWTs) |
| `ACCESS_TOKEN_TTL_MINUTES` | `erato` | `15` | `15` | Default session lifespan |
| `REFRESH_TOKEN_TTL_DAYS` | `erato` | `30` | `30` | Rotating cookie lifespan |
| `INVITE_TOKEN_TTL_DAYS` | `erato` | `14` | `14` | Invitation link expiration |
| `CLOUDINARY_CLOUD_NAME` | `erato` | Cloudinary name | Cloudinary name | Storage account |
| `CLOUDINARY_API_KEY` | `erato` | API key | API key | Upload credentials |
| `CLOUDINARY_API_SECRET` | `erato` | API secret | API secret | Upload credentials |
| `CLOUDINARY_FOLDER_PREFIX` | `erato` | `erato-preview` | `erato` | Asset separation in media bucket |
| `APP_BASE_URL` | `erato` | `https://<preview-alias>.vercel.app` | `<production-url>` | Fails closed if unset. Never host-derived |
| `VITE_APP_URL` | `erato` (landing) | `https://<preview-alias>.vercel.app` | `<production-url>` | Points CTAs from landing to web app |
| `FREE_PRO_ENABLED` | `erato-cloud` | `true` (Preview only) | **UNSET / false** | Feature gate for preview tier testing |
| `VERCEL_ENV` | Platform | `preview` | `production` | Injected by Vercel platform |

> [!WARNING]
> `FREE_PRO_ENABLED` MUST NEVER be enabled in Production. Even if set by mistake, the application includes a `VERCEL_ENV === "production"` guard that refuses to activate free Pro.

---

## 5. Database Bootstrap & Idempotent Indexes

The preview database starts empty. These are operator procedures, not commands to run in DOC.
Use a trusted preview connection and required settings supplied by the operator; run core modules
from the `erato` root. Only `erato_preview` is permitted here; never use production `erato`.

**Ordering prerequisite:** deploy the removal of legacy composition invitation routes and redemption
(F3.2b, already merged) **before** migrating, so old code cannot recreate legacy permissions.
Pause writes during migration/restore and retain the backup securely outside the deployment.

```bash
# 1. Inspect IDs without mutations or backup creation.
MONGODB_DB=erato_preview python -m scripts.migrate_bands
# 2. Only if legacy data is reported and the operator authorizes apply:
MONGODB_DB=erato_preview python -m scripts.migrate_bands --apply --confirm-db erato_preview
# 3. Bootstrap core indexes even when migration reports "nada que migrar".
MONGODB_DB=erato_preview python -m scripts.ensure_indexes
```

Apply refuses a missing/mismatched `--confirm-db`; the scripts themselves do not restrict the name
to preview. Selection: null/absent `band_id` with nonempty `members`, and invitations with
`composition_id` but no `target`. Apply fsyncs canonical Extended JSON to
`backups/migrate_bands-<UTC>.json` before clearing members and deleting those invitations.
It replaces the legacy invitation index with the target index. With no selected documents it
returns "nada que migrar" without touching indexes. Repeated apply is a no-op after success.

Run the cloud bootstrap from its own root after C1 is available:
`MONGODB_DB=erato_preview python -m scripts.ensure_cloud_indexes` (host-owned; not verified in DOC).
Core indexes are explicit, idempotent operations, never startup work. A detached cloud leaves
core running with `UnlimitedPlanPolicy`.

### Restore a migration backup

```bash
MONGODB_DB=erato_preview python -m scripts.restore_bands_migration --backup 'backups/migrate_bands-<UTC>.json' --confirm-db erato_preview
```

Use the exact retained backup filename. Restore sets backed-up composition members, reinserts
invitations by original `_id` (duplicate keys are ignored), and recreates
`idx_invitations_composition_id`; it does not remove `idx_invitations_target`, recreate deleted
compositions, or restore later edits. Restored invitations remain unusable under F3.2b code;
restore data together with a compatible code/pointer rollback before resuming writes.

---

## 6. Promotion Procedure (Documented — DO NOT EXECUTE)

When the preview verification phase is complete and signed off:

1. **Step 1: Merge Core to Main**:
   - Merge `erato` branch `preview` into `main` via PR.
   - Run the full test suites locally.
2. **Step 2: Update Cloud Submodule**:
   - In `erato-cloud`, fetch and checkout the new `main` commit of `erato`:
     ```bash
     cd erato && git checkout main && git pull
     cd .. && git add erato
     git commit -m "chore: actualiza el submodulo erato a main"
     ```
3. **Step 3: Merge Cloud to Main**:
   - Merge `erato-cloud` branch `preview` into `main` via PR.
4. **Step 4: Verify Production Settings**:
   - Confirm in Vercel project settings that `FREE_PRO_ENABLED` is NOT set in Production scope.
   - Confirm production database name remains `erato`.

---

## 7. Rollback Procedure (Documented — DO NOT EXECUTE)

In the event of a critical failure or regression during preview testing:

1. **Rollback Preview Database**:
   - Drop the `erato_preview` database:
     ```bash
     mongosh "<cluster-uri>/erato_preview" --eval "db.dropDatabase()"
     ```
   - Re-run core and, once available, cloud bootstraps from section 5 for a clean slate.
   - To preserve legacy data instead, pause writes and use the backup restore procedure above.
     Choose restore or database reset; dropping the database discards all preview data.
2. **Rollback Index Changes (Documents Retained)**:
   - To remove newly added indexes without dropping existing collections:
     ```bash
     MONGODB_URI="<cluster-uri>" MONGODB_DB="erato_preview" python -m scripts.ensure_indexes --rollback
     ```
   - `--rollback` has no `--confirm-db` guard. It drops only `idx_bands_owner_id`,
     `idx_bands_members_user_id`, `idx_compositions_band_id`, `idx_invitations_target`, and
     `uq_section_revisions_comp_section_rev`; absent indexes are tolerated. It does not restore
     the legacy index or data. Restore legacy data/index via the backup script when required.
3. **Rollback Submodule Pointer**:
   - Revert the submodule commit in `erato-cloud` to the prior working commit:
     ```bash
     git revert <submodule-bump-commit>
     ```
   - Restore the previous compatible deployment and rerun the pointer check against the chosen
     rollback commit (a rollback pin intentionally differs from current preview HEAD).
4. **Rollback Feature Flags**:
   - If `FREE_PRO_ENABLED` causes issues or was misconfigured, remove or set the variable to `false` in the Vercel dashboard and redeploy.

---

## 8. Landing Page Operations & Configuration

### Running the Landing Locally
To run and develop the standalone landing page locally on port `5174`:
```bash
cd landing
npm install
npm run dev
```
The landing dev server runs on `http://localhost:5174` (configured via `server.port = 5174` in `landing/vite.config.ts`) avoiding port collisions with the main app (`http://localhost:5173`).

To execute the test suite and verify the build:
```bash
cd landing
npm run test:unit
npm run build
```

### Application URL Resolution (`VITE_APP_URL`) & Fail-Closed Behavior
The landing page points all registration and login CTAs to the main web app:
- **Production (`VERCEL_ENV === 'production'`)**: `VITE_APP_URL` is **mandatory** and fail-closed. If `VITE_APP_URL` is unset or empty during a production build, Vite aborts immediately with an explicit error:
  `VITE_APP_URL is required in production (VERCEL_ENV === "production") and must not be empty.`
- **Development & Preview**: When `VITE_APP_URL` is omitted, `resolveAppUrl` automatically defaults to the local development app `http://localhost:5173`.
- **Sanitization**: Any trailing slashes (`/`) are stripped to prevent double-slash artifacts in CTA links (`/login`, `/register`).

### Search Engine Protection (`noindex`)
The landing Vite configuration (`landing/vite.config.ts`) includes a `transformIndexHtml` plugin (`noindexPlugin`) that controls robots indexing:
```html
<meta name="robots" content="noindex">
```
- **Preview & Local Environments**: When `process.env.VERCEL_ENV !== 'production'`, the plugin injects `<meta name="robots" content="noindex">` into `<head>`. This prevents preview deployments and local development artifacts from being indexed.
- **Production Environment**: When `process.env.VERCEL_ENV === 'production'`, the meta tag is omitted so the marketing site can be indexed properly.
- **Root Configuration Integrity**: This ensures preview indexing isolation entirely at build time in `landing/vite.config.ts` without altering the root `vercel.json` or affecting backend serverless routes.

