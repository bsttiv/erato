from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.bands import BandsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.deps import get_plan_policy
from app.main import app


@pytest.fixture
async def band_composition():
    db = get_db()
    await db.bands.drop()
    await db.compositions.drop()
    owner, member, stranger = ObjectId(), ObjectId(), ObjectId()
    band = await BandsRepository().insert("Trio", owner)
    await db.bands.update_one({"_id": band["_id"]},
                              {"$push": {"members": {"user_id": member, "role": "member"}}})
    doc = await CompositionsRepository().create_composition(owner, "Night", "public", "night")
    await db.compositions.update_one({"_id": doc["_id"]},
                                     {"$set": {"band_id": band["_id"], "band_editable": True}})
    yield db, doc, band, owner, member, stranger
    await db.bands.drop()
    await db.compositions.drop()


@pytest.mark.parametrize("active", [True, False])
async def test_band_response_and_write(band_composition, active):
    db, doc, band, owner, member, stranger = band_composition
    policy = UnlimitedPlanPolicy()
    policy.is_band_active = AsyncMock(return_value=active)
    app.dependency_overrides[get_plan_policy] = lambda: policy
    headers = {"Authorization": f"Bearer {mint_access_token(str(member))}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for path in [str(doc["_id"]), "by-slug/night"]:
            response = await client.get(f"/api/compositions/{path}", headers=headers)
            assert response.status_code == 200
            assert response.json()["user_role"] == "editor"
            assert response.json()["band_id"] == str(band["_id"])
            assert response.json()["band_editable"] is True
            assert response.json()["band_active"] is active
        result = await client.patch(f'/api/compositions/{doc["_id"]}',
                                    headers=headers, json={"title": "Changed"})
        assert result.status_code == (200 if active else 403)
        if not active:
            assert result.json()["error"] == "band_inactive"
            stored = await db.compositions.find_one({"_id": doc["_id"]})
            assert stored["title"] == "Night"
        await db.compositions.update_one({"_id": doc["_id"]},
                                         {"$set": {"visibility": "private", "band_editable": False}})
        read = await client.get(f'/api/compositions/{doc["_id"]}', headers=headers)
        assert read.json()["user_role"] == "viewer"
        outsider = {"Authorization": f"Bearer {mint_access_token(str(stranger))}"}
        assert (await client.get(f'/api/compositions/{doc["_id"]}', headers=outsider)).status_code == 404
        await db.compositions.update_one({"_id": doc["_id"]},
                                         {"$push": {"members": {"user_id": member, "role": "editor"}}})
        await db.bands.update_one({"_id": band["_id"]}, {"$pull": {"members": {"user_id": member}}})
        assert (await client.get(f'/api/compositions/{doc["_id"]}', headers=headers)).status_code == 404
