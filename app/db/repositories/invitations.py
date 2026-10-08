from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import GoneError, NotFoundError
from app.db.client import get_db


class InvitationsRepository:
    """Repository for reusable band invitations and legacy token rejection."""

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.invitations

    async def ensure_indexes(self) -> None:
        """Create indexes defined in design.md for the invitations collection."""
        await self.collection.create_indexes([
            IndexModel([("token_hash", ASCENDING)], unique=True, name="uq_invitations_token_hash"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_invitations_expires_at"),
            IndexModel([("target.type", ASCENDING), ("target.id", ASCENDING)], name="idx_invitations_target"),
        ])

    async def get_by_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Look up an invitation by token digest."""
        return await self.collection.find_one({"token_hash": token_hash})

    async def get_by_id(self, invitation_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """Look up an invitation by ID."""
        if isinstance(invitation_id, str):
            if not ObjectId.is_valid(invitation_id):
                return None
            oid = ObjectId(invitation_id)
        else:
            oid = invitation_id
        return await self.collection.find_one({"_id": oid})

    async def revoke_invitation(self, invitation_id: Union[str, ObjectId]) -> bool:
        """Revoke / delete an invitation by ID."""
        if isinstance(invitation_id, str):
            if not ObjectId.is_valid(invitation_id):
                return False
            oid = ObjectId(invitation_id)
        else:
            oid = invitation_id

        res = await self.collection.delete_one({"_id": oid})
        return res.deleted_count > 0

    async def create_band_invitation(
        self,
        band_id: Union[str, ObjectId],
        token_hash: str,
        expires_at: datetime,
        created_by: Union[str, ObjectId],
    ) -> Dict[str, Any]:
        """Create a reusable band invitation without a composition role."""
        doc = {
            "target": {"type": "band", "id": ObjectId(band_id)},
            "token_hash": token_hash,
            "expires_at": expires_at,
            "created_by": ObjectId(created_by),
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def list_by_band(self, band_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"target.type": "band", "target.id": ObjectId(band_id)}
        ).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def delete_by_band(self, band_id: Union[str, ObjectId]) -> int:
        result = await self.collection.delete_many(
            {"target.type": "band", "target.id": ObjectId(band_id)}
        )
        return result.deleted_count

    async def redeem_band_invitation(self, token_hash: str) -> Dict[str, Any]:
        """Validate a reusable band token and reject legacy composition tokens."""
        doc = await self.get_by_hash(token_hash)
        if not doc:
            raise NotFoundError("Invitación no encontrada")
        if (doc.get("target") or {}).get("type") != "band":
            raise GoneError("Invitación antigua no disponible", code="invitation_legacy")
        expiry = doc["expires_at"]
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            raise GoneError("Invitación expirada", code="invitation_expired")
        return doc
