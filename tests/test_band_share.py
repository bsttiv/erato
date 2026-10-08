import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.security.tokens import mint_access_token
from app.db.repositories.bands import BandsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.main import app


@pytest.fixture
async def share_case():
    owner, member, outsider = map(str, (ObjectId(), ObjectId(), ObjectId()))
    bands, comps = BandsRepository(), CompositionsRepository()
    band = await bands.insert('B7 band', owner)
    bid = str(band['_id'])
    await bands.add_member_if_seat(bid, member, None)
    comp = await comps.create_composition(owner, 'B7 song')
    cid = str(comp['_id'])
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client, comps, bands, cid, bid, owner, member, outsider
    await comps.delete_composition(cid)
    await bands.collection.delete_one({'_id': band['_id']})


def headers(uid):
    return {'Authorization': f'Bearer {mint_access_token(uid)}'}


@pytest.mark.asyncio
async def test_attach_roles_detach_and_absent_delete(share_case):
    client, comps, bands, cid, bid, owner, member, outsider = share_case
    path = f'/api/compositions/{cid}'
    response = await client.patch(path + '/band', json={'band_id': bid, 'band_editable': False}, headers=headers(owner))
    assert response.status_code == 200
    assert response.json()['band_id'] == bid
    assert response.json()['visibility'] == 'private'
    assert (await client.get(path, headers=headers(member))).json()['user_role'] == 'viewer'
    assert (await client.patch(path, json={'title': 'Denied'}, headers=headers(member))).status_code == 403
    for role in ('editor', 'viewer', 'editor'):
        response = await client.put(path + f'/members/{member}', json={'role': role}, headers=headers(owner))
        assert response.status_code == 204
        assert (await client.get(path, headers=headers(member))).json()['user_role'] == role
    assert len((await comps.get_by_id(cid))['members']) == 1
    for uid in (member, member, outsider):
        assert (await client.delete(path + f'/members/{uid}', headers=headers(owner))).status_code == 204
    await comps.set_member_role(cid, member, 'editor')
    response = await client.patch(path + '/band', json={'band_id': None, 'band_editable': True}, headers=headers(owner))
    assert response.status_code == 200
    doc = await comps.get_by_id(cid)
    assert (doc['band_id'], doc['band_editable'], doc['members']) == (None, False, [])
    assert (await client.get(path, headers=headers(member))).status_code == 404


@pytest.mark.asyncio
async def test_detach_all_is_scoped_and_clears_roles(share_case):
    _, comps, _, cid, bid, _, member, _ = share_case
    await comps.set_band(cid, bid, True)
    await comps.set_member_role(cid, member, 'editor')
    await comps.detach_all_band_compositions(str(ObjectId()))
    assert (await comps.get_by_id(cid))['band_id'] == ObjectId(bid)
    await comps.detach_all_band_compositions(bid)
    await comps.detach_all_band_compositions(bid)
    doc = await comps.get_by_id(cid)
    assert (doc['band_id'], doc['band_editable'], doc['members']) == (None, False, [])
