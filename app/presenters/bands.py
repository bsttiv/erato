from datetime import datetime, timezone

from app.core.plan_policy import PlanPolicy
from app.db.repositories.users import UsersRepository
from app.presenters.users import compute_initials
from app.schemas.bands import BandResponse, BandSummary


async def to_band_summary(doc: dict, user_id: str, policy: PlanPolicy) -> BandSummary:
    bid = str(doc['_id'])
    return BandSummary(
        id=bid, name=doc['name'], owner_id=str(doc['owner_id']),
        user_role='owner' if str(doc['owner_id']) == user_id else 'member',
        seats_used=len(doc['members']), seat_limit=await policy.seat_limit(bid),
        active=await policy.is_band_active(bid),
    )


async def to_band_response(doc: dict, user_id: str, policy: PlanPolicy) -> BandResponse:
    summary = await to_band_summary(doc, user_id, policy)
    users = await UsersRepository().get_by_ids([m['user_id'] for m in doc['members']])
    members = []
    for member in doc['members']:
        uid = str(member['user_id'])
        name = users.get(uid, {}).get('display_name')
        members.append({'user_id': uid, 'role': member['role'],
                        'display_name': name, 'initials': compute_initials(name)})
    transfer = doc.get('pending_transfer')
    pending = None
    if transfer:
        expiry = transfer['expires_at']
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry > datetime.now(timezone.utc):
            pending = {'to_user_id': str(transfer['to_user_id']),
                       'requested_at': transfer['requested_at'], 'expires_at': expiry}
    return BandResponse(
        **summary.model_dump(), members=members, pending_transfer=pending,
        created_at=doc['created_at'], updated_at=doc['updated_at'],
    )
