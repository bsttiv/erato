import secrets
from typing import Any, Dict, List, Optional
from bson import ObjectId

from app.core.errors import NotFoundError
from app.db.repositories.compositions import CompositionsRepository


def generate_share_slug() -> str:
    """Generate a random 128-bit (16-byte) URL-safe slug for public links."""
    return secrets.token_urlsafe(16)


class CompositionService:
    """Framework-agnostic business logic for compositions and embedded sections."""

    def __init__(self, repo: Optional[CompositionsRepository] = None) -> None:
        self.repo = repo or CompositionsRepository()

    async def create_composition(
        self,
        owner_id: str,
        title: str,
        visibility: str = "private",
    ) -> Dict[str, Any]:
        """Create a new composition for owner."""
        share_slug = generate_share_slug() if visibility == "public" else None
        return await self.repo.create_composition(
            owner_id=owner_id,
            title=title,
            visibility=visibility,
            share_slug=share_slug,
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
        return await self.repo.list_by_user(user_id)

    async def update_composition(
        self,
        composition_id: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update composition top-level fields (e.g. title)."""
        if title is not None:
            updated = await self.repo.update_title(composition_id, title)
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
        return True
