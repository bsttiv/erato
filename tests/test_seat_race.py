import asyncio

import pytest
from bson import ObjectId

from app.core.plan_policy import UnlimitedPlanPolicy
from app.db.repositories.bands import BandsRepository
from app.deps import get_plan_policy
from app.main import app
from tests.test_bands_invites import client, headers

pytestmark = pytest.mark.asyncio


async def test_last_seat_concurrent_redeems(client):
    class LastSeat(UnlimitedPlanPolicy):
        async def seat_limit(self, band_id):
            assert band_id == bid
            return 2
    band = await BandsRepository().insert('Jazz', ObjectId())
    bid = str(band['_id'])
    app.dependency_overrides[get_plan_policy] = LastSeat
    data = (await client.post(f'/api/bands/{bid}/invites', headers=headers(band['owner_id']), json={})).json()
    token = data['invite_url'].rsplit('/', 1)[1]
    responses = await asyncio.gather(*[
        client.post('/api/auth/redeem-invite', headers=headers(ObjectId()), json={'token': token})
        for _ in range(8)
    ])
    assert sum(r.status_code == 200 for r in responses) == 1
    assert sum(r.status_code == 409 and r.json()['error'] == 'band_full' for r in responses) == 7
    assert len((await BandsRepository().get_by_id(bid))['members']) == 2


async def test_repository_unbounded_and_idempotent(client):
    repo = BandsRepository()
    band = await repo.insert('Jazz', ObjectId())
    uid = ObjectId()
    results = await asyncio.gather(*[repo.add_member_if_seat(band['_id'], uid, None) for _ in range(8)])
    assert results.count('joined') == 1 and results.count('already_member') == 7
    assert await repo.add_member_if_seat(band['_id'], uid, 1) == 'already_member'
    for _ in range(12):
        assert await repo.add_member_if_seat(band['_id'], ObjectId(), None) == 'joined'
    assert len((await repo.get_by_id(band['_id']))['members']) == 14
