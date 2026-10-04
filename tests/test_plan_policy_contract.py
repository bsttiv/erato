import pytest
from typing import Optional
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import HostCapabilities, PlanPolicy, UnlimitedPlanPolicy
from app.deps import get_host_capabilities, get_plan_policy
from app.main import app
import api.index


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


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
async def test_dependency_getters_are_overridable_and_not_singletons():
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
    async def sample_endpoint(policy: PlanPolicy = pytest.importorskip("fastapi").Depends(get_plan_policy)):
        await policy.can_share_with_people("user-abc")
        return {"ok": True}

    app.include_router(router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/test/policy-override")
        assert res.status_code == 200

    # User-scoped methods receive only user_id
    assert len(stand_in.recorded_calls) == 1
    method_name, args = stand_in.recorded_calls[0]
    assert method_name == "can_share_with_people"
    assert args == ("user-abc",)


def test_api_index_app_is_main_app():
    assert api.index.app is app


@pytest.mark.asyncio
async def test_app_accepts_host_external_routers():
    host_router = APIRouter()

    @host_router.get("/api/cloud/ping")
    async def cloud_ping():
        return {"cloud": "pong"}

    app.include_router(host_router)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/cloud/ping")
        assert res.status_code == 200
        assert res.json() == {"cloud": "pong"}
