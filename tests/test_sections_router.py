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
async def test_sections_crud_owner_and_editor():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    editor = await users_repo.create_user("editor@test.com", "hash", "Editor")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Song with Sections", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        # Add editor to members
        comp_repo = CompositionsRepository()
        await comp_repo.add_member(cid, user_id=editor["_id"], role="editor")

        # 1. Chords section (written by owner)
        chords_payload = {
            "instrument": "guitar",
            "entries": [{"bar": 1, "notes": [0, 4, 7], "name": "C"}],
        }
        res_put_chords = await client.put(
            f"/api/compositions/{cid}/chords",
            json=chords_payload,
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_put_chords.status_code == 200
        assert res_put_chords.json()["entries"][0]["name"] == "C"

        # Read chords by editor
        res_get_chords = await client.get(
            f"/api/compositions/{cid}/chords",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_get_chords.status_code == 200
        assert res_get_chords.json()["entries"][0]["name"] == "C"

        # 2. Tablature section (written by editor)
        tab_payload = {"strings": 6, "content": "e|---0---|"}
        res_put_tab = await client.put(
            f"/api/compositions/{cid}/tablature",
            json=tab_payload,
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_put_tab.status_code == 200
        assert res_put_tab.json()["content"] == "e|---0---|"

        # 3. Lyrics section (written by editor)
        lyrics_payload = {"content": "[C]Hello world..."}
        res_put_lyrics = await client.put(
            f"/api/compositions/{cid}/lyrics",
            json=lyrics_payload,
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_put_lyrics.status_code == 200
        assert res_put_lyrics.json()["content"] == "[C]Hello world..."

        # 4. Todos section (written by owner)
        todos_payload = [{"text": "Mix vocals", "done": False}]
        res_put_todos = await client.put(
            f"/api/compositions/{cid}/todos",
            json=todos_payload,
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_put_todos.status_code == 200
        assert len(res_put_todos.json()) == 1


@pytest.mark.asyncio
async def test_sections_permissions_viewer_and_stranger():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Public composition
        res_pub = await client.post(
            "/api/compositions",
            json={"title": "Public Sections", "visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        pub_id = res_pub.json()["id"]

        # Private composition
        res_priv = await client.post(
            "/api/compositions",
            json={"title": "Private Sections", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        priv_id = res_priv.json()["id"]

        # Viewer (anonymous) can read public lyrics -> 200
        res_read_pub = await client.get(f"/api/compositions/{pub_id}/lyrics")
        assert res_read_pub.status_code == 200

        # Viewer (anonymous or non-invited) CANNOT edit public lyrics -> 403
        res_write_pub_anon = await client.put(
            f"/api/compositions/{pub_id}/lyrics",
            json={"content": "hacked"},
        )
        assert res_write_pub_anon.status_code == 403

        res_write_pub_stranger = await client.put(
            f"/api/compositions/{pub_id}/lyrics",
            json={"content": "stranger write"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_write_pub_stranger.status_code == 403

        # Stranger on private cannot read -> 404
        res_read_priv = await client.get(
            f"/api/compositions/{priv_id}/lyrics",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_read_priv.status_code == 404

        # Stranger on private cannot write -> 404 (not 403)
        res_write_priv = await client.put(
            f"/api/compositions/{priv_id}/lyrics",
            json={"content": "secret leak"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_write_priv.status_code == 404


@pytest.mark.asyncio
async def test_sections_versioning_and_conflict():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner_v1@test.com", "hash", "Owner V1")
    editor = await users_repo.create_user("editor_v1@test.com", "hash", "Editor V1")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Song Versioned", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        comp_repo = CompositionsRepository()
        await comp_repo.add_member(cid, user_id=editor["_id"], role="editor")

        # 1. Negative expected_rev -> 422
        res_neg = await client.put(
            f"/api/compositions/{cid}/lyrics?expected_rev=-1",
            json={"content": "v1"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_neg.status_code == 422

        # 2. Update lyrics with expected_rev=0 -> 200, rev=1
        res_v1 = await client.put(
            f"/api/compositions/{cid}/lyrics?expected_rev=0",
            json={"content": "v1 content"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_v1.status_code == 200
        assert res_v1.json()["content"] == "v1 content"
        assert res_v1.json()["rev"] == 1

        # 3. Update lyrics with expected_rev=1 -> 200, rev=2 (by editor)
        res_v2 = await client.put(
            f"/api/compositions/{cid}/lyrics?expected_rev=1",
            json={"content": "v2 content"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_v2.status_code == 200
        assert res_v2.json()["content"] == "v2 content"
        assert res_v2.json()["rev"] == 2

        # 4. Update lyrics with stale expected_rev=1 -> 409 conflict
        res_conflict = await client.put(
            f"/api/compositions/{cid}/lyrics?expected_rev=1",
            json={"content": "stale edit"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_conflict.status_code == 409
        conflict_data = res_conflict.json()
        assert conflict_data["error"] == "section_conflict"
        assert conflict_data["section"] == "lyrics"
        assert conflict_data["current_rev"] == 2
        assert conflict_data["content"] == {"content": "v2 content"}
        assert conflict_data["author"]["id"] == str(editor["_id"])

        assert conflict_data["author"]["display_name"] == "Editor V1"
        assert "updated_at" in conflict_data

        # 5. Check GET composition contains section_revs
        res_get_comp = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_get_comp.status_code == 200
        comp_data = res_get_comp.json()
        assert "section_revs" in comp_data
        assert comp_data["section_revs"]["lyrics"] == 2
        assert comp_data["section_revs"]["chords"] == 0
        assert comp_data["section_revs"]["tablature"] == 0

