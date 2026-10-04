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
  - `erato-cloud` includes `erato` as a git submodule (at `core/` or repo root reference).
  - While operating in preview, `erato-cloud`'s submodule MUST track the HEAD of `erato`'s `preview` branch.
  - Verification check before preview testing:
    ```bash
    git submodule status
    # Confirm submodule commit matches git rev-parse origin/preview of erato
    ```

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
| `APP_BASE_URL` | `erato` | `https://<preview-alias>.vercel.app` | `https://erato.vercel.app` | Fails closed if unset. Never host-derived |
| `VITE_APP_URL` | `erato` (landing) | `https://<preview-alias>.vercel.app` | `https://erato.vercel.app` | Points CTAs from landing to web app |
| `FREE_PRO_ENABLED` | `erato-cloud` | `true` (Preview only) | **UNSET / false** | Feature gate for preview tier testing |
| `VERCEL_ENV` | Platform | `preview` | `production` | Injected by Vercel platform |

> [!WARNING]
> `FREE_PRO_ENABLED` MUST NEVER be enabled in Production. Even if set by mistake, the application includes a `VERCEL_ENV === "production"` guard that refuses to activate free Pro.

---

## 5. Database Bootstrap & Idempotent Indexes

The preview database (`erato_preview`) starts completely empty and is prepared using idempotent migration and index scripts:

1. **Bootstrap Core Indexes**:
   ```bash
   MONGODB_URI="<cluster-uri>" MONGODB_DB="erato_preview" python scripts/ensure_indexes.py
   ```
2. **Bootstrap Cloud Indexes**:
   ```bash
   MONGODB_URI="<cluster-uri>" MONGODB_DB="erato_preview" python -m cloud.scripts.ensure_indexes
   ```
3. **Core Standalone Verification**:
   - If `erato-cloud` is detached or disabled, `erato` must remain fully operational on its own with the default `UnlimitedPlanPolicy`.

---

## 6. Promotion Procedure (Documented — DO NOT EXECUTE)

When the preview verification phase is complete and signed off:

1. **Step 1: Merge Core to Main**:
   - Merge `erato` branch `preview` into `main` via PR.
   - Ensure GitHub Actions test suites pass on `main`.
2. **Step 2: Update Cloud Submodule**:
   - In `erato-cloud`, fetch and checkout the new `main` commit of `erato`:
     ```bash
     cd core && git checkout main && git pull
     cd .. && git add core
     git commit -m "chore: bump core submodule to main"
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
   - Re-run the index bootstrap script if reprovisioning a clean slate.
2. **Rollback Index Changes (Non-destructive)**:
   - To remove newly added indexes without dropping existing collections:
     ```bash
     MONGODB_URI="<cluster-uri>" MONGODB_DB="erato_preview" python scripts/ensure_indexes.py --rollback
     ```
3. **Rollback Submodule Pointer**:
   - Revert the submodule commit in `erato-cloud` to the prior working commit:
     ```bash
     git revert <submodule-bump-commit>
     ```
4. **Rollback Feature Flags**:
   - If `FREE_PRO_ENABLED` causes issues or was misconfigured, remove or set the variable to `false` in the Vercel dashboard and redeploy.
