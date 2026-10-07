import pytest
from bson import ObjectId
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
async def test_user_role_in_detail_and_by_slug():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@erato.io", "hash", "Owner")
    editor = await users_repo.create_user("editor@erato.io", "hash", "Editor")
    viewer = await users_repo.create_user("viewer@erato.io", "hash", "Viewer")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))
    viewer_token = mint_access_token(str(viewer["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create public composition by owner
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Cancion Compartida", "visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_create.status_code == 201
        comp = res_create.json()
        cid = comp["id"]
        slug = comp["share_slug"]

        # Owner gets user_role: "owner"
        res_owner = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_owner.status_code == 200
        assert res_owner.json()["user_role"] == "owner"

        # Add editor and viewer as members
        db = get_db()
        await db.compositions.update_one(
            {"_id": ObjectId(cid)},
            {
                "$push": {
                    "members": {
                        "$each": [
                            {"user_id": editor["_id"], "role": "editor"},
                            {"user_id": viewer["_id"], "role": "viewer"},
                        ]
                    }
                }
            },
        )

        # Editor gets user_role: "editor"
        res_editor = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_editor.status_code == 200
        assert res_editor.json()["user_role"] == "editor"

        # Viewer gets user_role: "viewer"
        res_viewer = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_viewer.status_code == 200
        assert res_viewer.json()["user_role"] == "viewer"

        # Anonymous access to public share slug returns user_role: None
        res_slug_anon = await client.get(f"/api/compositions/by-slug/{slug}")
        assert res_slug_anon.status_code == 200
        assert res_slug_anon.json()["user_role"] is None

        # Authenticated access to public share slug by editor returns user_role: "editor"
        res_slug_editor = await client.get(
            f"/api/compositions/by-slug/{slug}",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_slug_editor.status_code == 200
        assert res_slug_editor.json()["user_role"] == "editor"


@pytest.mark.asyncio
async def test_list_compositions_counts_and_chord_names():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@erato.io", "hash", "Owner")
    owner_token = mint_access_token(str(owner["_id"]))

    db = get_db()
    # Insert composition with chords, tabs, todos, demos
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    comp_doc = {
        "owner_id": owner["_id"],
        "title": "Cancion Con Secciones",
        "visibility": "private",
        "status": "in_progress",
        "key": "G",
        "bpm": 110,
        "time_signature": "4/4",
        "style_tags": ["rock"],
        "sections_enabled": {
            "chords": True,
            "tablature": True,
            "lyrics": True,
            "demos": True,
            "todos": True,
        },
        "chords": {
            "instrument": "guitar",
            "entries": [
                {"bar": 1, "notes": [0, 2, 2, 0, 0, 0], "name": "Em"},
                {"bar": 2, "notes": [3, 2, 0, 0, 3, 3], "name": "G"},
                {"bar": 3, "notes": [0, 3, 2, 0, 1, 0], "name": "C"},
                {"bar": 4, "notes": [-1, 0, 0, 2, 3, 2], "name": "D"},
                {"bar": 5, "notes": [0, 0, 2, 2, 1, 0], "name": "Am"},
            ],
        },
        "tablature": {
            "strings": 6,
            "tabs": [
                {"id": "tab1", "title": "Intro", "content": "e|---"},
                {"id": "tab2", "title": "Solo", "content": "e|---"},
            ],
        },
        "lyrics": {"content": "[Em]Luz [G]de ciudad"},
        "todos": [
            {"id": "todo1", "text": "Grabar bajo", "done": True},
            {"id": "todo2", "text": "Mezclar intro", "done": False},
            {"id": "todo3", "text": "Revisar puente", "done": True},
        ],
        "demos": [
            {
                "demo_id": "demo1",
                "cloudinary_public_id": "c1",
                "title": "Toma 1",
                "duration_s": 120.0,
                "uploaded_by": str(owner["_id"]),
                "uploaded_at": now,
            }
        ],
        "members": [],
        "created_at": now,
        "updated_at": now,
    }
    await db.compositions.insert_one(comp_doc)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/compositions",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        item = items[0]

        # First 4 chord names
        assert item["chord_names"] == ["Em", "G", "C", "D"]

        # Counts
        assert item["counts"]["chords"] == 5
        assert item["counts"]["tabs"] == 2
        assert item["counts"]["demos"] == 1
        assert item["counts"]["todos_done"] == 2
        assert item["counts"]["todos_total"] == 3


async def test_bandless_response_defaults():
    from app.main import app
    token = mint_access_token(str(ObjectId()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/compositions", json={"title": "Solo"},
                                     headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 201
        assert response.json()["band_id"] is None
        assert response.json()["band_editable"] is False
        assert response.json()["band_active"] is None
