from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import ConflictError, NotFoundError
from app.db.client import get_db


class BandsRepository:
    """Store bands with embedded owner/member entries and pending transfers."""

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.bands

    async def ensure_indexes(self) -> None:
        await self.collection.create_indexes([
            IndexModel([("owner_id", ASCENDING)], name="idx_bands_owner_id"),
            IndexModel([("members.user_id", ASCENDING)], name="idx_bands_members_user_id"),
        ])

    async def insert(self, name: str, owner_id: str | ObjectId) -> dict:
        owner = ObjectId(owner_id)
        now = datetime.now(timezone.utc)
        doc = {
            "name": name.strip(), "owner_id": owner,
            "members": [{"user_id": owner, "role": "owner"}],
            "pending_transfer": None, "created_at": now, "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_by_id(self, band_id: str | ObjectId) -> Optional[dict]:
        if not ObjectId.is_valid(band_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(band_id)})

    async def list_by_member(self, user_id: str | ObjectId) -> list[dict]:
        cursor = self.collection.find({"members.user_id": ObjectId(user_id)}).sort("updated_at", -1)
        return await cursor.to_list(length=None)

    async def rename(self, band_id: str | ObjectId, name: str) -> Optional[dict]:
        if not ObjectId.is_valid(band_id):
            return None
        return await self.collection.find_one_and_update(
            {"_id": ObjectId(band_id)},
            {"$set": {"name": name.strip(), "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )

    async def remove_member(self, band_id: str | ObjectId, user_id: str | ObjectId) -> bool:
        """Remove a member idempotently while protecting the owner."""
        if not ObjectId.is_valid(band_id):
            return False
        user = ObjectId(user_id)
        result = await self.collection.update_one(
            {"_id": ObjectId(band_id), "owner_id": {"$ne": user}},
            {"$pull": {"members": {"user_id": user}},
             "$set": {"updated_at": datetime.now(timezone.utc)}},
        )
        return result.matched_count > 0

    async def add_member_if_seat(self, band_id: str | ObjectId, user_id: str | ObjectId,
                                 limit: Optional[int]) -> str:
        """Admit one member with a single conditional seat update."""
        uid = ObjectId(user_id)
        query = {'_id': ObjectId(band_id), 'members.user_id': {'$ne': uid}}
        if limit is not None:
            query['$expr'] = {'$lt': [{'$size': '$members'}, limit]}
        result = await self.collection.update_one(
            query, {'$push': {'members': {'user_id': uid, 'role': 'member'}},
                    '$set': {'updated_at': datetime.now(timezone.utc)}},
        )
        if result.matched_count:
            return 'joined'
        band = await self.get_by_id(band_id)
        if band is None:
            raise NotFoundError()
        if any(m['user_id'] == uid for m in band['members']):
            return 'already_member'
        raise ConflictError('La banda no tiene plazas disponibles', code='band_full')
