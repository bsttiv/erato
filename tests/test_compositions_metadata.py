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
async def test_create_composition_with_metadata_and_defaults():
    from app.main import app

    users_repo = UsersRepository()
    user = await users_repo.create_user("author@erato.io", "hash", "Author")
    uid = str(user["_id"])
    token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Default creation without metadata
        res_default = await client.post(
            "/api/compositions",
            json={"title": "Cancion Sin Metadatos", "visibility": "private"},
            headers=headers,
        )
        assert res_default.status_code == 201
        data_default = res_default.json()
        assert data_default["title"] == "Cancion Sin Metadatos"
        assert data_default["status"] == "idea"
        assert data_default["key"] is None
        assert data_default["bpm"] is None
        assert data_default["time_signature"] is None
        assert data_default["style_tags"] == []
        assert data_default["sections_enabled"] == {
            "chords": True,
            "tablature": False,
            "lyrics": True,
            "demos": True,
            "todos": True,
        }

        # 2. Creation with full optional metadata
        res_meta = await client.post(
            "/api/compositions",
            json={
                "title": "Cancion Con Metadatos",
                "visibility": "public",
                "key": "Am",
                "bpm": 124,
                "time_signature": "4/4",
                "style_tags": ["jazz", "ballad"],
                "status": "in_progress",
                "sections_enabled": {
                    "chords": True,
                    "tablature": True,
                    "lyrics": True,
                    "demos": False,
                    "todos": True,
                },
            },
            headers=headers,
        )
        assert res_meta.status_code == 201
        data_meta = res_meta.json()
        assert data_meta["title"] == "Cancion Con Metadatos"
        assert data_meta["key"] == "Am"
        assert data_meta["bpm"] == 124
        assert data_meta["time_signature"] == "4/4"
        assert data_meta["style_tags"] == ["jazz", "ballad"]
        assert data_meta["status"] == "in_progress"
        assert data_meta["sections_enabled"] == {
            "chords": True,
            "tablature": True,
            "lyrics": True,
            "demos": False,
            "todos": True,
        }


@pytest.mark.asyncio
async def test_status_validation():
    from app.main import app

    users_repo = UsersRepository()
    user = await users_repo.create_user("author@erato.io", "hash", "Author")
    uid = str(user["_id"])
    token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Valid statuses: "idea", "in_progress", "ready"
        for valid_status in ["idea", "in_progress", "ready"]:
            res = await client.post(
                "/api/compositions",
                json={"title": f"Status {valid_status}", "status": valid_status},
                headers=headers,
            )
            assert res.status_code == 201
            assert res.json()["status"] == valid_status

        # Invalid status returns 422 Unprocessable Entity
        res_invalid = await client.post(
            "/api/compositions",
            json={"title": "Status Invalid", "status": "draft"},
            headers=headers,
        )
        assert res_invalid.status_code == 422


@pytest.mark.asyncio
async def test_patch_composition_metadata():
    from app.main import app

    users_repo = UsersRepository()
    user = await users_repo.create_user("author@erato.io", "hash", "Author")
    uid = str(user["_id"])
    token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Create base composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Original Title"},
            headers=headers,
        )
        assert res_create.status_code == 201
        cid = res_create.json()["id"]

        # Patch metadata fields
        res_patch = await client.patch(
            f"/api/compositions/{cid}",
            json={
                "title": "Updated Title",
                "key": "E",
                "bpm": 95,
                "time_signature": "3/4",
                "style_tags": ["folk", "acústico"],
                "status": "ready",
                "sections_enabled": {
                    "chords": True,
                    "tablature": False,
                    "lyrics": True,
                    "demos": True,
                    "todos": False,
                },
            },
            headers=headers,
        )
        assert res_patch.status_code == 200
        patched = res_patch.json()
        assert patched["title"] == "Updated Title"
        assert patched["key"] == "E"
        assert patched["bpm"] == 95
        assert patched["time_signature"] == "3/4"
        assert patched["style_tags"] == ["folk", "acústico"]
        assert patched["status"] == "ready"
        assert patched["sections_enabled"]["todos"] is False

        # Read back via GET
        res_get = await client.get(f"/api/compositions/{cid}", headers=headers)
        assert res_get.status_code == 200
        get_data = res_get.json()
        assert get_data["key"] == "E"
        assert get_data["bpm"] == 95
        assert get_data["status"] == "ready"


@pytest.mark.asyncio
async def test_legacy_composition_deserialization_with_defaults():
    from datetime import datetime, timezone
    from bson import ObjectId
    from app.main import app

    db = get_db()
    users_repo = UsersRepository()
    user = await users_repo.create_user("author@erato.io", "hash", "Author")
    uid = user["_id"]
    token = mint_access_token(str(uid))

    # Insert raw legacy composition document lacking metadata fields
    now = datetime.now(timezone.utc)
    legacy_doc = {
        "owner_id": uid,
        "title": "Legacy Composition Without Metadata",
        "visibility": "private",
        "chords": None,
        "tablature": None,
        "lyrics": None,
        "todos": [],
        "demos": [],
        "members": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.compositions.insert_one(legacy_doc)
    cid = str(result.inserted_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get(f"/api/compositions/{cid}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == cid
        assert data["title"] == "Legacy Composition Without Metadata"
        assert data["status"] == "idea"
        assert data["key"] is None
        assert data["bpm"] is None
        assert data["time_signature"] is None
        assert data["style_tags"] == []
        assert data["sections_enabled"] == {
            "chords": True,
            "tablature": False,
            "lyrics": True,
            "demos": True,
            "todos": True,
        }
