import pytest
from httpx import ASGITransport, AsyncClient
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.db.repositories.users import UsersRepository


@pytest.fixture(autouse=True)
async def clean_db():
    db = get_db()
    await db.users.drop()
    await db.compositions.drop()
    await db.invitations.drop()
    await UsersRepository(db).ensure_indexes()
    await CompositionsRepository(db).ensure_indexes()
    await InvitationsRepository(db).ensure_indexes()
    yield
    await db.users.drop()
    await db.compositions.drop()
    await db.invitations.drop()


@pytest.mark.asyncio
async def test_members_projection_and_security():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Carlos Santana")
    editor = await users_repo.create_user("editor@test.com", "hash", "Ana Pérez")
    viewer = await users_repo.create_user("viewer@test.com", "hash", "Juan Domínguez")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Extraño")

    owner_token = mint_access_token(str(owner["_id"]))
    editor_token = mint_access_token(str(editor["_id"]))
    viewer_token = mint_access_token(str(viewer["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Band Projection Test", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_create.status_code == 201
        cid = res_create.json()["id"]

        # Existing member roles remain readable; legacy pending invites are excluded.
        await CompositionsRepository().set_member_role(cid, str(editor['_id']), 'editor')
        await CompositionsRepository().set_member_role(cid, str(viewer['_id']), 'viewer')
        from datetime import datetime, timedelta, timezone
        from bson import ObjectId
        await get_db().invitations.insert_one({
            'composition_id': ObjectId(cid), 'token_hash': 'pending-legacy',
            'role': 'editor', 'used_at': None, 'invited_email': 'pending@test.com',
            'expires_at': datetime.now(timezone.utc) + timedelta(days=14),
        })

        # 1. GET /api/compositions/{id}/members for owner
        res_members = await client.get(
            f"/api/compositions/{cid}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_members.status_code == 200
        members_data = res_members.json()
        assert len(members_data) == 3  # owner + editor + viewer
        assert all(not m["pending"] and m["user_id"] for m in members_data)

        # Active owner
        m_owner = next(m for m in members_data if m["role"] == "owner")
        assert m_owner["user_id"] == str(owner["_id"])
        assert m_owner["display_name"] == "Carlos Santana"
        assert m_owner["email"] == "owner@test.com"
        assert m_owner["initials"] == "CS"
        assert m_owner["pending"] is False

        # Active editor
        m_editor = next(m for m in members_data if m["user_id"] == str(editor["_id"]))
        assert m_editor["display_name"] == "Ana Pérez"
        assert m_editor["email"] == "editor@test.com"
        assert m_editor["initials"] == "AP"
        assert m_editor["role"] == "editor"
        assert m_editor["pending"] is False

        # Active viewer
        m_viewer = next(m for m in members_data if m["user_id"] == str(viewer["_id"]))
        assert m_viewer["display_name"] == "Juan Domínguez"
        assert m_viewer["email"] == "viewer@test.com"
        assert m_viewer["initials"] == "JD"
        assert m_viewer["role"] == "viewer"
        assert m_viewer["pending"] is False

        # 2. Permissions check:
        # Editor cannot GET members -> 403
        res_editor_get = await client.get(
            f"/api/compositions/{cid}/members",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert res_editor_get.status_code == 403

        # Viewer cannot GET members -> 403
        res_viewer_get = await client.get(
            f"/api/compositions/{cid}/members",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_viewer_get.status_code == 403

        # Stranger on private -> 404
        res_stranger_get = await client.get(
            f"/api/compositions/{cid}/members",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_get.status_code == 404

        # 3. CompositionResponse members has display_name and initials, but NEVER email (D8)
        res_comp = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_comp.status_code == 200
        comp_members = res_comp.json()["members"]
        assert len(comp_members) == 2  # editor + viewer
        for cm in comp_members:
            assert "display_name" in cm and cm["display_name"] is not None
            assert "initials" in cm and cm["initials"] is not None
            assert "email" not in cm

        # Public by-slug route also returns MemberItem without email
        await client.patch(
            f"/api/compositions/{cid}/visibility",
            json={"visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        pub_slug = res_comp.json()["share_slug"] or (await client.get(f"/api/compositions/{cid}", headers={"Authorization": f"Bearer {owner_token}"})).json()["share_slug"]
        res_slug = await client.get(f"/api/compositions/by-slug/{pub_slug}")
        assert res_slug.status_code == 200
        for cm in res_slug.json()["members"]:
            assert "display_name" in cm and cm["display_name"] is not None
            assert "initials" in cm and cm["initials"] is not None
            assert "email" not in cm
