import pytest
from httpx import ASGITransport, AsyncClient
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.users import UsersRepository


@pytest.fixture(autouse=True)
async def clean_db():
    db = get_db()
    await db.users.drop()
    await db.compositions.drop()
    await UsersRepository(db).ensure_indexes()
    await CompositionsRepository(db).ensure_indexes()
    yield
    await db.users.drop()
    await db.compositions.drop()


@pytest.mark.asyncio
async def test_tablature_tabs_crud_and_validation():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("guitarist@test.com", "hash", "Guitarist")
    owner_token = mint_access_token(str(owner["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Flamenco Fusion", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_create.status_code == 201
        cid = res_create.json()["id"]

        # 1. Empty tabs array is valid
        res_empty = await client.put(
            f"/api/compositions/{cid}/tablature",
            json={"tabs": []},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_empty.status_code == 200
        assert res_empty.json()["tabs"] == []

        # 2. Valid multi-tab update
        tabs_payload = [
            {
                "id": "tab-intro",
                "title": "Intro Guitarra",
                "strings": 6,
                "columns": [["0", "", "", "", "", ""], "|", ["", "1", "", "", "", ""]],
            },
            {
                "id": "tab-solo",
                "title": "Solo Final",
                "strings": 6,
                "columns": [["", "", "5h7", "", "", ""]],
            },
        ]
        res_put = await client.put(
            f"/api/compositions/{cid}/tablature",
            json={"tabs": tabs_payload},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_put.status_code == 200
        data = res_put.json()
        assert len(data["tabs"]) == 2
        assert data["tabs"][0]["id"] == "tab-intro"
        assert data["tabs"][0]["title"] == "Intro Guitarra"
        assert data["tabs"][0]["strings"] == 6
        assert len(data["tabs"][0]["columns"]) == 3
        assert data["tabs"][1]["id"] == "tab-solo"

        # 3. GET composition persists tabs array without requiring derived ASCII text
        res_get = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_get.status_code == 200
        saved_comp = res_get.json()
        assert saved_comp["tablature"] is not None
        assert len(saved_comp["tablature"]["tabs"]) == 2
        assert saved_comp["tablature"]["tabs"][0]["id"] == "tab-intro"

        # 4. Validation: title must be 1-80 chars
        res_bad_title = await client.put(
            f"/api/compositions/{cid}/tablature",
            json={
                "tabs": [
                    {
                        "id": "tab-1",
                        "title": "",  # empty
                        "strings": 6,
                        "columns": [],
                    }
                ]
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_bad_title.status_code == 422

        res_long_title = await client.put(
            f"/api/compositions/{cid}/tablature",
            json={
                "tabs": [
                    {
                        "id": "tab-1",
                        "title": "x" * 81,  # exceeds 80
                        "strings": 6,
                        "columns": [],
                    }
                ]
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_long_title.status_code == 422
