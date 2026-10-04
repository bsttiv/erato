from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from bson import ObjectId
from pymongo import AsyncMongoClient

from app.db.client import get_db


class SectionRevisionsRepository:
    """Repository for managing versioned section snapshots in MongoDB."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db if db is not None else get_db()
        self.collection = self.db.section_revisions

    def _to_oid(self, val: Union[str, ObjectId]) -> ObjectId:
        if isinstance(val, ObjectId):
            return val
        return ObjectId(val)

    async def ensure_indexes(self) -> None:
        """Create unique compound index on composition_id, section, rev descending."""
        await self.collection.create_index(
            [("composition_id", 1), ("section", 1), ("rev", -1)],
            unique=True,
            name="uq_section_revisions_comp_section_rev",
        )

    async def insert_revision(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        rev: int,
        content: Any,
        author_id: Union[str, ObjectId],
        created_at: Optional[datetime] = None,
    ) -> dict:
        """Insert a snapshot of section content at revision rev."""
        cid = self._to_oid(composition_id)
        aid = self._to_oid(author_id)
        now = created_at or datetime.now(timezone.utc)
        doc = {
            "composition_id": cid,
            "section": section,
            "rev": rev,
            "content": content,
            "author_id": aid,
            "created_at": now,
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc

    async def get_by_rev(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        rev: int,
    ) -> Optional[dict]:
        """Fetch revision by exact rev."""
        cid = self._to_oid(composition_id)
        return await self.collection.find_one(
            {"composition_id": cid, "section": section, "rev": rev}
        )

    async def prune_revisions(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        max_rev: int,
    ) -> int:
        """Delete revisions with rev <= max_rev for retention management."""
        cid = self._to_oid(composition_id)
        res = await self.collection.delete_many(
            {"composition_id": cid, "section": section, "rev": {"$lte": max_rev}}
        )
        return res.deleted_count

    async def list_revisions(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        skip: int = 0,
        limit: int = 50,
        before_rev: Optional[int] = None,
    ) -> List[dict]:
        """List snapshots for a section sorted by rev descending."""
        cid = self._to_oid(composition_id)
        query: dict = {"composition_id": cid, "section": section}
        if before_rev is not None:
            query["rev"] = {"$lt": before_rev}
        cursor = (
            self.collection.find(query)
            .sort("rev", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)


    async def get_newest_at_or_below(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        rev: int,
    ) -> Optional[dict]:
        """Fetch the most recent revision snapshot with rev <= given rev."""
        cid = self._to_oid(composition_id)
        cursor = (
            self.collection.find(
                {"composition_id": cid, "section": section, "rev": {"$lte": rev}}
            )
            .sort("rev", -1)
            .limit(1)
        )
        items = await cursor.to_list(length=1)
        return items[0] if items else None

    async def delete_by_composition(
        self,
        composition_id: Union[str, ObjectId],
    ) -> int:
        """Cascade delete all revisions belonging to a composition."""
        cid = self._to_oid(composition_id)
        res = await self.collection.delete_many({"composition_id": cid})
        return res.deleted_count
