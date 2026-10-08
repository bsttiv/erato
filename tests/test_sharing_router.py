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
async def test_composition_invite_routes_removed():
    from bson import ObjectId
    from app.main import app
    owner = str(ObjectId())
    comp = await CompositionsRepository().create_composition(owner, "Song")
    path = f"/api/compositions/{comp['_id']}/invites"
    headers = {"Authorization": f"Bearer {mint_access_token(owner)}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for method, suffix in (("POST", ""), ("GET", ""), ("DELETE", f"/{ObjectId()}")):
            response = await client.request(method, path + suffix, headers=headers, json={})
            assert response.status_code in (404, 405)
    assert await get_db().invitations.count_documents({}) == 0


@pytest.mark.asyncio
async def test_band_sharing_authorization_and_validation():
    from bson import ObjectId
    from app.db.repositories.bands import BandsRepository
    from app.main import app

    owner, member, stranger = map(str, (ObjectId(), ObjectId(), ObjectId()))
    bands, comps = BandsRepository(), CompositionsRepository()
    band = await bands.insert('Sharing authorization', owner)
    bid = str(band['_id'])
    await bands.add_member_if_seat(bid, member, None)
    comp = await comps.create_composition(owner, 'Private band song')
    cid = str(comp['_id'])
    path = f'/api/compositions/{cid}'
    def headers(uid):
        return {'Authorization': f'Bearer {mint_access_token(uid)}'}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            response = await client.patch(path + '/band', json={'band_id': bid, 'band_editable': True}, headers=headers(owner))
            assert response.status_code == 200
            for uid, expected in ((member, 403), (stranger, 404)):
                for method, suffix, body in (
                    ('PATCH', '/band', {'band_id': None, 'band_editable': False}),
                    ('PUT', f'/members/{member}', {'role': 'editor'}),
                    ('DELETE', f'/members/{member}', None),
                ):
                    response = await client.request(method, path + suffix, json=body, headers=headers(uid))
                    assert response.status_code == expected
            for body in ({'band_id': bid, 'band_editable': True, 'extra': 1}, {'band_id': bid}):
                assert (await client.patch(path + '/band', json=body, headers=headers(owner))).status_code == 422
            assert (await client.put(path + f'/members/{member}', json={'role': 'owner'}, headers=headers(owner))).status_code == 422
            for target in (stranger, 'invalid'):
                response = await client.put(path + f'/members/{target}', json={'role': 'editor'}, headers=headers(owner))
                assert response.status_code == 409
                assert response.json()['error'] == 'not_a_band_member'
            response = await client.patch(path + '/band', json={'band_id': str(ObjectId()), 'band_editable': True}, headers=headers(owner))
            assert response.status_code == 409
            assert response.json()['error'] == 'not_a_band_member'
            await client.patch(path + '/band', json={'band_id': None, 'band_editable': False}, headers=headers(owner))
            assert (await client.put(path + f'/members/{member}', json={'role': 'editor'}, headers=headers(owner))).status_code == 409
    finally:
        await bands.collection.delete_one({'_id': band['_id']})
