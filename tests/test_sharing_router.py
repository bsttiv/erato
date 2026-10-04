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
async def test_sharing_and_visibility_spec_scenarios():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")
    invitee = await users_repo.create_user("invitee@test.com", "hash", "Invitee")

    owner_token = mint_access_token(str(owner["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))
    invitee_token = mint_access_token(str(invitee["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create private composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Private Collab", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        # Scenario 1: Stranger cannot view private composition -> 404
        res_stranger_view = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_view.status_code == 404
        assert "Private Collab" not in res_stranger_view.text

        # Scenario 2: Stranger cannot edit private composition -> 404
        res_stranger_edit = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_edit.status_code == 404

        # Scenario 3: Issue invite (owner only)
        res_invite = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "editor", "invited_email": "invitee@test.com"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_invite.status_code == 201
        invite_data = res_invite.json()
        assert "invite_url" in invite_data
        invite_id = invite_data["id"]
        # Extract token from invite_url
        token_plain = invite_data["invite_url"].split("/")[-1]

        # Scenario 4: Stranger attempting invite management -> 404
        res_stranger_invite = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "editor"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_invite.status_code == 404

        # Scenario 5: Unauthenticated invite redemption fails -> 401
        res_anon_redeem = await client.post(
            "/api/auth/redeem-invite",
            json={"token": token_plain},
        )
        assert res_anon_redeem.status_code == 401

        # Scenario 6: Authenticated invitee redeems invite -> 200
        res_redeem = await client.post(
            "/api/auth/redeem-invite",
            json={"token": token_plain},
            headers={"Authorization": f"Bearer {invitee_token}"},
        )
        assert res_redeem.status_code == 200
        assert res_redeem.json()["composition_id"] == cid

        # Scenario 7: Invitee now has editor role on private composition -> 200 view and edit
        res_invitee_view = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {invitee_token}"},
        )
        assert res_invitee_view.status_code == 200
        assert res_invitee_view.json()["title"] == "Private Collab"

        res_invitee_edit = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Collab In Progress"},
            headers={"Authorization": f"Bearer {invitee_token}"},
        )
        assert res_invitee_edit.status_code == 200

        # Invitee cannot manage sharing (only owner can) -> 403
        res_invitee_share = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "editor"},
            headers={"Authorization": f"Bearer {invitee_token}"},
        )
        assert res_invitee_share.status_code == 403

        # Scenario 8: Owner toggles visibility to public -> mints share_slug
        res_toggle_pub = await client.patch(
            f"/api/compositions/{cid}/visibility",
            json={"visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_toggle_pub.status_code == 200
        pub_comp = res_toggle_pub.json()
        assert pub_comp["visibility"] == "public"
        assert pub_comp["share_slug"] is not None
        slug = pub_comp["share_slug"]

        # Anonymous view of public composition via by-slug -> 200
        res_anon_slug = await client.get(f"/api/compositions/by-slug/{slug}")
        assert res_anon_slug.status_code == 200

        # Anonymous write on public composition -> 401 or 403
        res_anon_write = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Anonymous Deface"},
        )
        assert res_anon_write.status_code in (401, 403)

        # Stranger (authenticated non-invited) write on public composition -> 403
        res_stranger_write = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Stranger Deface"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_write.status_code == 403

        # List invites (owner only)
        res_list_inv = await client.get(
            f"/api/compositions/{cid}/invites",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_list_inv.status_code == 200
        assert len(res_list_inv.json()) == 1

        # Revoke invite (owner only)
        res_rev = await client.delete(
            f"/api/compositions/{cid}/invites/{invite_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_rev.status_code == 200


@pytest.mark.asyncio
async def test_invite_creation_fails_500_config_missing_when_app_base_url_unset(monkeypatch):
    from app.main import app
    from app.settings import get_settings

    monkeypatch.setattr(get_settings(), "app_base_url", None)

    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner_unconfigured@test.com", "hash", "Owner")
    owner_token = mint_access_token(str(owner["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://attacker-controlled-host.com") as client:
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Test Comp", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        cid = res_create.json()["id"]

        res_invite = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "editor", "invited_email": "invitee@test.com"},
            headers={"Authorization": f"Bearer {owner_token}", "Host": "attacker-controlled-host.com"},
        )
        assert res_invite.status_code == 500
        data = res_invite.json()
        assert data["error"] == "config_missing"
        assert "APP_BASE_URL" in data["message"]

        # Fail-closed: assert no orphan invitation was persisted
        invitations_repo = InvitationsRepository()
        assert len(await invitations_repo.list_by_composition(cid)) == 0


