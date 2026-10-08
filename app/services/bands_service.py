from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

from bson import ObjectId
from pydantic import ValidationError as SchemaValidationError
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import ForbiddenError, NotFoundError, PlanGateError, ValidationError
from app.core.plan_policy import PlanPolicy
from app.core.security.tokens import mint_opaque_token
from app.db.repositories.bands import BandsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.schemas.bands import BandCreate
from app.settings import get_settings


class BandsService:
    """Core band operations, including gate-free host creation and compensation."""

    def __init__(self, policy: PlanPolicy, db: Optional[AsyncDatabase] = None):
        self.policy = policy
        self.bands = BandsRepository(db)
        self.invitations = InvitationsRepository(db)

    async def create(self, user: Mapping[str, Any], name: str) -> dict:
        if not await self.policy.can_create_band(user['id']):
            raise PlanGateError('plan_gate_band_creation')
        return await self.create_for_user(user['id'], name)

    async def create_for_user(self, user_id: str, name: str) -> dict:
        try:
            body = BandCreate(name=name)
        except SchemaValidationError as exc:
            raise ValidationError() from exc
        return await self.bands.insert(body.name, user_id)

    async def delete_band(self, band_id: str) -> None:
        if await self.bands.get_by_id(band_id) is None:
            return
        await self.bands.db.compositions.update_many(
            {'band_id': ObjectId(band_id)},
            {'$set': {'band_id': None, 'band_editable': False, 'members': [],
                      'updated_at': datetime.now(timezone.utc)}},
        )
        await self.invitations.delete_by_band(band_id)
        await self.bands.collection.delete_one({'_id': ObjectId(band_id)})

    async def list_for_user(self, user_id: str) -> list[dict]:
        return await self.bands.list_by_member(user_id)

    async def get_for_user(self, band_id: str, user_id: str) -> dict:
        band = await self.bands.get_by_id(band_id)
        if band is None or not any(str(m['user_id']) == user_id for m in band['members']):
            raise NotFoundError()
        return band

    async def rename(self, band_id: str, user_id: str, name: str) -> dict:
        band = await self.get_for_user(band_id, user_id)
        if str(band['owner_id']) != user_id:
            raise ForbiddenError()
        renamed = await self.bands.rename(band_id, name)
        if renamed is None:
            raise NotFoundError()
        return renamed

    async def _require_owner(self, band_id: str, user_id: str) -> dict:
        band = await self.get_for_user(band_id, user_id)
        if str(band['owner_id']) != user_id:
            raise ForbiddenError()
        return band

    async def create_invite(self, band_id: str, user_id: str) -> dict:
        await self._require_owner(band_id, user_id)
        if not await self.policy.is_band_active(band_id):
            raise ForbiddenError('La banda está inactiva', code='band_inactive')
        settings = get_settings()
        token, digest = mint_opaque_token()
        url = settings.build_app_url(f'/invite/{token}')
        invitation = await self.invitations.create_band_invitation(
            band_id, digest,
            datetime.now(timezone.utc) + timedelta(days=settings.invite_token_ttl_days), user_id,
        )
        return {'id': str(invitation['_id']), 'invite_url': url,
                'expires_at': invitation['expires_at']}

    async def list_invites(self, band_id: str, user_id: str) -> list[dict]:
        await self._require_owner(band_id, user_id)
        return [{'id': str(doc['_id']), 'expires_at': doc['expires_at']}
                for doc in await self.invitations.list_by_band(band_id)]

    async def delete_invite(self, band_id: str, user_id: str, invite_id: str) -> None:
        await self._require_owner(band_id, user_id)
        if not ObjectId.is_valid(invite_id):
            raise NotFoundError('Invitación no encontrada')
        result = await self.invitations.collection.delete_one({
            '_id': ObjectId(invite_id), 'target.type': 'band', 'target.id': ObjectId(band_id),
        })
        if not result.deleted_count:
            raise NotFoundError('Invitación no encontrada')

    async def redeem_invite(self, token_hash: str, user_id: str) -> dict:
        invitation = await self.invitations.redeem_band_invitation(token_hash)
        band_id = str(invitation['target']['id'])
        if not await self.policy.is_band_active(band_id):
            raise ForbiddenError('La banda está inactiva', code='band_inactive')
        limit = await self.policy.seat_limit(band_id)
        result = await self.bands.add_member_if_seat(band_id, user_id, limit)
        return {'band_id': band_id, 'status': result}
