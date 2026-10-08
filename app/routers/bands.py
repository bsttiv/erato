from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from app.core.plan_policy import PlanPolicy
from app.db.repositories.users import UsersRepository
from app.deps import current_user_required, get_plan_policy
from app.routers.compositions import compute_initials
from app.schemas.bands import (BandCreate, BandRename, BandResponse, BandSummary,
                               BandInviteCreate, BandInviteResponse, BandInviteSummary)
from app.services.bands_service import BandsService

router = APIRouter(prefix='/api/bands', tags=['bands'])


def get_service(policy: PlanPolicy = Depends(get_plan_policy)) -> BandsService:
    return BandsService(policy)


async def _to_summary(doc: dict, user_id: str, policy: PlanPolicy) -> BandSummary:
    bid = str(doc['_id'])
    return BandSummary(
        id=bid, name=doc['name'], owner_id=str(doc['owner_id']),
        user_role='owner' if str(doc['owner_id']) == user_id else 'member',
        seats_used=len(doc['members']), seat_limit=await policy.seat_limit(bid),
        active=await policy.is_band_active(bid),
    )


async def _to_response(doc: dict, user_id: str, policy: PlanPolicy) -> BandResponse:
    summary = await _to_summary(doc, user_id, policy)
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


@router.post('', response_model=BandResponse, status_code=status.HTTP_201_CREATED)
async def create_band(
    body: BandCreate, user: dict = Depends(current_user_required),
    service: BandsService = Depends(get_service),
) -> BandResponse:
    doc = await service.create(user, body.name)
    return await _to_response(doc, user['id'], service.policy)


@router.get('', response_model=list[BandSummary])
async def list_bands(
    user: dict = Depends(current_user_required), service: BandsService = Depends(get_service),
) -> list[BandSummary]:
    return [await _to_summary(doc, user['id'], service.policy)
            for doc in await service.list_for_user(user['id'])]


@router.get('/{band_id}', response_model=BandResponse)
async def get_band(
    band_id: str, user: dict = Depends(current_user_required),
    service: BandsService = Depends(get_service),
) -> BandResponse:
    doc = await service.get_for_user(band_id, user['id'])
    return await _to_response(doc, user['id'], service.policy)


@router.patch('/{band_id}', response_model=BandResponse)
async def rename_band(
    band_id: str, body: BandRename, user: dict = Depends(current_user_required),
    service: BandsService = Depends(get_service),
) -> BandResponse:
    doc = await service.rename(band_id, user['id'], body.name)
    return await _to_response(doc, user['id'], service.policy)


@router.post('/{band_id}/invites', response_model=BandInviteResponse, status_code=201)
async def create_invite(
    band_id: str, body: BandInviteCreate = BandInviteCreate(),
    user: dict = Depends(current_user_required), service: BandsService = Depends(get_service),
) -> dict:
    return await service.create_invite(band_id, user['id'])


@router.get('/{band_id}/invites', response_model=list[BandInviteSummary])
async def list_invites(
    band_id: str, user: dict = Depends(current_user_required),
    service: BandsService = Depends(get_service),
) -> list[dict]:
    return await service.list_invites(band_id, user['id'])


@router.delete('/{band_id}/invites/{invite_id}', status_code=204)
async def delete_invite(
    band_id: str, invite_id: str, user: dict = Depends(current_user_required),
    service: BandsService = Depends(get_service),
) -> None:
    await service.delete_invite(band_id, user['id'], invite_id)
