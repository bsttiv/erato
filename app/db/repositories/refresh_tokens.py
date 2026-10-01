from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import UnauthorizedError
from app.db.client import get_db


class RefreshTokensRepository:
    """Repository managing the 'refresh_tokens' collection per the Approved Data Model.
    
    Shape:
    - _id: ObjectId
    - token_hash: str (unique SHA-256 digest)
    - user_id: ObjectId
    - family_id: str (rotation family identifier)
    - revoked: bool
    - expires_at: datetime (TTL index)
    - created_at: datetime
    """

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.refresh_tokens

    async def ensure_indexes(self) -> None:
        """Create indexes defined in design.md for the refresh_tokens collection."""
        await self.collection.create_indexes([
            IndexModel([("token_hash", ASCENDING)], unique=True, name="uq_refresh_tokens_hash"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_refresh_tokens_expires_at"),
            IndexModel([("family_id", ASCENDING)], name="idx_refresh_tokens_family_id"),
        ])

    async def create_token(
        self,
        token_hash: str,
        user_id: Union[str, ObjectId],
        family_id: str,
        expires_at: datetime,
    ) -> Dict[str, Any]:
        """Store a new refresh token digest within a rotation family."""
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)

        doc: Dict[str, Any] = {
            "token_hash": token_hash,
            "user_id": oid,
            "family_id": str(family_id),
            "revoked": False,
            "expires_at": expires_at,
            "created_at": now,
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def redeem_token(self, token_hash: str) -> Dict[str, Any]:
        """Redeem a refresh token digest.
        
        Single-use semantics:
        - If unexpired and unrevoked, marks the token as revoked and returns it.
        - If already revoked (reuse detection), invalidates the ENTIRE token family and raises UnauthorizedError.
        - If expired or not found, raises UnauthorizedError.
        """
        doc = await self.collection.find_one({"token_hash": token_hash})
        if not doc:
            raise UnauthorizedError("Token de actualización inválido")

        doc_exp = doc["expires_at"]
        if doc_exp.tzinfo is None:
            doc_exp = doc_exp.replace(tzinfo=timezone.utc)
        if doc_exp < datetime.now(timezone.utc):
            raise UnauthorizedError("Token de actualización expirado")

        if doc.get("revoked", False):
            # Reuse detected! Invalidate the entire family
            await self.invalidate_family(doc["family_id"])
            raise UnauthorizedError("Token de actualización ya utilizado o revocado")

        # Mark single-use token as revoked (consumed)
        await self.collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"revoked": True}},
        )
        doc["revoked"] = True
        return doc

    async def invalidate_family(self, family_id: str) -> int:
        """Revoke all tokens belonging to the given family identifier."""
        result = await self.collection.update_many(
            {"family_id": str(family_id)},
            {"$set": {"revoked": True}},
        )
        return result.modified_count
