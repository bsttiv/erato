from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.errors import ConflictError
from app.db.client import get_db


class UsersRepository:
    """Repository managing the 'users' collection per the Approved Data Model."""

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.users

    async def ensure_indexes(self) -> None:
        """Create indexes defined in design.md for the users collection."""
        await self.collection.create_indexes([
            IndexModel([("email", ASCENDING)], unique=True, name="uq_users_email"),
        ])

    async def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> Dict[str, Any]:
        """Create a new user with unique email constraint."""
        normalized_email = email.strip().lower()
        now = datetime.now(timezone.utc)

        user_doc: Dict[str, Any] = {
            "email": normalized_email,
            "password_hash": password_hash,
            "display_name": display_name.strip(),
            "token_version": 1,
            "created_at": now,
        }

        try:
            result = await self.collection.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            return user_doc
        except DuplicateKeyError:
            raise ConflictError("El correo electrónico ya está registrado")

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up user by email (case-insensitive)."""
        normalized_email = email.strip().lower()
        return await self.collection.find_one({"email": normalized_email})

    async def get_by_id(self, user_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """Look up user by document ObjectId or valid string representation."""
        if isinstance(user_id, str):
            if not ObjectId.is_valid(user_id):
                return None
            oid = ObjectId(user_id)
        else:
            oid = user_id

        return await self.collection.find_one({"_id": oid})

    async def increment_token_version(self, user_id: Union[str, ObjectId]) -> Optional[int]:
        """Increment user's token version for global revocation of issued access tokens."""
        if isinstance(user_id, str):
            if not ObjectId.is_valid(user_id):
                return None
            oid = ObjectId(user_id)
        else:
            oid = user_id

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$inc": {"token_version": 1}},
            return_document=True,
        )
        if result:
            return result.get("token_version", 1)
        return None
