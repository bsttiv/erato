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
async def test_create_and_list_compositions():
    from app.main import app
    users_repo = UsersRepository()
    user = await users_repo.create_user("owner@test.com", "hash", "Owner")
    uid = str(user["_id"])
    token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Unauthenticated create -> 401
        res_unauth = await client.post("/api/compositions", json={"title": "No Auth"})
        assert res_unauth.status_code == 401

        # Authenticated create
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Mi Primera Cancion", "visibility": "private"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_create.status_code == 201
        comp = res_create.json()
        assert comp["title"] == "Mi Primera Cancion"
        assert comp["visibility"] == "private"
        assert comp["owner_id"] == uid
        assert comp["section_revs"] == {"lyrics": 0, "chords": 0, "tablature": 0}
        cid = comp["id"]


        # List user's compositions
        res_list = await client.get(
            "/api/compositions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_list.status_code == 200
        items = res_list.json()
        assert len(items) == 1
        assert items[0]["id"] == cid


@pytest.mark.asyncio
async def test_read_by_id_and_read_by_slug_anonymous():
    from app.main import app
    users_repo = UsersRepository()
    user = await users_repo.create_user("owner@test.com", "hash", "Owner")
    uid = str(user["_id"])
    token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create public composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Cancion Publica", "visibility": "public"},
            headers={"Authorization": f"Bearer {token}"},
        )
        comp = res_create.json()
        cid = comp["id"]
        slug = comp["share_slug"]
        assert slug is not None

        # Anonymous read by slug -> 200
        res_slug = await client.get(f"/api/compositions/by-slug/{slug}")
        assert res_slug.status_code == 200
        assert res_slug.json()["title"] == "Cancion Publica"

        # Anonymous read by id on public -> 200 (viewer role granted for public)
        res_id_anon = await client.get(f"/api/compositions/{cid}")
        assert res_id_anon.status_code == 200

        # Create private composition
        res_priv = await client.post(
            "/api/compositions",
            json={"title": "Cancion Privada", "visibility": "private"},
            headers={"Authorization": f"Bearer {token}"},
        )
        priv_id = res_priv.json()["id"]

        # Anonymous read by id on private -> 404
        res_priv_anon = await client.get(f"/api/compositions/{priv_id}")
        assert res_priv_anon.status_code == 404


@pytest.mark.asyncio
async def test_delete_composition_permissions():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    editor = await users_repo.create_user("editor@test.com", "hash", "Editor")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create private composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Cancion para Borrar", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        # Add editor to members directly via repo
        comp_repo = CompositionsRepository()
        await comp_repo.add_member(cid, user_id=editor["_id"], role="editor")

        # Stranger attempts delete -> 404 (private, non-member)
        res_stranger = await client.delete(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger.status_code == 404

        # Editor attempts delete -> 403 (member, but only owner can delete)
        res_editor = await client.delete(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_editor.status_code == 403

        # Owner deletes -> 200 (or 204)
        res_owner = await client.delete(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_owner.status_code in (200, 204)

        # After delete, owner get returns 404
        res_get_deleted = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_get_deleted.status_code == 404


async def test_list_includes_band_compositions_and_excludes_ex_member_roles():
    from bson import ObjectId
    from app.db.repositories.bands import BandsRepository
    from app.main import app
    db = get_db()
    uid, other = ObjectId(), ObjectId()
    band = await BandsRepository().insert("List band", other)
    try:
        await db.bands.update_one({"_id": band["_id"]},
                                 {"$push": {"members": {"user_id": uid, "role": "member"}}})
        repo = CompositionsRepository()
        own = await repo.create_composition(uid, "Own")
        shared = await repo.create_composition(other, "Band")
        legacy = await repo.create_composition(other, "Legacy")
        await repo.add_member(legacy["_id"], uid, "viewer")
        await db.compositions.update_one({"_id": shared["_id"]}, {"$set": {"band_id": band["_id"]}})
        headers = {"Authorization": f"Bearer {mint_access_token(str(uid))}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            items = (await client.get("/api/compositions", headers=headers)).json()
            by_id = {item["id"]: item for item in items}
            assert set(by_id) == {str(d["_id"]) for d in [own, shared, legacy]}
            assert by_id[str(shared["_id"])]["via_band"] is True
            assert by_id[str(shared["_id"])]["band_id"] == str(band["_id"])
            assert by_id[str(own["_id"])]["via_band"] is False
            assert by_id[str(legacy["_id"])]["via_band"] is False
            await repo.add_member(shared["_id"], uid, "editor")
            await db.bands.update_one({"_id": band["_id"]}, {"$pull": {"members": {"user_id": uid}}})
            remaining = (await client.get("/api/compositions", headers=headers)).json()
            assert {item["id"] for item in remaining} == {str(own["_id"]), str(legacy["_id"])}
    finally:
        await db.bands.delete_one({"_id": band["_id"]})
