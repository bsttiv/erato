import pytest
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import HostCapabilities, PlanPolicy, UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.repositories.users import UsersRepository
from app.deps import get_host_capabilities, get_plan_policy
from app.main import app
import api.index


def test_seams_documentation_pins_host_contract():
    path = Path(__file__).resolve().parents[1] / "docs" / "seams.md"
    assert path.is_file(), "docs/seams.md must document the host contract"
    documentation = path.read_text(encoding="utf-8")
    methods = {name for name, value in vars(PlanPolicy).items()
               if not name.startswith("_") and callable(value)}
    for name in sorted(methods | {
        "get_plan_policy", "get_host_capabilities", "BandsService.create_for_user",
        "BandsService.delete_band", "createEratoApp", "PaymentExtension",
    }):
        assert name in documentation, f"Missing seam: {name}"


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def restore_routes():
    """Snapshot and restore registered routes to prevent test leakage."""
    original_routes = list(app.router.routes)
    yield
    app.router.routes = original_routes


@pytest.mark.asyncio
async def test_unlimited_plan_policy_answers_seven_questions():
    policy = UnlimitedPlanPolicy()

    assert await policy.can_share_with_people("user-123") is True
    assert await policy.can_create_band("user-123") is True
    assert await policy.can_view_history("user-123") is True
    assert await policy.demo_limit("user-123") is None
    assert await policy.seat_limit("band-456") is None
    assert await policy.is_band_active("band-456") is True
    assert await policy.confirm_band_transfer("band-456", "user-1", "user-2") is True


@pytest.mark.asyncio
async def test_abort_band_transfer_contract():
    assert 'abort_band_transfer' in vars(PlanPolicy)
    assert await UnlimitedPlanPolicy().abort_band_transfer("band-456", "user-1", "user-2") is None


class RecordingStandInPolicy:
    """Mock policy implementing PlanPolicy Protocol that records invocation arguments."""

    def __init__(self):
        self.recorded_calls = []

    async def can_share_with_people(self, user_id: str) -> bool:
        self.recorded_calls.append(("can_share_with_people", (user_id,)))
        return False

    async def can_create_band(self, user_id: str) -> bool:
        self.recorded_calls.append(("can_create_band", (user_id,)))
        return False

    async def can_view_history(self, user_id: str) -> bool:
        self.recorded_calls.append(("can_view_history", (user_id,)))
        return False

    async def demo_limit(self, user_id: str) -> Optional[int]:
        self.recorded_calls.append(("demo_limit", (user_id,)))
        return 3

    async def seat_limit(self, band_id: str) -> Optional[int]:
        self.recorded_calls.append(("seat_limit", (band_id,)))
        return 5

    async def is_band_active(self, band_id: str) -> bool:
        self.recorded_calls.append(("is_band_active", (band_id,)))
        return False

    async def confirm_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> bool:
        self.recorded_calls.append(("confirm_band_transfer", (band_id, previous_owner_id, new_owner_id)))
        return False

    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None:
        self.recorded_calls.append(("abort_band_transfer", (band_id, previous_owner_id, new_owner_id)))


def test_plan_policy_protocol_conformance():
    policy = UnlimitedPlanPolicy()
    assert isinstance(policy, PlanPolicy)

    stand_in = RecordingStandInPolicy()
    assert isinstance(stand_in, PlanPolicy)


