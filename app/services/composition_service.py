import secrets
from typing import Any, Dict, List, Optional
from bson import ObjectId

from app.core.errors import NotFoundError
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.bands import BandsRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository


def generate_share_slug() -> str:
    """Generate a random 128-bit (16-byte) URL-safe slug for public links."""
    return secrets.token_urlsafe(16)


class CompositionService:
    """Framework-agnostic business logic for compositions and embedded sections."""

    def __init__(
        self,
        repo: Optional[CompositionsRepository] = None,
        revisions_repo: Optional[SectionRevisionsRepository] = None,
    ) -> None:
        self.repo = repo or CompositionsRepository()
        self.revisions_repo = revisions_repo or SectionRevisionsRepository()


    async def create_composition(
        self,
        owner_id: str,
        title: str,
        visibility: str = "private",
        key: Optional[str] = None,
        bpm: Optional[int] = None,
        time_signature: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
        status: str = "idea",
        sections_enabled: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Create a new composition for owner."""
        share_slug = generate_share_slug() if visibility == "public" else None
        return await self.repo.create_composition(
            owner_id=owner_id,
            title=title,
            visibility=visibility,
            share_slug=share_slug,
            key=key,
            bpm=bpm,
            time_signature=time_signature,
            style_tags=style_tags,
            status=status,
            sections_enabled=sections_enabled,
        )

    async def get_composition(self, composition_id: str) -> Dict[str, Any]:
        """Retrieve composition by id."""
        doc = await self.repo.get_by_id(composition_id)
        if not doc:
            raise NotFoundError("Composición no encontrada")
        return doc

    async def get_by_slug(self, slug: str) -> Dict[str, Any]:
        """Retrieve a public composition by its unguessable share slug."""
        doc = await self.repo.get_by_slug(slug)
        if not doc:
            raise NotFoundError("Composición no encontrada")
        return doc

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all compositions owned by or shared with user."""
        bands = await BandsRepository(self.repo.db).list_by_member(user_id)
        band_ids = [band["_id"] for band in bands]
        docs = await self.repo.list_by_user(user_id, band_ids)
        for doc in docs:
            invited = any(str(m["user_id"]) == user_id for m in doc.get("members", []))
            doc["via_band"] = (doc.get("band_id") in band_ids
                               and str(doc["owner_id"]) != user_id and not invited)
        return docs

    async def update_composition(
        self,
        composition_id: str,
        **fields: Any,
    ) -> Dict[str, Any]:
        """Update composition top-level fields (e.g. title, metadata)."""
        clean_fields = {k: v for k, v in fields.items() if v is not None}
        if clean_fields:
            updated = await self.repo.update_fields(composition_id, clean_fields)
            if not updated:
                raise NotFoundError("Composición no encontrada")
            return updated
        return await self.get_composition(composition_id)

    async def update_section(
        self,
        composition_id: str,
        section_name: str,
        content: Any,
    ) -> Dict[str, Any]:
        """Update an embedded section (chords, tablature, lyrics, todos)."""
        updated = await self.repo.update_section(composition_id, section_name, content)
        if not updated:
            raise NotFoundError("Composición no encontrada")
        return updated

    async def delete_composition(self, composition_id: str) -> bool:
        """Delete composition."""
        deleted = await self.repo.delete_composition(composition_id)
        if not deleted:
            raise NotFoundError("Composición no encontrada")
        await self.revisions_repo.delete_by_composition(composition_id)
        return True

