from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.permissions import Role, resolve_role
from app.core.plan_policy import UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.bands import BandsRepository
from app.services.bands_service import BandsService
from app.main import app

pytestmark = pytest.mark.asyncio


def headers(uid):
    return {'Authorization': f'Bearer {mint_access_token(str(uid))}'}


@pytest.fixture
async def setup():
    db = get_db()
    for collection in (db.bands, db.compositions):
        await collection.drop()
    owner, member, other = ObjectId(), ObjectId(), ObjectId()
    repo = BandsRepository()
    band = await repo.insert('Quartet', owner)
    bid = str(band['_id'])
    await repo.add_member_if_seat(bid, member, None)
    await repo.add_member_if_seat(bid, other, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield db, client, bid, owner, member, other
    for collection in (db.bands, db.compositions):
        await collection.drop()


async def composition(db, owner, band, member):
    doc = {'owner_id': owner, 'band_id': band, 'band_editable': True,
           'members': [{'user_id': member, 'role': 'editor'}], 'visibility': 'private',
           'updated_at': datetime(2020, 1, 1, tzinfo=timezone.utc)}
    doc['_id'] = (await db.compositions.insert_one(doc)).inserted_id
    return await db.compositions.find_one({'_id': doc['_id']})


@pytest.mark.parametrize('action', ['leave', 'remove'])
async def test_authorization_and_no_changes(setup, action):
    db, client, bid, owner, member, other = setup
    outsider = ObjectId()
    before = await db.bands.find_one({'_id': ObjectId(bid)})

    async def request(target, uid, removed=member):
        if action == 'leave':
            return await client.post(f'/api/bands/{target}/leave', headers=headers(uid))
        return await client.delete(f'/api/bands/{target}/members/{removed}', headers=headers(uid))

    for target in (bid, str(ObjectId()), 'malformed'):
        response = await request(target, outsider)
        assert response.status_code == 404 and response.json()['error'] == 'not_found'
    response = await request(bid, owner, owner)
    assert response.status_code == 409 and response.json()['error'] == 'owner_must_transfer'
    if action == 'remove':
        response = await request(bid, member)
        assert response.status_code == 403 and response.json()['error'] == 'forbidden'
        for absent in (outsider, 'malformed'):
            response = await request(bid, owner, absent)
            assert response.status_code == 204 and response.content == b''
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before


@pytest.mark.parametrize('action', ['leave', 'remove'])
@pytest.mark.parametrize('transfer_target', ['departing', 'other'])
async def test_detach_order_scope_roles_and_transfer(setup, action, transfer_target):
    db, client, bid, owner, member, other = setup
    own = await composition(db, member, ObjectId(bid), other)
    untouched = [await composition(db, other, ObjectId(bid), member),
                 await composition(db, member, ObjectId(), other),
                 await composition(db, member, None, other)]
    transfer = {'to_user_id': member if transfer_target == 'departing' else other}
    await db.bands.update_one({'_id': ObjectId(bid)}, {'$set': {'pending_transfer': transfer}})
    original = BandsRepository.remove_member

    async def observed_pull(repo, band_id, uid):
        detached = await db.compositions.find_one({'_id': own['_id']})
        assert detached['band_id'] is None and detached['band_editable'] is False
        assert detached['members'] == [] and detached['updated_at'] > own['updated_at']
        assert any(m['user_id'] == member for m in (await repo.get_by_id(bid))['members'])
        return await original(repo, band_id, uid)

    with patch.object(BandsRepository, 'remove_member', observed_pull):
        if action == 'leave':
            response = await client.post(f'/api/bands/{bid}/leave', headers=headers(member))
        else:
            response = await client.delete(f'/api/bands/{bid}/members/{member}', headers=headers(owner))
    assert response.status_code == 204 and response.content == b''
    band = await db.bands.find_one({'_id': ObjectId(bid)})
    assert [m['user_id'] for m in band['members']] == [owner, other]
    assert band['pending_transfer'] == (None if transfer_target == 'departing' else transfer)
    detached = await db.compositions.find_one({'_id': own['_id']})
    assert resolve_role(other, detached) is None
    assert resolve_role(other, {**detached, 'members': own['members']}) == Role.EDITOR
    for doc in untouched:
        assert await db.compositions.find_one({'_id': doc['_id']}) == doc
    if action == 'remove':
        assert (await client.delete(f'/api/bands/{bid}/members/{member}', headers=headers(owner))).status_code == 204
        assert await db.bands.find_one({'_id': ObjectId(bid)}) == band
        assert await db.compositions.find_one({'_id': own['_id']}) == detached


@pytest.mark.parametrize('action', ['leave', 'remove'])
async def test_retry_after_detach_before_pull_failure(setup, action):
    db, client, bid, owner, member, other = setup
    own = await composition(db, member, ObjectId(bid), other)
    service = BandsService(UnlimitedPlanPolicy())

    async def run():
        if action == 'leave':
            await service.leave(bid, str(member))
        else:
            await service.remove_member(bid, str(owner), str(member))

    with patch.object(BandsRepository, 'remove_member', side_effect=RuntimeError('simulated pull failure')):
        with pytest.raises(RuntimeError, match='simulated pull failure'):
            await run()
    detached = await db.compositions.find_one({'_id': own['_id']})
    assert detached['band_id'] is None and detached['members'] == []
    assert any(m['user_id'] == member for m in (await service.bands.get_by_id(bid))['members'])
    await run()
    assert await db.compositions.find_one({'_id': own['_id']}) == detached
    assert all(m['user_id'] != member for m in (await service.bands.get_by_id(bid))['members'])


async def test_repository_owner_guard_and_conditional_transfer_cleanup(setup):
    db, client, bid, owner, member, other = setup
    repo = BandsRepository()
    await db.bands.update_one({'_id': ObjectId(bid)}, {'$set': {'pending_transfer': {'to_user_id': member}}})
    before = await repo.get_by_id(bid)
    assert await repo.remove_member(bid, owner) is False
    assert await repo.get_by_id(bid) == before
    original = db.bands.update_one
    calls = []

    async def observe(query, update, **kwargs):
        calls.append((query, update))
        return await original(query, update, **kwargs)

    with patch.object(type(db.bands), 'update_one', side_effect=observe):
        assert await repo.remove_member(bid, member) is True
    assert calls[0][0] == {'_id': ObjectId(bid), 'owner_id': {'$ne': member}}
    assert calls[0][1]['$pull'] == {'members': {'user_id': member}}
    assert calls[1][0] == {'_id': ObjectId(bid), 'pending_transfer.to_user_id': member}
    assert calls[1][1]['$set']['pending_transfer'] is None
