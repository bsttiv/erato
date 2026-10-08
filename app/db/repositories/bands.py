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
        if result.matched_count:
            await self.collection.update_one(
                {'_id': ObjectId(band_id), 'pending_transfer.to_user_id': user},
                {'$set': {'pending_transfer': None}},
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

    async def request_transfer(self, band_id: str, owner_id: str, target_id: str,
                               now: datetime, expires_at: datetime) -> bool:
        result = await self.collection.update_one(
            {'_id': ObjectId(band_id), 'owner_id': ObjectId(owner_id),
             'members.user_id': ObjectId(target_id),
             '$or': [{'pending_transfer': None}, {'pending_transfer.expires_at': {'$lte': now}}]},
            {'$set': {'pending_transfer': {'to_user_id': ObjectId(target_id),
                      'requested_by': ObjectId(owner_id), 'requested_at': now,
                      'expires_at': expires_at}}},
        )
        return result.matched_count > 0

    async def clear_transfer(self, band_id: str, transfer: dict,
                             user_id: Optional[str] = None, now: Optional[datetime] = None) -> bool:
        query = {'_id': ObjectId(band_id),
                 'pending_transfer.to_user_id': transfer['to_user_id'],
                 'pending_transfer.expires_at': transfer['expires_at']}
        if user_id is not None:
            query['$or'] = [{'owner_id': ObjectId(user_id)},
                            {'pending_transfer.to_user_id': ObjectId(user_id)}]
            query['pending_transfer.expires_at'] = {'$eq': transfer['expires_at'], '$gt': now}
        result = await self.collection.update_one(query, {'$set': {'pending_transfer': None}})
        return result.matched_count > 0

    async def swap_owner(self, band_id: str, owner_id: str, target_id: str,
                         now: datetime) -> bool:
        owner, target = ObjectId(owner_id), ObjectId(target_id)
        result = await self.collection.update_one(
            {'_id': ObjectId(band_id), 'owner_id': owner, 'members.user_id': target,
             'pending_transfer.to_user_id': target, 'pending_transfer.expires_at': {'$gt': now}},
            {'$set': {'owner_id': target, 'members.$[old].role': 'member',
                      'members.$[new].role': 'owner', 'pending_transfer': None, 'updated_at': now}},
            array_filters=[{'old.user_id': owner}, {'new.user_id': target}],
        )
        return result.matched_count > 0
