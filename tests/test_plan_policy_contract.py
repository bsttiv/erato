import pytest
from typing import Optional
from fastapi import APIRouter, Depends
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import HostCapabilities, PlanPolicy, UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.repositories.users import UsersRepository
from app.deps import get_host_capabilities, get_plan_policy
from app.main import app
import api.index


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

