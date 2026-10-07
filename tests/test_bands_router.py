from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.plan_policy import UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.bands import BandsRepository
from app.db.repositories.users import UsersRepository
from app.deps import get_plan_policy
from app.main import app

pytestmark = pytest.mark.asyncio
SUMMARY = {'id', 'name', 'owner_id', 'user_role', 'seats_used', 'seat_limit', 'active'}
RESPONSE = SUMMARY | {'members', 'pending_transfer', 'created_at', 'updated_at'}


@pytest.fixture
async def client():
    db = get_db()
    for collection in (db.bands, db.users):
        await collection.drop()
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client
    for collection in (db.bands, db.users):
        await collection.drop()


def headers(uid):
    return {'Authorization': f'Bearer {mint_access_token(str(uid))}'}


class RestrictedPolicy(UnlimitedPlanPolicy):
    async def can_create_band(self, user_id):
        return False

    async def seat_limit(self, band_id):
        return 8

    async def is_band_active(self, band_id):
        return False


async def test_create_gate_auth_and_validation(client):
    owner = ObjectId()
    assert (await client.post('/api/bands', json={'name': 'Quartet'})).status_code == 401
    response = await client.post('/api/bands', headers=headers(owner), json={'name': ' Quartet '})
    assert response.status_code == 201
    data = response.json()
    assert set(data) == RESPONSE
    assert data['name'] == 'Quartet' and data['owner_id'] == str(owner)
    assert data['user_role'] == 'owner' and data['seats_used'] == 1
    assert data['seat_limit'] is None and data['active'] is True
    assert data['pending_transfer'] is None
    assert data['members'] == [{'user_id': str(owner), 'role': 'owner', 'display_name': None, 'initials': None}]
    app.dependency_overrides[get_plan_policy] = RestrictedPolicy
    response = await client.post('/api/bands', headers=headers(owner), json={'name': 'Denied'})
    assert response.status_code == 403 and response.json()['error'] == 'plan_gate_band_creation'
    for body in ({'name': ''}, {'name': '  '}, {'name': 'x' * 81}, {'name': 'Valid', 'owner_id': str(owner)}, {}, {'name': 12}):
        response = await client.post('/api/bands', headers=headers(owner), json=body)
        assert response.status_code == 422 and response.json()['error'] == 'validation_error'
    assert await get_db().bands.count_documents({}) == 1


async def test_list_read_member_projection_policy_and_expiry(client):
    owner, member, outsider = ObjectId(), ObjectId(), ObjectId()
    await get_db().users.insert_many([{'_id': owner, 'display_name': 'Ana Luz'}, {'_id': member, 'display_name': 'Pablo'}])
    repo = BandsRepository()
    band = await repo.insert('Quartet', owner)
    bid = str(band['_id'])
    await repo.insert('Other', outsider)
    await repo.collection.update_one({'_id': band['_id']}, {'$push': {'members': {'user_id': member, 'role': 'member'}}})
    app.dependency_overrides[get_plan_policy] = RestrictedPolicy
    for uid, role in ((owner, 'owner'), (member, 'member')):
        listing = await client.get('/api/bands', headers=headers(uid))
        assert listing.status_code == 200
        assert len(listing.json()) == 1 and set(listing.json()[0]) == SUMMARY
        assert listing.json()[0] == {'id': bid, 'name': 'Quartet', 'owner_id': str(owner), 'user_role': role, 'seats_used': 2, 'seat_limit': 8, 'active': False}
    batch_lookup = UsersRepository.get_by_ids
    with patch.object(UsersRepository, 'get_by_ids', autospec=True) as lookup:
        # Use the real batch implementation while counting its invocations.
        lookup.side_effect = batch_lookup
        response = await client.get(f'/api/bands/{bid}', headers=headers(member))
        assert response.status_code == 200
        lookup.assert_awaited_once()
        assert set(lookup.call_args.args[1]) == {owner, member}
    data = response.json()
    assert set(data) == RESPONSE and data['user_role'] == 'member'
    assert data['seat_limit'] == 8 and data['active'] is False and data['seats_used'] == 2
    assert data['members'] == [
        {'user_id': str(owner), 'display_name': 'Ana Luz', 'initials': 'AL', 'role': 'owner'},
        {'user_id': str(member), 'display_name': 'Pablo', 'initials': 'PA', 'role': 'member'},
    ]
    for days in (-1, 1):
        transfer = {'to_user_id': member, 'requested_by': owner, 'requested_at': datetime.now(timezone.utc), 'expires_at': datetime.now(timezone.utc) + timedelta(days=days)}
        await repo.collection.update_one({'_id': band['_id']}, {'$set': {'pending_transfer': transfer}})
        data = (await client.get(f'/api/bands/{bid}', headers=headers(member))).json()
        if days < 0:
            assert data['pending_transfer'] is None
        else:
            assert set(data['pending_transfer']) == {'to_user_id', 'requested_at', 'expires_at'}
            assert data['pending_transfer']['to_user_id'] == str(member)
        assert (await repo.get_by_id(bid))['pending_transfer'] is not None
    for target in (bid, str(ObjectId()), 'malformed'):
        response = await client.get(f'/api/bands/{target}', headers=headers(outsider))
        assert response.status_code == 404 and response.json()['error'] == 'not_found'
    assert (await client.get('/api/bands')).status_code == 401
    assert (await client.get(f'/api/bands/{bid}')).status_code == 401


async def test_rename_owner_only_and_extra_forbidden(client):
    owner, member = ObjectId(), ObjectId()
    band = await BandsRepository().insert('Quartet', owner)
    bid = str(band['_id'])
    await get_db().bands.update_one({'_id': band['_id']}, {'$push': {'members': {'user_id': member, 'role': 'member'}}})
    response = await client.patch(f'/api/bands/{bid}', headers=headers(member), json={'name': 'Denied'})
    assert response.status_code == 403 and response.json()['error'] == 'forbidden'
    outsider = ObjectId()
    for target in (bid, str(ObjectId()), 'malformed'):
        response = await client.patch(f'/api/bands/{target}', headers=headers(outsider), json={'name': 'Denied'})
        assert response.status_code == 404 and response.json()['error'] == 'not_found'
    for body in ({'name': ' '}, {'name': 'x' * 81}, {'name': 'Valid', 'active': True}):
        response = await client.patch(f'/api/bands/{bid}', headers=headers(owner), json=body)
        assert response.status_code == 422 and response.json()['error'] == 'validation_error'
    response = await client.patch(f'/api/bands/{bid}', headers=headers(owner), json={'name': ' ' + 'x' * 80 + ' '})
    assert response.status_code == 200 and response.json()['name'] == 'x' * 80
    assert set(response.json()) == RESPONSE
    assert (await client.patch(f'/api/bands/{bid}', json={'name': 'X'})).status_code == 401
    assert (await client.delete(f'/api/bands/{bid}', headers=headers(owner))).status_code == 405
