from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import PlanPolicy, UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository
from app.deps import get_plan_policy


@pytest.fixture(autouse=True)
async def clean_db_and_routes():
    from app.main import app

    db = get_db()
    await db.users.drop()
    await db.compositions.drop()
    await db.section_revisions.drop()
    await UsersRepository(db).ensure_indexes()
    await CompositionsRepository(db).ensure_indexes()
    await SectionRevisionsRepository(db).ensure_indexes()

    saved_routes = list(app.router.routes)
    yield
    app.router.routes = saved_routes
    app.dependency_overrides.clear()
    await db.users.drop()
    await db.compositions.drop()
    await db.section_revisions.drop()


class RecordingPolicy:
    """Policy stand-in recording history gate calls."""

    def __init__(self, allow_history: bool = True) -> None:
        self.allow_history = allow_history
        self.history_calls: List[tuple] = []

    async def can_share_with_people(self, user_id: str) -> bool:
        return True

    async def can_create_band(self, user_id: str) -> bool:
        return True

    async def can_view_history(self, user_id: str) -> bool:
        self.history_calls.append((user_id,))
        return self.allow_history

    async def demo_limit(self, user_id: str) -> Optional[int]:
        return None

    async def seat_limit(self, band_id: str) -> Optional[int]:
        return None

    async def is_band_active(self, band_id: str) -> bool:
        return True

    async def confirm_band_transfer(
        self, band_id: str, previous_owner_id: str, new_owner_id: str
    ) -> bool:
        return True

    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None:
        return None


