from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.core.plan_policy import UnlimitedPlanPolicy
from app.db.client import get_db


@pytest.fixture
def band_doc():
    owner, member = ObjectId(), ObjectId()
    now = datetime.now(timezone.utc)
    return {
        '_id': ObjectId(), 'name': 'Quartet', 'owner_id': owner,
        'members': [{'user_id': owner, 'role': 'owner'},
                    {'user_id': member, 'role': 'member'}],
        'created_at': now, 'updated_at': now,
    }


@pytest.mark.parametrize('viewer,role', [(0, 'owner'), (1, 'member')])
@pytest.mark.parametrize('limit,active', [(None, True), (8, False)])
async def test_to_band_summary(band_doc, viewer, role, limit, active):
    from app.presenters.bands import to_band_summary

    policy = UnlimitedPlanPolicy()
    policy.seat_limit = AsyncMock(return_value=limit)
    policy.is_band_active = AsyncMock(return_value=active)
    summary = await to_band_summary(
        band_doc, str(band_doc['members'][viewer]['user_id']), policy,
    )
    assert summary.model_dump() == {
        'id': str(band_doc['_id']), 'name': 'Quartet',
        'owner_id': str(band_doc['owner_id']), 'user_role': role,
        'seats_used': 2, 'seat_limit': limit, 'active': active,
    }
    policy.seat_limit.assert_awaited_once_with(str(band_doc['_id']))
    policy.is_band_active.assert_awaited_once_with(str(band_doc['_id']))


@pytest.mark.parametrize('viewer,role', [(0, 'owner'), (1, 'member')])
@pytest.mark.parametrize('days,naive', [(None, False), (-1, False), (1, False),
                                        (-1, True), (1, True)])
async def test_to_band_response(band_doc, viewer, role, days, naive):
    from app.presenters.bands import to_band_response

    owner, member = [m['user_id'] for m in band_doc['members']]
    db = get_db()
    await db.users.insert_many([
        {'_id': owner, 'display_name': 'Ana Luz', 'email': f'{owner}@example.test'},
        {'_id': member, 'display_name': 'Pablo', 'email': f'{member}@example.test'},
    ])
    try:
        if days is not None:
            expiry = band_doc['created_at'] + timedelta(days=days)
            band_doc['pending_transfer'] = {
                'to_user_id': member, 'requested_at': band_doc['created_at'],
                'expires_at': expiry.replace(tzinfo=None) if naive else expiry,
            }
        policy = UnlimitedPlanPolicy()
        policy.seat_limit = AsyncMock(return_value=8)
        policy.is_band_active = AsyncMock(return_value=False)
        response = await to_band_response(
            band_doc, str(band_doc['members'][viewer]['user_id']), policy,
        )
        assert response.user_role == role
        assert (response.seats_used, response.seat_limit, response.active) == (2, 8, False)
        assert response.created_at == band_doc['created_at']
        assert response.updated_at == band_doc['updated_at']
        assert [m.model_dump() for m in response.members] == [
            {'user_id': str(owner), 'role': 'owner', 'display_name': 'Ana Luz', 'initials': 'AL'},
            {'user_id': str(member), 'role': 'member', 'display_name': 'Pablo', 'initials': 'PA'},
        ]
        if days is None or days < 0:
            assert response.pending_transfer is None
        else:
            assert response.pending_transfer.model_dump() == {
                'to_user_id': str(member), 'requested_at': band_doc['created_at'],
                'expires_at': expiry,
            }
            assert response.pending_transfer.expires_at.tzinfo == timezone.utc
    finally:
        await db.users.delete_many({'_id': {'$in': [owner, member]}})


def test_compute_initials_public_api_and_compatibility():
    from app.presenters.users import compute_initials
    from app.routers.compositions import compute_initials as legacy_compute_initials

    assert legacy_compute_initials is compute_initials
    for name, expected in [(None, None), ('  ', None), ('Pablo', 'PA'), ('Ana Luz', 'AL')]:
        assert compute_initials(name) == expected
