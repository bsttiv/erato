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
async def test_invite_roles_validation_and_permissions():
    from app.main import app
    users_repo = UsersRepository()
    owner = await users_repo.create_user("owner@test.com", "hash", "Owner")
    viewer_user = await users_repo.create_user("viewer@test.com", "hash", "Viewer User")
    stranger = await users_repo.create_user("stranger@test.com", "hash", "Stranger")

    owner_token = mint_access_token(str(owner["_id"]))
    viewer_token = mint_access_token(str(viewer_user["_id"]))
    stranger_token = mint_access_token(str(stranger["_id"]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create private composition
        res_create = await client.post(
            "/api/compositions",
            json={"title": "Song Roles", "visibility": "private"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_create.status_code == 201
        cid = res_create.json()["id"]

        # 1. Invalid role in invite rejected with 422
        res_invalid_role = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "admin", "invited_email": "viewer@test.com"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_invalid_role.status_code == 422

        # 2. Invite with role "viewer" accepted with 201
        res_viewer_invite = await client.post(
            f"/api/compositions/{cid}/invites",
            json={"role": "viewer", "invited_email": "viewer@test.com"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_viewer_invite.status_code == 201
        inv_data = res_viewer_invite.json()
        assert inv_data["role"] == "viewer"
        token_plain = inv_data["invite_url"].split("/")[-1]

        # 3. Redeem viewer invite
        res_redeem = await client.post(
            "/api/auth/redeem-invite",
            json={"token": token_plain},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_redeem.status_code == 200

        # Check composition members has viewer role
        res_owner_get = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        members = res_owner_get.json()["members"]
        assert any(m["user_id"] == str(viewer_user["_id"]) and m["role"] == "viewer" for m in members)

        # 4. User with "viewer" role can GET private composition
        res_viewer_get = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_viewer_get.status_code == 200
        assert res_viewer_get.json()["user_role"] == "viewer"

        # 5. User with "viewer" role rejected with 403 on all write endpoints:
        # PATCH /api/compositions/{id}
        res_patch = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Viewer Edit Attempt"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_patch.status_code == 403

        # PUT /chords
        res_chords = await client.put(
            f"/api/compositions/{cid}/chords",
            json={"instrument": "guitar", "entries": []},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_chords.status_code == 403

        # PUT /tablature
        res_tab = await client.put(
            f"/api/compositions/{cid}/tablature",
            json={"tabs": []},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_tab.status_code == 403

        # PUT /lyrics
        res_lyrics = await client.put(
            f"/api/compositions/{cid}/lyrics",
            json={"content": "New lyrics"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_lyrics.status_code == 403

        # PUT /todos
        res_todos = await client.put(
            f"/api/compositions/{cid}/todos",
            json=[{"text": "New task", "done": False}],
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_todos.status_code == 403

        # 6. Make composition public
        await client.patch(
            f"/api/compositions/{cid}/visibility",
            json={"visibility": "public"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        # Viewer can still GET public composition
        res_viewer_pub = await client.get(
            f"/api/compositions/{cid}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res_viewer_pub.status_code == 200

        # Authenticated non-invited user cannot edit public composition -> 403
        res_stranger_edit = await client.patch(
            f"/api/compositions/{cid}",
            json={"title": "Stranger Edit Attempt"},
            headers={"Authorization": f"Bearer {stranger_token}"},
        )
        assert res_stranger_edit.status_code == 403


@pytest.mark.asyncio
async def test_departed_band_member_legacy_role_is_ignored():
    from bson import ObjectId
    from app.db.repositories.bands import BandsRepository
    from app.main import app

    owner, member = str(ObjectId()), str(ObjectId())
    bands, comps = BandsRepository(), CompositionsRepository()
    band = await bands.insert('Role departure', owner)
    bid = str(band['_id'])
    await bands.add_member_if_seat(bid, member, None)
    comp = await comps.create_composition(owner, 'Legacy role')
    cid = str(comp['_id'])
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            path = f'/api/compositions/{cid}'
            owner_headers = {'Authorization': f'Bearer {mint_access_token(owner)}'}
            member_headers = {'Authorization': f'Bearer {mint_access_token(member)}'}
            assert (await client.patch(path + '/band', json={'band_id': bid, 'band_editable': True}, headers=owner_headers)).status_code == 200
            await comps.set_member_role(cid, member, 'editor')
            await bands.remove_member(bid, member)
            assert (await comps.get_by_id(cid))['members']
            assert (await client.get(path, headers=member_headers)).status_code == 404
            assert (await client.get(path)).status_code == 404
            await client.patch(path + '/visibility', json={'visibility': 'public'}, headers=owner_headers)
            assert (await client.get(path)).status_code == 200
            assert (await client.get(path, headers=member_headers)).json()['user_role'] == 'viewer'
            assert (await client.patch(path, json={'title': 'Denied'}, headers=member_headers)).status_code == 403
    finally:
        await bands.collection.delete_one({'_id': band['_id']})
