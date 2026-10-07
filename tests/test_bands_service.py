from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection

from app.core.errors import PlanGateError, ValidationError
from app.core.plan_policy import UnlimitedPlanPolicy
from app.db.client import get_db
from app.db.repositories.invitations import InvitationsRepository
from app.services.bands_service import BandsService

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def clean_state():
    db = get_db()
    for collection in (db.bands, db.compositions, db.invitations):
        await collection.drop()
    yield
    for collection in (db.bands, db.compositions, db.invitations):
        await collection.drop()


async def test_host_creation_shape_validation_and_no_gate():
    policy = UnlimitedPlanPolicy()
    policy.can_create_band = AsyncMock(return_value=False)
    service = BandsService(policy, get_db())
    owner = str(ObjectId())
    for name in (' X ', ' ' + 'x' * 80 + ' '):
        band = await service.create_for_user(owner, name)
        assert set(band) == {'_id', 'name', 'owner_id', 'members', 'pending_transfer', 'created_at', 'updated_at'}
        assert band['name'] == name.strip()
        assert band['owner_id'] == ObjectId(owner)
        assert band['members'] == [{'user_id': ObjectId(owner), 'role': 'owner'}]
        assert band['pending_transfer'] is None
        assert isinstance(band['created_at'], datetime)
        assert band['created_at'] == band['updated_at']
    for name in ('', '   ', 'x' * 81, None, 123):
        with pytest.raises(ValidationError) as error:
            await service.create_for_user(owner, name)
        assert (error.value.status_code, error.value.code) == (422, 'validation_error')
    assert await get_db().bands.count_documents({}) == 2
    policy.can_create_band.assert_not_awaited()


async def test_direct_creation_gate_and_unlimited_multiple_bands():
    policy = UnlimitedPlanPolicy()
    policy.can_create_band = AsyncMock(return_value=False)
    user = {'id': str(ObjectId())}
    with pytest.raises(PlanGateError) as error:
        await BandsService(policy).create(user, 'Quartet')
    assert (error.value.status_code, error.value.code) == (403, 'plan_gate_band_creation')
    policy.can_create_band.assert_awaited_once_with(user['id'])
    assert await get_db().bands.count_documents({}) == 0
    service = BandsService(UnlimitedPlanPolicy())
    for _ in range(3):
        await service.create(user, 'Quartet')
    assert await get_db().bands.count_documents({}) == 3


async def test_delete_order_idempotency_and_unknown_ids():
    db = get_db()
    service = BandsService(UnlimitedPlanPolicy(), db)
    owner = str(ObjectId())
    band = await service.create_for_user(owner, 'Quartet')
    bid = band['_id']
    other = ObjectId()
    await db.compositions.insert_many([
        {'band_id': bid, 'band_editable': True, 'members': [{'user_id': ObjectId(owner)}]},
        {'band_id': other, 'band_editable': True, 'members': []},
    ])
    await InvitationsRepository(db).create_band_invitation(bid, 'token', datetime.now(timezone.utc) + timedelta(days=1), owner)
    events = []
    detach, invitations, delete = AsyncCollection.update_many, InvitationsRepository.delete_by_band, AsyncCollection.delete_one

    async def detach_spy(*args, **kwargs):
        events.append('detach')
        return await detach(*args, **kwargs)

    async def invitations_spy(repo, *args):
        events.append('invitations')
        return await invitations(repo, *args)

    async def delete_spy(*args, **kwargs):
        events.append('band')
        return await delete(*args, **kwargs)

    with patch.object(AsyncCollection, 'update_many', detach_spy), patch.object(InvitationsRepository, 'delete_by_band', invitations_spy), patch.object(AsyncCollection, 'delete_one', delete_spy):
        await service.delete_band(str(bid))
        assert events == ['detach', 'invitations', 'band']
        await service.delete_band(str(bid))
        await service.delete_band(str(ObjectId()))
        await service.delete_band('malformed')
        assert events == ['detach', 'invitations', 'band']
    detached = await db.compositions.find_one({'band_id': None})
    assert detached['band_editable'] is False and detached['members'] == []
    assert isinstance(detached['updated_at'], datetime)
    assert await db.compositions.count_documents({'band_id': other, 'band_editable': True}) == 1
    assert await db.invitations.count_documents({}) == 0
    assert await db.bands.count_documents({}) == 0
