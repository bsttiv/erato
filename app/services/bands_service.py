from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from bson import ObjectId
from pydantic import ValidationError as SchemaValidationError
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import ForbiddenError, NotFoundError, PlanGateError, ValidationError
from app.core.plan_policy import PlanPolicy
from app.db.repositories.bands import BandsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.schemas.bands import BandCreate


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
