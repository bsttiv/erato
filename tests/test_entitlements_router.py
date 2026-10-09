import pytest
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import HostCapabilities, UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.users import UsersRepository
from app.deps import get_host_capabilities, get_plan_policy
from app.main import app


@pytest.fixture(autouse=True)
async def clean_state():
    db = get_db()
    await db.users.drop()
    await UsersRepository(db).ensure_indexes()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    await db.users.drop()


class DenyAllPolicy:
    """Policy that denies all gates and restricts direct band creation."""

    async def can_share_with_people(self, user_id: str) -> bool:
        return False

    async def can_create_band(self, user_id: str) -> bool:
        return False

    async def can_view_history(self, user_id: str) -> bool:
        return False

    async def demo_limit(self, user_id: str):
        return 2

    async def seat_limit(self, band_id: str):
        return 5

    async def is_band_active(self, band_id: str) -> bool:
        return False

    async def confirm_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> bool:
        return False

    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None:
        return None


@pytest.mark.asyncio
async def test_entitlements_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/me/entitlements")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_entitlements_default_unlimited():
    users_repo = UsersRepository()
    user = await users_repo.create_user("testuser@erato.com", "hashpass", "Test User")
    token = mint_access_token(str(user["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/me/entitlements",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["can_share_with_people"] is True
        assert data["can_create_band"] is True
        assert data["can_view_history"] is True
        assert data["demo_limit_per_composition"] is None
        assert data["extensions_available"] is False
        assert data["band_creation_mode"] == "direct"


@pytest.mark.asyncio
async def test_entitlements_with_restricted_policy_and_host_capabilities():
    users_repo = UsersRepository()
    user = await users_repo.create_user("restricted@erato.com", "hashpass", "Restricted User")
    token = mint_access_token(str(user["_id"]))

    app.dependency_overrides[get_plan_policy] = lambda: DenyAllPolicy()
    app.dependency_overrides[get_host_capabilities] = lambda: HostCapabilities(extensions_available=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/me/entitlements",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["can_share_with_people"] is False
        assert data["can_create_band"] is False
        assert data["can_view_history"] is False
        assert data["demo_limit_per_composition"] == 2
        assert data["extensions_available"] is True
        assert data["band_creation_mode"] == "hand_off"
        # Never varies per composition; no composition_id in response
        assert "composition_id" not in data
