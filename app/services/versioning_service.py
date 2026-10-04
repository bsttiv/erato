import logging
from typing import Any, Dict, Optional, Tuple
from bson import ObjectId

from app.core.errors import NotFoundError, SectionConflictError
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository

logger = logging.getLogger("erato.versioning")


class VersioningService:
    """Business logic for atomic section updates, versioning, conflict detection, and snapshots."""

    def __init__(
        self,
        compositions_repo: Optional[CompositionsRepository] = None,
        revisions_repo: Optional[SectionRevisionsRepository] = None,
        users_repo: Optional[UsersRepository] = None,
    ) -> None:
        self.compositions_repo = compositions_repo or CompositionsRepository()
        self.revisions_repo = revisions_repo or SectionRevisionsRepository()
        self.users_repo = users_repo or UsersRepository()

    async def update_versioned_section(
        self,
        composition_id: str,
        section_name: str,
        content: Any,
        author_id: str,
        expected_rev: Optional[int] = None,
    ) -> Tuple[Any, int]:
        """Atomically update a section with conditional expected_rev check.

        Returns (updated_content, new_rev).
        Raises NotFoundError if composition does not exist.
        Raises SectionConflictError if expected_rev does not match current_rev.
        """
        before = await self.compositions_repo.update_versioned_section(
            composition_id=composition_id,
            section=section_name,
            content=content,
            expected_rev=expected_rev,
        )

        if before is None:
            # Re-read composition to differentiate 404 from 409
            comp = await self.compositions_repo.get_by_id(composition_id)
            if not comp:
                raise NotFoundError("Composición no encontrada")

            # Stale revision conflict (409)
            current_rev = (comp.get("section_revs") or {}).get(section_name, 0)
            current_content = comp.get(section_name)

            # Resolve author and timestamp from the latest snapshot <= current_rev
            author: Optional[Dict[str, Optional[str]]] = None
            updated_at = comp.get("updated_at")

            try:
                snap = await self.revisions_repo.get_newest_at_or_below(
                    composition_id, section_name, current_rev
                )
                if snap and snap.get("author_id"):
                    aid = snap["author_id"]
                    user = await self.users_repo.get_by_id(aid)
                    author = {
                        "id": str(aid),
                        "display_name": user.get("display_name") if user else None,
                    }
                    if snap.get("created_at"):
                        updated_at = snap["created_at"]
            except Exception:
                logger.exception("Failed to resolve author for section conflict")

            raise SectionConflictError(
                section=section_name,
                current_rev=current_rev,
                content=current_content,
                author=author,
                updated_at=updated_at,
            )

        # Update succeeded: compute new_rev
        prev_rev = (before.get("section_revs") or {}).get(section_name, 0)
        new_rev = prev_rev + 1

        # Snapshot insertion and pruning if content changed
        if before.get(section_name) != content:
            try:
                await self.revisions_repo.insert_revision(
                    composition_id=composition_id,
                    section=section_name,
                    rev=new_rev,
                    content=content,
                    author_id=author_id,
                )
                if new_rev > 50:
                    await self.revisions_repo.prune_revisions(
                        composition_id=composition_id,
                        section=section_name,
                        max_rev=new_rev - 50,
                    )
            except Exception:
                logger.exception("Failed to write or prune section revision snapshot")

        return content, new_rev
