# Host integration seams

## Backend identity and dependency injection

The stable FastAPI instance is `app.main.app`; `api/index.py` re-exports that same object.
`app/main.py` includes health, maintenance, auth, bands, compositions, sections, sharing,
demos, entitlements and history routers. Hosts may call `app.include_router(...)` after import.
Put the core repository on `sys.path` before importing it. Always import core modules as
`app.*`, never `erato.app.*`: duplicate module identities would break dependency override keys.
Keep the host package distinct (for example, `erato_cloud`).

`app.deps.get_plan_policy() -> PlanPolicy` returns a new `UnlimitedPlanPolicy`.
`app.deps.get_host_capabilities() -> HostCapabilities` returns a new instance with
`extensions_available=False`. FastAPI caches dependency results within each request;
a host getter should construct its policy per request, with no cross-request entitlement cache.
HTTP routers inject the policy. Direct construction of `SharingService`, `DemoService` or
`VersioningService` without a policy falls back to `UnlimitedPlanPolicy`; hosts must pass it explicitly.
Install overrides using the original getter objects:

```python
from app.main import app
from app.deps import get_plan_policy, get_host_capabilities
from app.core.plan_policy import HostCapabilities

# get_subscription_plan_policy and plan_router are supplied by the host.
app.dependency_overrides[get_plan_policy] = get_subscription_plan_policy
app.dependency_overrides[get_host_capabilities] = lambda: HostCapabilities(extensions_available=True)
app.include_router(plan_router)
```

## PlanPolicy port

`app.core.plan_policy.PlanPolicy` is a runtime-checkable Protocol. All seven methods are async;
signatures below omit `self`. User arguments identify the acting authenticated user, with no
composition context. The core contains no plan catalogue or payment provider implementation.

| Signature | Meaning |
| --- | --- |
| `can_share_with_people(user_id: str) -> bool` | Permit band attachment and explicit composition member roles; detachment is ungated. |
| `can_create_band(user_id: str) -> bool` | Permit direct creation through `POST /api/bands`. |
| `can_view_history(user_id: str) -> bool` | Permit history list/get/restore after edit authorization. |
| `demo_limit(user_id: str) -> Optional[int]` | Per-composition demo count ceiling for the uploader; `None` means unlimited. |
| `seat_limit(band_id: str) -> Optional[int]` | Atomic band join ceiling; `None` means unlimited. |
| `is_band_active(band_id: str) -> bool` | Allow invitation creation/join and band sharing changes; band-derived content writes require activity, owner content edits are exempt. |
| `confirm_band_transfer(band_id: str, previous_owner_id: str, new_owner_id: str) -> bool` | Called before the owner/role swap; `False` yields 409 `transfer_not_confirmed`, host `AppError` propagates, neither changes core transfer state. |

`UnlimitedPlanPolicy` answers `True` to all boolean methods and `None` to both limits.
A successful transfer confirmation precedes a conditional swap: a lost swap returns 404 and
logs `transfer_swap_lost`; host subscription changes are not automatically compensated by core.
Hosts own subscription resolution and any provider compensation (design AD19/AD20).

## Entitlements response

Authenticated `GET /api/me/entitlements` returns `app.schemas.entitlements.EntitlementsResponse`;
missing authentication returns 401. Default response:

```json
{"can_share_with_people":true,"can_create_band":true,"can_view_history":true,
 "demo_limit_per_composition":null,"extensions_available":false,"band_creation_mode":"direct"}
```

The first three fields and `extensions_available` are booleans; the demo limit is integer or null.
`band_creation_mode` is `direct` when `can_create_band` is true, otherwise `hand_off`, independently
of host capabilities. The frontend entry supplies the hand-off target, not this endpoint.

## Host-invocable band operations

Import `BandsService` from `app.services.bands_service` and `BandCreate` from `app.schemas.bands`.
Constructor: `BandsService(policy: PlanPolicy, db: Optional[AsyncDatabase] = None)`, using
`pymongo.asynchronous.database.AsyncDatabase`. Services return raw Mongo documents, not API schemas.

- `await BandsService.create_for_user(user_id: str, name: str) -> dict` validates with `BandCreate`
  (strip whitespace, 1–80 characters; invalid name: 422 `validation_error`) and inserts the owner
  member, null pending transfer and timestamps. It does **not** call the creation gate; the host
  must authenticate and confirm checkout first. User IDs must be valid Mongo ObjectId strings.
- `await BandsService.delete_band(band_id: str) -> None` is host compensation, with no HTTP endpoint
  or permission gate. Unknown/malformed IDs are no-ops. For an existing band it detaches all its
  compositions (`band_id=null`, `band_editable=false`, `members=[]`, refreshed `updated_at`),
  deletes band-targeted invitations, then deletes the band. Ordered steps are safe to retry;
  there is no transaction or subscription cleanup.

## Frontend payment extension

`frontend/src/app.ts` exports `createEratoApp(options: EratoAppOptions = {}): VueApp` and
`createEratoRouter(payments?: PaymentExtension): Router`. `frontend/src/extension.ts` defines
`EratoAppOptions { payments?: PaymentExtension }` and the following registration contract:

```ts
interface PaymentExtension {
  routes: RouteRecordRaw[]
  navItems?: PaymentNavItem[] // { label: string; to: RouteLocationRaw }
  bandCreationEntry?: RouteLocationRaw
}
// Host initializes shared auth and then mounts:
ensureAuthReady()
createEratoApp({ payments: { routes: [checkoutRoute],
  bandCreationEntry: { name: 'band-checkout' } } }).mount('#app')
```

Startup validates every route and child: resolved paths must equal `EXTENSION_ROUTE_PREFIX`
(`/plan`) or start with that prefix followed by `/` (`/plan/...`);
`meta.requiresAuth` must be exactly true, and `meta.public`/`meta.guestOnly` must be falsy.
If supplied, `bandCreationEntry` must resolve with a matched registered extension record or startup
throws. Routes are inserted before the catch-all and share core auth/navigation guards.
`PAYMENT_EXTENSION_KEY` is the typed `Symbol('payments')` injection key in `frontend/src/extension.ts`,
re-exported by `app.ts`; the factory provides the extension through it. Nav extras appear only when
authenticated. No payments option means no payment routes or nav entries. In `hand_off` mode without
an entry the creation control is disabled. Successful navigation out of `/plan` or `/plan/...` refreshes
entitlements.
