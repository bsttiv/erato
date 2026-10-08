from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.errors import AppError
from app.core.plan_policy import UnlimitedPlanPolicy
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.bands import BandsRepository
from app.deps import get_plan_policy
from app.main import app

pytestmark = pytest.mark.asyncio
NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


def headers(uid):
    return {'Authorization': f'Bearer {mint_access_token(str(uid))}'}


@pytest.fixture
async def setup():
    db = get_db()
    await db.bands.drop()
    owner, target, other = ObjectId(), ObjectId(), ObjectId()
    repo = BandsRepository()
    band = await repo.insert('Quartet', owner)
    bid = str(band['_id'])
    for uid in (target, other):
        await repo.add_member_if_seat(bid, uid, None)
    with patch('app.services.bands_service.datetime', Clock), patch('app.routers.bands.datetime', Clock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            yield db, client, bid, owner, target, other
    await db.bands.drop()


async def seed(db, bid, owner, target, expired=False):
    transfer = {'to_user_id': target, 'requested_by': owner, 'requested_at': NOW,
                'expires_at': NOW + timedelta(days=0 if expired else 14)}
    await db.bands.update_one({'_id': ObjectId(bid)}, {'$set': {'pending_transfer': transfer}})
    return await db.bands.find_one({'_id': ObjectId(bid)})


async def call(client, bid, uid, action, target=None):
    path = f'/api/bands/{bid}/transfer'
    if action == 'accept':
        return await client.post(path + '/accept', headers=headers(uid))
    if action == 'delete':
        return await client.delete(path, headers=headers(uid))
    return await client.post(path, headers=headers(uid), json={'to_user_id': str(target)})


def error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()['error'] == code


async def test_request_rules(setup):
    db, client, bid, owner, target, other = setup
    error(await call(client, bid, target, 'request', other), 403, 'forbidden')
    for uid, status, code in ((ObjectId(), 409, 'not_a_band_member'),
                              (owner, 422, 'validation_error')):
        error(await call(client, bid, owner, 'request', uid), status, code)
        assert (await db.bands.find_one({'_id': ObjectId(bid)}))['pending_transfer'] is None
    response = await call(client, bid, owner, 'request', target)
    assert response.status_code == 201
    before = await db.bands.find_one({'_id': ObjectId(bid)})
    transfer = before['pending_transfer']
    assert transfer == {'to_user_id': target, 'requested_by': owner,
                        'requested_at': NOW.replace(tzinfo=None),
                        'expires_at': (NOW + timedelta(days=14)).replace(tzinfo=None)}
    error(await call(client, bid, owner, 'request', other), 409, 'transfer_pending')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before
    await seed(db, bid, owner, target, expired=True)
    assert (await call(client, bid, owner, 'request', other)).status_code == 201
    assert (await db.bands.find_one({'_id': ObjectId(bid)}))['pending_transfer']['to_user_id'] == other


@pytest.mark.parametrize('action', ['request', 'delete', 'accept'])
async def test_outsiders_and_unknown_bands(setup, action):
    db, client, bid, owner, target, other = setup
    await seed(db, bid, owner, target)
    for band_id, uid in ((bid, ObjectId()), ('malformed', owner), (str(ObjectId()), owner)):
        error(await call(client, band_id, uid, action, target), 404, 'not_found')


@pytest.mark.parametrize('uid_index', [3, 4])
async def test_cancel_or_reject(setup, uid_index):
    db, client, bid, owner, target, other = setup
    before = await seed(db, bid, owner, target)
    error(await call(client, bid, other, 'delete'), 403, 'forbidden')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before
    response = await call(client, bid, setup[uid_index], 'delete')
    assert response.status_code == 204 and response.content == b''
    after = await db.bands.find_one({'_id': ObjectId(bid)})
    assert after == {**before, 'pending_transfer': None}
    error(await call(client, bid, owner, 'delete'), 404, 'transfer_not_found')
    before = await seed(db, bid, owner, target, expired=True)
    error(await call(client, bid, target, 'delete'), 404, 'transfer_not_found')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before


async def test_accept_validation_and_lazy_get(setup):
    db, client, bid, owner, target, other = setup
    error(await call(client, bid, target, 'accept'), 404, 'transfer_not_found')
    await seed(db, bid, owner, target)
    error(await call(client, bid, other, 'accept'), 403, 'forbidden')
    before = await seed(db, bid, owner, target, expired=True)
    with patch.object(type(db.bands), 'update_one', side_effect=AssertionError('GET wrote')):
        response = await client.get(f'/api/bands/{bid}', headers=headers(target))
    assert response.status_code == 200 and response.json()['pending_transfer'] is None
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before
    error(await call(client, bid, target, 'accept'), 410, 'transfer_expired')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == {**before, 'pending_transfer': None}


@pytest.mark.parametrize('outcome', ['success', 'refuse', 'error', 'cancel', 'leave'])
async def test_confirm_before_writes_and_atomic_swap(setup, outcome, caplog):
    db, client, bid, owner, target, other = setup
    before = await seed(db, bid, owner, target)
    events, writes = [], []
    original = type(db.bands).update_one
    host_error = AppError('Pago no disponible', code='billing_unavailable', status_code=503,
                          details={'retry': True})

    class Policy(UnlimitedPlanPolicy):
        async def confirm_band_transfer(self, band_id, previous, new):
            assert (band_id, previous, new) == (bid, str(owner), str(target))
            assert events == []
            assert await db.bands.find_one({'_id': ObjectId(bid)}) == before
            events.append('confirm')
            if outcome == 'error':
                raise host_error
            if outcome == 'cancel':
                await original(db.bands, {'_id': ObjectId(bid)}, {'$set': {'pending_transfer': None}})
            if outcome == 'leave':
                await original(db.bands, {'_id': ObjectId(bid)}, {'$pull': {'members': {'user_id': target}}})
            return outcome != 'refuse'

    async def observe(collection, query, update, **kwargs):
        events.append('write')
        writes.append((query, update, kwargs))
        return await original(collection, query, update, **kwargs)

    app.dependency_overrides[get_plan_policy] = Policy
    with patch.object(type(db.bands), 'update_one', observe):
        response = await call(client, bid, target, 'accept')
    after = await db.bands.find_one({'_id': ObjectId(bid)})
    if outcome in ('refuse', 'error'):
        error(response, 409 if outcome == 'refuse' else 503,
              'transfer_not_confirmed' if outcome == 'refuse' else host_error.code)
        if outcome == 'error':
            assert response.json() == host_error.to_dict()
        assert events == ['confirm'] and after == before
        return
    assert events == ['confirm', 'write'] and len(writes) == 1
    query, update, kwargs = writes[0]
    assert query == {'_id': ObjectId(bid), 'owner_id': owner, 'members.user_id': target,
                     'pending_transfer.to_user_id': target, 'pending_transfer.expires_at': {'$gt': NOW}}
    assert kwargs['array_filters'] == [{'old.user_id': owner}, {'new.user_id': target}]
    assert update['$set'] == {'owner_id': target, 'members.$[old].role': 'member',
                              'members.$[new].role': 'owner', 'pending_transfer': None, 'updated_at': NOW}
    if outcome in ('cancel', 'leave'):
        error(response, 404, 'transfer_not_found')
        assert 'transfer_swap_lost' in caplog.text and after['owner_id'] == owner
    else:
        assert response.status_code == 200 and response.json()['user_role'] == 'owner'
        assert after['owner_id'] == target and after['pending_transfer'] is None
        assert after['members'] == [{'user_id': owner, 'role': 'member'},
                                    {'user_id': target, 'role': 'owner'}, {'user_id': other, 'role': 'member'}]


@pytest.mark.parametrize("expired", [False, True])
async def test_stale_target_clears_without_confirm(setup, expired):
    db, client, bid, owner, target, other = setup
    await seed(db, bid, owner, target, expired=expired)
    await db.bands.update_one({'_id': ObjectId(bid)}, {'$pull': {'members': {'user_id': target}}})
    before = await db.bands.find_one({'_id': ObjectId(bid)})
    with patch.object(UnlimitedPlanPolicy, 'confirm_band_transfer', side_effect=AssertionError('confirmed')):
        error(await call(client, bid, target, 'accept'), 409, 'not_a_band_member')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == {**before, 'pending_transfer': None}


async def test_conditional_cleanup_preserves_replacement(setup):
    db, client, bid, owner, target, other = setup
    repo = BandsRepository()
    old = await seed(db, bid, owner, target, expired=True)
    replacement = await seed(db, bid, owner, target)
    assert not await repo.clear_transfer(bid, old['pending_transfer'])
    assert await repo.get_by_id(bid) == replacement
    replacement = await seed(db, bid, owner, other, expired=True)
    assert not await repo.clear_transfer(bid, old['pending_transfer'])
    assert await repo.get_by_id(bid) == replacement


async def test_request_conditional_update_and_reread(setup):
    db, client, bid, owner, target, other = setup
    original = type(db.bands).update_one
    writes = []

    async def observe(collection, query, update, **kwargs):
        writes.append((query, update))
        return await original(collection, query, update, **kwargs)

    with patch.object(type(db.bands), 'update_one', observe):
        assert (await call(client, bid, owner, 'request', target)).status_code == 201
    assert len(writes) == 1
    assert writes[0][0] == {'_id': ObjectId(bid), 'owner_id': owner, 'members.user_id': target,
                            '$or': [{'pending_transfer': None},
                                    {'pending_transfer.expires_at': {'$lte': NOW}}]}
    before = await db.bands.find_one({'_id': ObjectId(bid)})
    with patch.object(BandsRepository, 'request_transfer', return_value=False):
        error(await call(client, bid, owner, 'request', other), 409, 'transfer_pending')
        error(await call(client, bid, owner, 'request', ObjectId()), 409, 'not_a_band_member')
    assert await db.bands.find_one({'_id': ObjectId(bid)}) == before