@pytest.mark.asyncio
async def test_dependency_getters_are_overridable_and_not_singletons(restore_routes):
    # Calling getters repeatedly returns new instances (not module singletons)
    p1 = get_plan_policy()
    p2 = get_plan_policy()
    assert isinstance(p1, UnlimitedPlanPolicy)
    assert p1 is not p2

    h1 = get_host_capabilities()
    h2 = get_host_capabilities()
    assert h1.extensions_available is False
    assert h1 is not h2

    # Overrides via app.dependency_overrides
    stand_in = RecordingStandInPolicy()
    app.dependency_overrides[get_plan_policy] = lambda: stand_in
    app.dependency_overrides[get_host_capabilities] = lambda: HostCapabilities(extensions_available=True)

    # In a dummy route or dependency resolution
    router = APIRouter()

    @router.get("/test/policy-override")
    async def sample_endpoint(
        policy: PlanPolicy = Depends(get_plan_policy),
        host_caps: HostCapabilities = Depends(get_host_capabilities),
    ):
        await policy.can_share_with_people("user-abc")
        return {"extensions": host_caps.extensions_available}

    app.include_router(router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/test/policy-override")
        assert res.status_code == 200
        assert res.json() == {"extensions": True}


@pytest.mark.asyncio
async def test_user_scoped_methods_receive_only_user_id_from_entitlements_endpoint():
    users_repo = UsersRepository()
    user = await users_repo.create_user("contract_user@test.com", "hashpass", "Contract User")
    user_id = str(user["_id"])
    token = mint_access_token(user_id)

    stand_in = RecordingStandInPolicy()
    app.dependency_overrides[get_plan_policy] = lambda: stand_in

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/me/entitlements",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    # Assert that can_share_with_people, can_create_band, can_view_history and demo_limit
    # were each called exactly once with exactly (user_id,)
    assert len(stand_in.recorded_calls) == 4
    expected_calls = [
        ("can_share_with_people", (user_id,)),
        ("can_create_band", (user_id,)),
        ("can_view_history", (user_id,)),
        ("demo_limit", (user_id,)),
    ]
    assert stand_in.recorded_calls == expected_calls


def test_api_index_app_is_main_app():
    assert api.index.app is app


@pytest.mark.asyncio
async def test_app_accepts_host_external_routers(restore_routes):
    host_router = APIRouter()

    @host_router.get("/api/cloud/ping")
    async def cloud_ping():
        return {"cloud": "pong"}

    app.include_router(host_router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/cloud/ping")
        assert res.status_code == 200
        assert res.json() == {"cloud": "pong"}


@pytest.mark.asyncio
@pytest.mark.parametrize("call_site", ["list", "get", "restore", "signature", "confirm"])
async def test_existing_gate_call_sites_honor_user_scoped_policy(call_site, monkeypatch):
    from uuid import uuid4
    import cloudinary.utils
    from app.db.repositories.compositions import CompositionsRepository
    from app.settings import get_settings

    user = await UsersRepository().create_user(f"gate-{call_site}-{uuid4().hex}@test.com", "hash", "Gate User")
    uid = str(user["_id"])
    repo = CompositionsRepository()
    comp = await repo.create_composition(owner_id=uid, title="Gate contract")
    cid = str(comp["_id"])
    await repo.add_demo(cid, "existing", "existing", "Existing", 1, uid)

    class LimitOnePolicy(RecordingStandInPolicy):
        async def demo_limit(self, user_id):
            self.recorded_calls.append(("demo_limit", (user_id,)))
            return 1

    monkeypatch.setattr("cloudinary.uploader.remove_tag", lambda *args, **kwargs: None)
    policy = LimitOnePolicy()
    app.dependency_overrides[get_plan_policy] = lambda: policy
    public_id = f"{get_settings().cloudinary_folder_prefix}/compositions/{cid}/new"
    body = {"public_id": public_id, "version": "1", "title": "New", "duration_s": 1,
            "signature": cloudinary.utils.api_sign_request(
                {"public_id": public_id, "version": "1"}, get_settings().cloudinary_api_secret)}
    requests = {
        "list": ("GET", "/history/lyrics", None),
        "get": ("GET", "/history/lyrics/1", None),
        "restore": ("POST", "/history/lyrics/1/restore?expected_rev=0", None),
        "signature": ("POST", "/demos/upload-signature", None),
        "confirm": ("POST", "/demos", body),
    }
    method, suffix, payload = requests[call_site]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.request(method, f"/api/compositions/{cid}{suffix}", json=payload,
                                        headers={"Authorization": f"Bearer {mint_access_token(uid)}"})
    assert response.status_code == 403
    question = "demo_limit" if call_site in ("signature", "confirm") else "can_view_history"
    assert response.json()["error"] == ("plan_gate_demo_limit" if question == "demo_limit" else "plan_gate_history")
    assert policy.recorded_calls == [(question, (uid,))]


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['attach', 'put', 'delete', 'detach', 'invalid_attach', 'invalid_put'])
@pytest.mark.parametrize('sharing_allowed', [False, True])
async def test_band_sharing_gate_order_and_gate_free_detach(operation, sharing_allowed):
    from bson import ObjectId
    from app.db.repositories.bands import BandsRepository
    from app.db.repositories.compositions import CompositionsRepository

    uid, member = str(ObjectId()), str(ObjectId())
    bands, comps = BandsRepository(), CompositionsRepository()
    band = await bands.insert('Policy contract', uid)
    bid = str(band['_id'])
    await bands.add_member_if_seat(bid, member, None)
    comp = await comps.create_composition(uid, 'Policy sharing')
    cid = str(comp['_id'])
    await comps.collection.update_one({'_id': comp['_id']}, {'$set': {'band_id': band['_id'], 'band_editable': True}})
    await comps.set_member_role(cid, member, 'editor')

    class SharingPolicy(RecordingStandInPolicy):
        async def can_share_with_people(self, user_id):
            await super().can_share_with_people(user_id)
            return sharing_allowed

    policy = SharingPolicy()
    app.dependency_overrides[get_plan_policy] = lambda: policy
    requests = {
        'attach': ('PATCH', '/band', {'band_id': bid, 'band_editable': True}),
        'put': ('PUT', f'/members/{member}', {'role': 'viewer'}),
        'delete': ('DELETE', f'/members/{member}', None),
        'detach': ('PATCH', '/band', {'band_id': None, 'band_editable': True}),
        'invalid_attach': ('PATCH', '/band', {'band_id': str(ObjectId()), 'band_editable': True}),
        'invalid_put': ('PUT', f'/members/{ObjectId()}', {'role': 'viewer'}),
    }
    try:
        method, suffix, body = requests[operation]
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            response = await client.request(method, f'/api/compositions/{cid}{suffix}', json=body,
                                            headers={'Authorization': f'Bearer {mint_access_token(uid)}'})
        expected = []
        if operation == 'detach':
            assert response.status_code == 200
            doc = await comps.get_by_id(cid)
            assert (doc['band_id'], doc['band_editable'], doc['members']) == (None, False, [])
        elif operation.startswith('invalid'):
            assert response.status_code == 409
            assert response.json()['error'] == 'not_a_band_member'
        else:
            assert response.status_code == 403
            if operation != 'delete':
                expected.append(('can_share_with_people', (uid,)))
            if operation == 'delete' or sharing_allowed:
                expected.append(('is_band_active', (bid,)))
            assert response.json()['error'] == ('band_inactive' if operation == 'delete' or sharing_allowed else 'plan_gate_sharing')
            doc = await comps.get_by_id(cid)
            assert doc['band_id'] == band['_id'] and doc['members'][0]['role'] == 'editor'
        assert policy.recorded_calls == expected
    finally:
        await comps.delete_composition(cid)
        await bands.collection.delete_one({'_id': band['_id']})
