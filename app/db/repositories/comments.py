from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.db.client import get_db


class CommentsRepository:
    """Repository managing the 'composition_comments' collection per the Approved Data Model.
    
    Shape:
    - _id: ObjectId
    - composition_id: ObjectId
    - demo_id: str
    - author_id: ObjectId
    - timestamp_s: float
    - text: str
    - created_at: datetime
    
    Index: { composition_id: 1, demo_id: 1, created_at: 1 }
    """

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.composition_comments

    async def ensure_indexes(self) -> None:
        """Create compound index for fast timestamped demo comment lookups."""
        await self.collection.create_indexes([
            IndexModel(
                [
                    ("composition_id", ASCENDING),
                    ("demo_id", ASCENDING),
                    ("created_at", ASCENDING),
                ],
                name="idx_composition_demo_comments_created",
            )
        ])

    async def create_comment(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
        author_id: Union[str, ObjectId],
        timestamp_s: float,
        text: str,
    ) -> Dict[str, Any]:
        """Create a timestamp-anchored comment on a demo."""
        cid = ObjectId(composition_id) if isinstance(composition_id, str) else composition_id
        aid = ObjectId(author_id) if isinstance(author_id, str) else author_id

        doc: Dict[str, Any] = {
            "composition_id": cid,
            "demo_id": demo_id,
            "author_id": aid,
            "timestamp_s": float(timestamp_s),
            "text": text.strip(),
            "created_at": datetime.now(timezone.utc),
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def list_comments(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
    ) -> List[Dict[str, Any]]:
        """List comments for a demo ordered by created_at without loading the composition document."""
        cid = ObjectId(composition_id) if isinstance(composition_id, str) else composition_id
        cursor = self.collection.find(
            {"composition_id": cid, "demo_id": demo_id}
        ).sort("created_at", ASCENDING)
        return await cursor.to_list(length=None)
