from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import UnlimitedPlanPolicy
from app.core.security.tokens import hash_opaque_token, mint_access_token
from app.db.client import get_db
from app.db.repositories.bands import BandsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.deps import get_plan_policy
from app.main import app
from app.services.sharing_service import SharingService

pytestmark = pytest.mark.asyncio


def headers(uid):
    return {'Authorization': f'Bearer {mint_access_token(str(uid))}'}


@pytest.fixture
async def client():
    db = get_db()
    for name in ('bands', 'invitations', 'compositions'):
        await db[name].drop()
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client
    for name in ('bands', 'invitations', 'compositions'):
        await db[name].drop()


async def test_owner_invites_permissions_validation_and_scoped_delete(client):
    owner, member, outsider = ObjectId(), ObjectId(), ObjectId()
    repo = BandsRepository()
    band = await repo.insert('Jazz', owner)
    bid = str(band['_id'])
    await repo.collection.update_one({'_id': band['_id']}, {'$push': {'members': {'user_id': member, 'role': 'member'}}})
    path = f'/api/bands/{bid}/invites'
    created = await client.post(path, headers=headers(owner), json={})
    assert created.status_code == 201
    data = created.json()
    assert set(data) == {'id', 'invite_url', 'expires_at'}
    assert data['invite_url'].startswith('http://localhost:5173/invite/')
    stored = await InvitationsRepository().get_by_hash(hash_opaque_token(data['invite_url'].rsplit('/', 1)[1]))
    assert stored['target'] == {'type': 'band', 'id': band['_id']}
    assert 'role' not in stored and 'used_at' not in stored
    listing = await client.get(path, headers=headers(owner))
    assert listing.status_code == 200
    assert listing.json()[0]['id'] == data['id']
    assert set(listing.json()[0]) == {'id', 'expires_at'}
    listed_expiry = datetime.fromisoformat(listing.json()[0]['expires_at']).replace(tzinfo=timezone.utc)
    assert abs((listed_expiry - datetime.fromisoformat(data['expires_at'])).total_seconds()) < 0.001
    for uid, expected in ((member, 403), (outsider, 404)):
        for method, url, body in (('POST', path, {}), ('GET', path, None), ('DELETE', path + '/' + data['id'], None)):
            response = await client.request(method, url, headers=headers(uid), json=body)
            assert response.status_code == expected
    assert (await client.post(path, headers=headers(owner), json={'role': 'editor'})).status_code == 422
    assert (await client.post(path, json={})).status_code == 401
    other = await repo.insert('Other', owner)
    response = await client.delete(f"/api/bands/{other['_id']}/invites/{data['id']}", headers=headers(owner))
    assert response.status_code == 404
    assert (await client.delete(path + '/invalid', headers=headers(owner))).status_code == 404
    assert (await client.delete(path + '/' + data['id'], headers=headers(owner))).status_code == 204
    assert (await client.get(path, headers=headers(owner))).json() == []


async def test_multiuse_redeem_and_errors(client):
    owner, first, second = ObjectId(), ObjectId(), ObjectId()
    band = await BandsRepository().insert('Jazz', owner)
    bid = str(band['_id'])
    data = (await client.post(f'/api/bands/{bid}/invites', headers=headers(owner), json={})).json()
    token = data['invite_url'].rsplit('/', 1)[1]
    for uid, expected in ((first, 'joined'), (second, 'joined'), (first, 'already_member')):
        response = await client.post('/api/auth/redeem-invite', headers=headers(uid), json={'token': token})
        assert response.status_code == 200
        assert response.json() == {'band_id': bid, 'status': expected}
    doc = await BandsRepository().get_by_id(bid)
    assert doc['members'] == [{'user_id': owner, 'role': 'owner'}, {'user_id': first, 'role': 'member'}, {'user_id': second, 'role': 'member'}]
    assert 'used_at' not in await InvitationsRepository().get_by_hash(hash_opaque_token(token))
    class Inactive(UnlimitedPlanPolicy):
        async def is_band_active(self, band_id):
            return False
    app.dependency_overrides[get_plan_policy] = Inactive
    response = await client.post('/api/auth/redeem-invite', headers=headers(first), json={'token': token})
    assert response.status_code == 403 and response.json()['error'] == 'band_inactive'
    await get_db().invitations.update_one({'_id': ObjectId(data['id'])}, {'$set': {'expires_at': datetime.now(timezone.utc) - timedelta(days=1)}})
    response = await client.post('/api/auth/redeem-invite', headers=headers(first), json={'token': token})
    assert response.status_code == 410 and response.json()['error'] == 'invitation_expired'
    response = await client.post('/api/auth/redeem-invite', headers=headers(first), json={'token': 'unknown'})
    assert response.status_code == 404 and response.json()['error'] == 'not_found'


async def test_legacy_response_unchanged(client):
    owner, user = ObjectId(), ObjectId()
    comp = await CompositionsRepository().create_composition(owner, 'Legacy')
    _, token = await SharingService().create_invite(str(comp['_id']), str(owner), role='viewer')
    response = await client.post('/api/auth/redeem-invite', headers=headers(user), json={'token': token})
    assert response.status_code == 200
    assert response.json() == {'message': 'Invitación canjeada con éxito', 'composition_id': str(comp['_id'])}
    assert (await CompositionsRepository().get_by_id(comp['_id']))['members'] == [{'user_id': user, 'role': 'viewer'}]
    assert (await InvitationsRepository().get_by_hash(hash_opaque_token(token)))['used_at'] is not None