@pytest.mark.asyncio
async def test_history_invalid_section_returns_404_without_touching_db():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    owner_token = mint_access_token(str(owner["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_comp = await client.post(
            "/api/compositions",
            json={"title": "Test Invalid Sections", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_comp.json()["id"]

        # Prohibir secciones no versionables o arbitrarias
        for invalid_sec in ["todos", "title", "section_revs", "unknown", "demos"]:
            res_list = await client.get(
                f"/api/compositions/{cid}/history/{invalid_sec}",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_list.status_code == 404

            res_get = await client.get(
                f"/api/compositions/{cid}/history/{invalid_sec}/1",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_get.status_code == 404

            res_restore = await client.post(
                f"/api/compositions/{cid}/history/{invalid_sec}/1/restore?expected_rev=0",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_restore.status_code == 404

        # Comprobar que la composición no fue modificada
        comp_after = await CompositionsRepository().get_by_id(cid)
        assert comp_after.get("section_revs") is None or comp_after.get("section_revs") == {}


@pytest.mark.asyncio
async def test_history_permissions_viewer_and_stranger():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner_perm@test.com", "hash", "Owner")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Composición pública
        res_pub = await client.post(
            "/api/compositions",
            json={"title": "Public Comp", "visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        pub_id = res_pub.json()["id"]

        # Guardar una versión
        await client.put(
            f"/api/compositions/{pub_id}/lyrics",
            json={"content": "v1 lyrics"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        # Viewer anónimo en pública tiene rol viewer -> 403 Forbidden
        res_anon = await client.get(f"/api/compositions/{pub_id}/history/lyrics")
        assert res_anon.status_code == 403


        # Usuario autenticado pero sin rol editor en pública -> 403 Forbidden
        res_stranger_pub = await client.get(
            f"/api/compositions/{pub_id}/history/lyrics",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_pub.status_code == 403

        # 2. Composición privada
        res_priv = await client.post(
            "/api/compositions",
            json={"title": "Private Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        priv_id = res_priv.json()["id"]

        # Extraño en privada -> 404 (anti-probing)
        res_stranger_priv = await client.get(
            f"/api/compositions/{priv_id}/history/lyrics",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_priv.status_code == 404


@pytest.mark.asyncio
async def test_history_gated_by_plan_policy_with_user_scoped_check():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("gate_owner@test.com", "hash", "Gate Owner")
    uid = str(owner["_id"])
    owner_token = mint_access_token(uid)

    # Policy que deniega historial
    deny_policy = RecordingPolicy(allow_history=False)
    app.dependency_overrides[get_plan_policy] = lambda: deny_policy

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_comp = await client.post(
            "/api/compositions",
            json={"title": "Gated Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_comp.json()["id"]

        # Insertar un snapshot manualmente para tener data
        revisions_repo = SectionRevisionsRepository()
        await revisions_repo.insert_revision(cid, "lyrics", 1, {"content": "initial"}, uid)

        # 1. List history -> 403 plan_gate_history
        res_list = await client.get(
            f"/api/compositions/{cid}/history/lyrics",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_list.status_code == 403
        assert res_list.json()["error"] == "plan_gate_history"

        # 2. Get history item -> 403 plan_gate_history
        res_get = await client.get(
            f"/api/compositions/{cid}/history/lyrics/1",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_get.status_code == 403
        assert res_get.json()["error"] == "plan_gate_history"

        # 3. Restore -> 403 plan_gate_history y NO cambia el contenido
        res_restore = await client.post(
            f"/api/compositions/{cid}/history/lyrics/1/restore?expected_rev=0",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_restore.status_code == 403
        assert res_restore.json()["error"] == "plan_gate_history"

        # Verificar que la policy recibió ÚNICAMENTE el user_id
        assert len(deny_policy.history_calls) == 3
        for call_args in deny_policy.history_calls:
            assert call_args == (uid,)

        # Verificar que no hubo cambios en la composición
        comp_after = await CompositionsRepository().get_by_id(cid)
        assert comp_after.get("lyrics") is None or comp_after.get("lyrics") == ""


@pytest.mark.asyncio
async def test_history_list_pagination_and_retention():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("hist_owner@test.com", "hash", "Hist Owner")
    uid = str(owner["_id"])
    owner_token = mint_access_token(uid)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_comp = await client.post(
            "/api/compositions",
            json={"title": "Pagination Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_comp.json()["id"]

        # Crear 51 revisiones con contenido distinto a través de PUTs sucesivos
        # para ejercitar la retención de 50 snapshots
        for r in range(1, 52):
            res_put = await client.put(
                f"/api/compositions/{cid}/lyrics?expected_rev={r - 1}",
                json={"content": f"lyrics line {r}"},
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_put.status_code == 200

        # Página 1: limit=20 -> items rev 51 down to 32, next_before_rev = 32
        res_page1 = await client.get(
            f"/api/compositions/{cid}/history/lyrics?limit=20",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_page1.status_code == 200
        p1 = res_page1.json()
        assert len(p1["items"]) == 20
        assert p1["items"][0]["rev"] == 51
        assert p1["items"][-1]["rev"] == 32
        assert p1["items"][0]["author"]["id"] == uid
        assert p1["items"][0]["author"]["display_name"] == "Hist Owner"
        assert p1["next_before_rev"] == 32

        # Página 2: limit=20, before_rev=32 -> items rev 31 down to 12, next_before_rev = 12
        res_page2 = await client.get(
            f"/api/compositions/{cid}/history/lyrics?limit=20&before_rev=32",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_page2.status_code == 200
        p2 = res_page2.json()
        assert len(p2["items"]) == 20
        assert p2["items"][0]["rev"] == 31
        assert p2["items"][-1]["rev"] == 12
        assert p2["next_before_rev"] == 12

        # Página 3: limit=20, before_rev=12 -> items rev 11 down to 2 (porque rev 1 fue podada!), next_before_rev = None
        res_page3 = await client.get(
            f"/api/compositions/{cid}/history/lyrics?limit=20&before_rev=12",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_page3.status_code == 200
        p3 = res_page3.json()
        assert len(p3["items"]) == 10  # 11, 10, 9, 8, 7, 6, 5, 4, 3, 2
        assert p3["items"][0]["rev"] == 11
        assert p3["items"][-1]["rev"] == 2
        assert p3["next_before_rev"] is None

        # Rev 1 fue podada: GET por rev 1 -> 404
        res_rev1 = await client.get(
            f"/api/compositions/{cid}/history/lyrics/1",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_rev1.status_code == 404

        # Rev 2 existe: GET por rev 2 -> 200
        res_rev2 = await client.get(
            f"/api/compositions/{cid}/history/lyrics/2",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_rev2.status_code == 200
        r2 = res_rev2.json()
        assert r2["rev"] == 2
        assert r2["content"] == {"content": "lyrics line 2"}
        assert r2["author"]["id"] == uid


@pytest.mark.asyncio
async def test_history_restore_creates_new_revision_and_checks_conflict():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner_res@test.com", "hash", "Owner Restore")
    editor = await users_repo.create_user("editor_res@test.com", "hash", "Editor Restore")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_comp = await client.post(
            "/api/compositions",
            json={"title": "Restore Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_comp.json()["id"]

        comp_repo = CompositionsRepository()
        await comp_repo.add_member(cid, user_id=editor["_id"], role="editor")

        # Crear 9 revisiones sucesivas: rev 1..9
        for r in range(1, 10):
            await client.put(
                f"/api/compositions/{cid}/lyrics?expected_rev={r - 1}",
                json={"content": f"line {r}"},
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        # 1. Restore sin expected_rev -> 422
        res_no_exp = await client.post(
            f"/api/compositions/{cid}/history/lyrics/5/restore",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_no_exp.status_code == 422

        # 2. Restore con expected_rev negativo -> 422
        res_neg = await client.post(
            f"/api/compositions/{cid}/history/lyrics/5/restore?expected_rev=-1",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_neg.status_code == 422

        # 3. Restore con expected_rev stale (ej. expected_rev=8 cuando current es 9) -> 409 section_conflict
        res_stale = await client.post(
            f"/api/compositions/{cid}/history/lyrics/5/restore?expected_rev=8",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_stale.status_code == 409
        assert res_stale.json()["error"] == "section_conflict"
        assert res_stale.json()["current_rev"] == 9

        # 4. Restore rev inexistente -> 404
        res_404 = await client.post(
            f"/api/compositions/{cid}/history/lyrics/999/restore?expected_rev=9",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_404.status_code == 404

        # 5. Restore exitoso: lyrics at rev 9, restore rev 5 con expected_rev=9
        # -> content equals snapshot rev 5 content ("line 5"), revision becomes 10
        # -> respuesta idéntica al PUT (LyricsWriteResponse)
        # -> snapshot atribuido al editor
        res_restore_ok = await client.post(
            f"/api/compositions/{cid}/history/lyrics/5/restore?expected_rev=9",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_restore_ok.status_code == 200
        restored = res_restore_ok.json()
        assert restored["content"] == "line 5"
        assert restored["rev"] == 10

        # Verificar en base de datos: lyrics actual y section_revs.lyrics == 10
        comp_doc = await comp_repo.get_by_id(cid)
        assert comp_doc["lyrics"]["content"] == "line 5"
        assert comp_doc["section_revs"]["lyrics"] == 10

        # Verificar que el nuevo snapshot (rev 10) fue atribuido a editor
        sec_repo = SectionRevisionsRepository()
        snap_10 = await sec_repo.get_by_rev(cid, "lyrics", 10)
        assert snap_10 is not None
        assert snap_10["content"] == {"content": "line 5"}
        assert snap_10["author_id"] == editor["_id"]


@pytest.mark.asyncio
async def test_history_restore_chords_and_tablature_under_default_unlimited_policy():
    from app.main import app

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner_ct@test.com", "hash", "Owner CT")
    token = mint_access_token(str(owner["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_comp = await client.post(
            "/api/compositions",
            json={"title": "Chords and Tabs Restore", "visibility": "private"},
            headers={"Authorization": f"Bearer {token}"},
        )
        cid = res_comp.json()["id"]

        # 1. Chords: save rev 1 and rev 2
        await client.put(
            f"/api/compositions/{cid}/chords?expected_rev=0",
            json={"instrument": "guitar", "entries": [{"bar": 1, "notes": [0, 4, 7], "name": "C"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.put(
            f"/api/compositions/{cid}/chords?expected_rev=1",
            json={"instrument": "guitar", "entries": [{"bar": 1, "notes": [5, 9, 0], "name": "F"}]},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Restore chords rev 1
        res_res_chords = await client.post(
            f"/api/compositions/{cid}/history/chords/1/restore?expected_rev=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_res_chords.status_code == 200
        chords_data = res_res_chords.json()
        assert chords_data["rev"] == 3
        assert chords_data["instrument"] == "guitar"
        assert chords_data["entries"][0]["name"] == "C"

        # 2. Tablature: save rev 1 and rev 2
        await client.put(
            f"/api/compositions/{cid}/tablature?expected_rev=0",
            json={"strings": 6, "content": "e|---0---|", "tabs": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.put(
            f"/api/compositions/{cid}/tablature?expected_rev=1",
            json={"strings": 6, "content": "e|---3---|", "tabs": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Restore tablature rev 1
        res_res_tab = await client.post(
            f"/api/compositions/{cid}/history/tablature/1/restore?expected_rev=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_res_tab.status_code == 200
        tab_data = res_res_tab.json()
        assert tab_data["rev"] == 3
        assert tab_data["strings"] == 6
        assert tab_data["content"] == "e|---0---|"

