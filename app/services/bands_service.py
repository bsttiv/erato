import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

from bson import ObjectId
from pydantic import ValidationError as SchemaValidationError
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import ConflictError, ForbiddenError, GoneError, NotFoundError, PlanGateError, ValidationError
from app.core.plan_policy import PlanPolicy
from app.core.security.tokens import mint_opaque_token
from app.db.repositories.bands import BandsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.schemas.bands import BandCreate
from app.settings import get_settings


class BandsService:
    """Core band operations, including gate-free host creation and compensation."""

    def __init__(self, policy: PlanPolicy, db: Optional[AsyncDatabase] = None):
        self.policy = policy
        self.bands = BandsRepository(db)
        self.compositions = CompositionsRepository(db)
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
        await self.compositions.detach_all_band_compositions(band_id)
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

    async def leave(self, band_id: str, user_id: str) -> None:
        band = await self.get_for_user(band_id, user_id)
        await self._detach_member(band, user_id)

    async def remove_member(self, band_id: str, owner_id: str, target_uid: str) -> None:
        band = await self._require_owner(band_id, owner_id)
        if any(str(m['user_id']) == target_uid for m in band['members']):
            await self._detach_member(band, target_uid)

    async def _detach_member(self, band: dict, user_id: str) -> None:
        if str(band['owner_id']) == user_id:
            raise ConflictError('Transfiere la propiedad antes de salir de la banda',
                                code='owner_must_transfer')
        band_id = str(band['_id'])
        await self.compositions.detach_owner_band_compositions(user_id, band_id)
        await self.bands.remove_member(band_id, user_id)

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

    @staticmethod
    def _transfer_expired(transfer: dict, now: datetime) -> bool:
        return transfer['expires_at'].replace(tzinfo=timezone.utc) <= now

    @staticmethod
    def _transfer_missing() -> NotFoundError:
        return NotFoundError('Solicitud de transferencia no encontrada', code='transfer_not_found')

    async def request_transfer(self, band_id: str, user_id: str, target_id: str) -> dict:
        await self._require_owner(band_id, user_id)
        if target_id == user_id:
            raise ValidationError('No puedes transferirte la banda a ti mismo')
        now = datetime.now(timezone.utc)
        if ObjectId.is_valid(target_id) and await self.bands.request_transfer(
            band_id, user_id, target_id, now, now + timedelta(days=14),
        ):
            return await self.bands.get_by_id(band_id)
        band = await self._require_owner(band_id, user_id)
        if not any(str(m['user_id']) == target_id for m in band['members']):
            raise ConflictError('El usuario no pertenece a la banda', code='not_a_band_member')
        transfer = band.get('pending_transfer')
        if transfer and not self._transfer_expired(transfer, now):
            raise ConflictError('Ya hay una transferencia pendiente', code='transfer_pending')
        raise self._transfer_missing()

    async def cancel_transfer(self, band_id: str, user_id: str) -> None:
        band = await self.get_for_user(band_id, user_id)
        transfer = band.get('pending_transfer')
        now = datetime.now(timezone.utc)
        if not transfer or self._transfer_expired(transfer, now):
            raise self._transfer_missing()
        if user_id not in (str(band['owner_id']), str(transfer['to_user_id'])):
            raise ForbiddenError()
        if not await self.bands.clear_transfer(band_id, transfer, user_id, now):
            raise self._transfer_missing()

    async def accept_transfer(self, band_id: str, user_id: str) -> dict:
        band = await self.bands.get_by_id(band_id)
        if band is None:
            raise NotFoundError()
        transfer = band.get('pending_transfer')
        member = any(str(m['user_id']) == user_id for m in band['members'])
        # A stale target may clean up its own request after a partially completed leave.
        if not member and (not transfer or str(transfer['to_user_id']) != user_id):
            raise NotFoundError()
        if not transfer:
            raise self._transfer_missing()
        if str(transfer['to_user_id']) != user_id:
            raise ForbiddenError()
        now = datetime.now(timezone.utc)
        if not member:
            await self.bands.clear_transfer(band_id, transfer)
            raise ConflictError('El usuario no pertenece a la banda', code='not_a_band_member')
        if self._transfer_expired(transfer, now):
            await self.bands.clear_transfer(band_id, transfer)
            raise GoneError('La solicitud de transferencia ha expirado', code='transfer_expired')
        owner_id = str(band['owner_id'])
        if not await self.policy.confirm_band_transfer(band_id, owner_id, user_id):
            raise ConflictError('No se ha confirmado la transferencia', code='transfer_not_confirmed')
        if not await self.bands.swap_owner(band_id, owner_id, user_id, datetime.now(timezone.utc)):
            logging.getLogger(__name__).warning('transfer_swap_lost band_id=%s', band_id)
            raise self._transfer_missing()
        return await self.bands.get_by_id(band_id)
