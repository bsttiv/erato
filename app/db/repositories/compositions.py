from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from pymongo import ASCENDING, IndexModel, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.db.client import get_db



class CompositionsRepository:
    """Repository managing the 'compositions' collection per the Approved Data Model.
    
    Embedded sections: chords, tablature, lyrics, todos, demos.
    Members: [{ user_id: ObjectId, role: 'editor' }]
    Indexes: owner_id, members.user_id, share_slug (unique, sparse).
    """

    def __init__(self, db: Optional[AsyncDatabase] = None) -> None:
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        return self._db if self._db is not None else get_db()

    @property
    def collection(self):
        return self.db.compositions

    async def detach_owner_band_compositions(self, user_id: str, band_id: str) -> None:
        """Detach only this owner's band compositions without preserving legacy roles."""
        await self.collection.update_many(
            {'owner_id': ObjectId(user_id), 'band_id': ObjectId(band_id)},
            {'$set': {'band_id': None, 'band_editable': False, 'members': [],
                      'updated_at': datetime.now(timezone.utc)}},
        )

    async def ensure_indexes(self) -> None:
        """Create indexes defined in design.md for the compositions collection."""
        await self.collection.create_indexes([
            IndexModel([("owner_id", ASCENDING)], name="idx_compositions_owner_id"),
            IndexModel([("band_id", ASCENDING)], name="idx_compositions_band_id"),
            IndexModel([("members.user_id", ASCENDING)], name="idx_compositions_members_user_id"),
            IndexModel([("share_slug", ASCENDING)], unique=True, sparse=True, name="uq_sparse_compositions_share_slug"),
        ])

    async def create_composition(
        self,
        owner_id: Union[str, ObjectId],
        title: str,
        visibility: str = "private",
        share_slug: Optional[str] = None,
        key: Optional[str] = None,
        bpm: Optional[int] = None,
        time_signature: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
        status: str = "idea",
        sections_enabled: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Create a new composition with empty embedded sections and metadata."""
        oid = ObjectId(owner_id) if isinstance(owner_id, str) else owner_id
        now = datetime.now(timezone.utc)

        doc: Dict[str, Any] = {
            "owner_id": oid,
            "title": title.strip(),
            "visibility": visibility,
            "key": key,
            "bpm": bpm,
            "time_signature": time_signature,
            "style_tags": style_tags if style_tags is not None else [],
            "status": status,
            "sections_enabled": sections_enabled if sections_enabled is not None else {
                "chords": True,
                "tablature": False,
                "lyrics": True,
                "demos": True,
                "todos": True,
            },
            "chords": None,
            "tablature": None,
            "lyrics": None,
            "todos": [],
            "demos": [],
            "members": [],
            "created_at": now,
            "updated_at": now,
        }

        if visibility == "public" and share_slug:
            doc["share_slug"] = share_slug

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_by_id(self, composition_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """Look up composition by document ObjectId."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        return await self.collection.find_one({"_id": oid})

    async def get_by_slug(self, share_slug: str) -> Optional[Dict[str, Any]]:
        """Look up composition by unguessable share slug."""
        return await self.collection.find_one({"share_slug": share_slug, "visibility": "public"})

    async def list_by_user(self, user_id: Union[str, ObjectId], band_ids: Optional[List[ObjectId]] = None) -> List[Dict[str, Any]]:
        """List owned compositions, eligible invited ones, and band shares."""
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        ids = [ObjectId(band_id) for band_id in (band_ids or [])]
        cursor = self.collection.find({
            "$or": [
                {"owner_id": oid},
                {"members.user_id": oid, "band_id": None},
                {"band_id": {"$in": ids}},
            ]
        }).sort("updated_at", -1)
        return await cursor.to_list(length=None)

    async def update_section(
        self,
        composition_id: Union[str, ObjectId],
        section_name: str,
        content: Any,
    ) -> Optional[Dict[str, Any]]:
        """Update an embedded section (chords, tablature, lyrics, todos, demos)."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    section_name: content,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        return result

    async def update_versioned_section(
        self,
        composition_id: Union[str, ObjectId],
        section: str,
        content: Any,
        expected_rev: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Atomically update a section with conditional expected_rev check.

        Returns the document BEFORE update, or None if the filter did not match.
        """
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        filter_doc: Dict[str, Any] = {"_id": oid}
        if expected_rev is not None:
            if expected_rev == 0:
                filter_doc["$or"] = [
                    {f"section_revs.{section}": 0},
                    {f"section_revs.{section}": {"$exists": False}},
                ]
            else:
                filter_doc[f"section_revs.{section}"] = expected_rev

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            filter_doc,
            {
                "$set": {
                    section: content,
                    "updated_at": now,
                },
                "$inc": {
                    f"section_revs.{section}": 1,
                },
            },
            return_document=ReturnDocument.BEFORE,
        )
        return result

    async def update_title(
        self,
        composition_id: Union[str, ObjectId],
        title: str,

    ) -> Optional[Dict[str, Any]]:
        """Update composition title."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"title": title.strip(), "updated_at": now}},
            return_document=True,
        )
        return result

    async def update_fields(
        self,
        composition_id: Union[str, ObjectId],
        fields: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update allowed top-level metadata fields."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        allowed_keys = {
            "title",
            "key",
            "bpm",
            "time_signature",
            "style_tags",
            "status",
            "sections_enabled",
        }
        set_dict = {k: v for k, v in fields.items() if k in allowed_keys and v is not None}
        if "title" in set_dict and isinstance(set_dict["title"], str):
            set_dict["title"] = set_dict["title"].strip()

        now = datetime.now(timezone.utc)
        set_dict["updated_at"] = now

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": set_dict},
            return_document=True,
        )
        return result

    async def update_visibility(
        self,
        composition_id: Union[str, ObjectId],
        visibility: str,
        share_slug: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update visibility. Sets share_slug on public, unsets on private."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        now = datetime.now(timezone.utc)
        update_op: Dict[str, Any] = {"$set": {"visibility": visibility, "updated_at": now}}

        if visibility == "public" and share_slug:
            update_op["$set"]["share_slug"] = share_slug
        elif visibility == "private":
            update_op["$unset"] = {"share_slug": ""}

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            update_op,
            return_document=True,
        )
        return result

    async def add_member(
        self,
        composition_id: Union[str, ObjectId],
        user_id: Union[str, ObjectId],
        role: str = "editor",
    ) -> Optional[Dict[str, Any]]:
        """Add or update a member with a role in the composition."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        uid = ObjectId(user_id) if isinstance(user_id, str) else user_id

        # First remove if already present to avoid duplicates
        await self.collection.update_one(
            {"_id": oid},
            {"$pull": {"members": {"user_id": uid}}},
        )

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {
                "$push": {"members": {"user_id": uid, "role": role}},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        return result

    async def remove_member(
        self,
        composition_id: Union[str, ObjectId],
        user_id: Union[str, ObjectId],
    ) -> Optional[Dict[str, Any]]:
        """Remove a member from the composition."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        uid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {
                "$pull": {"members": {"user_id": uid}},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        return result

    async def delete_composition(self, composition_id: Union[str, ObjectId]) -> bool:
        """Delete a composition document."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return False
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        res = await self.collection.delete_one({"_id": oid})
        return res.deleted_count > 0

    # Note on demo limits (referencing design.md, Approved Data Model):
    # The author expects few demos per composition (5–10). Demos are therefore embedded directly
    # in the composition document as small, bounded sub-documents (rarely exceeding a few KB).
    # Per tasks.md Task 4.5, this 5–10 expected cap is not hard-validated with an artificially rigid
    # cutoff, but safely bounded to prevent document bloating.

    async def add_demo(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
        cloudinary_public_id: str,
        title: str,
        duration_s: float,
        uploaded_by: Union[str, ObjectId],
    ) -> Optional[Dict[str, Any]]:
        """Add a demo without a quota."""
        return await self.add_demo_if_below(
            composition_id, demo_id, cloudinary_public_id, title, duration_s, uploaded_by, None,
        )

    async def add_demo_if_below(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
        cloudinary_public_id: str,
        title: str,
        duration_s: float,
        uploaded_by: Union[str, ObjectId],
        limit: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """Atomically append a demo only while the quota has room; None is unbounded."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        uploader_oid = ObjectId(uploaded_by) if isinstance(uploaded_by, str) else uploaded_by
        now = datetime.now(timezone.utc)

        demo_subdoc = {
            "demo_id": demo_id,
            "cloudinary_public_id": cloudinary_public_id,
            "title": title.strip(),
            "duration_s": float(duration_s),
            "uploaded_by": uploader_oid,
            "uploaded_at": now,
        }

        filter_doc: Dict[str, Any] = {"_id": oid}
        if limit is not None:
            filter_doc[f"demos.{limit - 1}"] = {"$exists": False}

        # Push to demos and update timestamp
        result = await self.collection.find_one_and_update(
            filter_doc,
            {
                "$push": {"demos": demo_subdoc},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        return result

    async def remove_demo(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Remove a demo sub-document by demo_id."""
        if isinstance(composition_id, str):
            if not ObjectId.is_valid(composition_id):
                return None
            oid = ObjectId(composition_id)
        else:
            oid = composition_id

        now = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {
                "$pull": {"demos": {"demo_id": demo_id}},
                "$set": {"updated_at": now},
            },
            return_document=True,
        )
        return result

    async def get_demo(
        self,
        composition_id: Union[str, ObjectId],
        demo_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a specific demo sub-document inside composition."""
        doc = await self.get_by_id(composition_id)
        if not doc:
            return None
        for demo in doc.get("demos") or []:
            if demo.get("demo_id") == demo_id:
                return demo
        return None

    async def list_demos(
        self,
        composition_id: Union[str, ObjectId],
    ) -> List[Dict[str, Any]]:
        """List embedded demos for a composition."""
        doc = await self.get_by_id(composition_id)
        if not doc:
            return []
        return doc.get("demos") or []


    async def set_member_role(self, composition_id: Union[str, ObjectId],
                              user_id: Union[str, ObjectId], role: str) -> None:
        """Set an existing role or conditionally insert without duplicate members."""
        oid, uid = ObjectId(composition_id), ObjectId(user_id)
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {'_id': oid, 'members.user_id': uid},
            {'$set': {'members.$.role': role, 'updated_at': now}},
        )
        if not result.matched_count:
            await self.collection.update_one(
                {'_id': oid, 'members.user_id': {'$ne': uid}},
                {'$push': {'members': {'user_id': uid, 'role': role}},
                 '$set': {'updated_at': now}},
            )
