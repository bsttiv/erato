from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import GoneError, NotFoundError, UnauthorizedError
from app.db.client import get_db


class InvitationsRepository:
    """Repository managing the 'invitations' collection per the Approved Data Model.
    
    Shape:
    - _id: ObjectId
    - composition_id: ObjectId
    - token_hash: str (unique SHA-256 digest)
    - invited_email: Optional[str]
    - role: str ("editor")
    - expires_at: datetime (TTL index)
    - used_at: Optional[datetime] (null initially)
    - created_by: ObjectId
    """

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

    async def create_invitation(
        self,
        composition_id: Union[str, ObjectId],
        token_hash: str,
        expires_at: datetime,
        created_by: Union[str, ObjectId],
        invited_email: Optional[str] = None,
        role: str = "editor",
    ) -> Dict[str, Any]:
        """Create a new invitation record."""
        cid = ObjectId(composition_id) if isinstance(composition_id, str) else composition_id
        creator = ObjectId(created_by) if isinstance(created_by, str) else created_by

        doc: Dict[str, Any] = {
            "composition_id": cid,
            "token_hash": token_hash,
            "invited_email": invited_email.strip().lower() if invited_email else None,
            "role": role,
            "expires_at": expires_at,
            "used_at": None,
            "created_by": creator,
            "created_at": datetime.now(timezone.utc),
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

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

    async def list_by_composition(
        self,
        composition_id: Union[str, ObjectId],
    ) -> List[Dict[str, Any]]:
        """List all active or historical invitations for a composition."""
        cid = ObjectId(composition_id) if isinstance(composition_id, str) else composition_id
        cursor = self.collection.find({"composition_id": cid}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def redeem_invitation(self, token_hash: str) -> Dict[str, Any]:
        """Redeem an invitation digest idempotently.
        
        - If unexpired and unconsumed (used_at is null), sets used_at to now.
        - If already consumed, safely returns existing document (idempotent replay).
        - If expired, raises UnauthorizedError.
        - If not found, raises NotFoundError.
        """
        doc = await self.collection.find_one({"token_hash": token_hash})
        if not doc:
            raise NotFoundError("Invitación no encontrada")

        doc_exp = doc["expires_at"]
        if doc_exp.tzinfo is None:
            doc_exp = doc_exp.replace(tzinfo=timezone.utc)
        if doc_exp < datetime.now(timezone.utc):
            raise UnauthorizedError("Invitación expirada")

        if doc.get("used_at") is not None:
            # Already redeemed: idempotent return
            return doc

        now = datetime.now(timezone.utc)
        updated = await self.collection.find_one_and_update(
            {"token_hash": token_hash, "used_at": None},
            {"$set": {"used_at": now}},
            return_document=True,
        )
        return updated or doc

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
        """Validate a band token without consuming it; legacy flow stays separate."""
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
