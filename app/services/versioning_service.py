import logging
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId

from app.core.errors import NotFoundError, PlanGateError, SectionConflictError
from app.core.plan_policy import PlanPolicy, UnlimitedPlanPolicy
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository

logger = logging.getLogger("erato.versioning")

VALID_SECTIONS = {"lyrics", "chords", "tablature"}


class VersioningService:
    """Business logic for atomic section updates, versioning, conflict detection, snapshots, and history."""

    def __init__(
        self,
        compositions_repo: Optional[CompositionsRepository] = None,
        revisions_repo: Optional[SectionRevisionsRepository] = None,
        users_repo: Optional[UsersRepository] = None,
        policy: Optional[PlanPolicy] = None,
    ) -> None:
        self.compositions_repo = compositions_repo or CompositionsRepository()
        self.revisions_repo = revisions_repo or SectionRevisionsRepository()
        self.users_repo = users_repo or UsersRepository()
        self.policy = policy or UnlimitedPlanPolicy()

    def _validate_section(self, section: str) -> None:
        """Validate section name against allowed versioned sections before any DB access."""
        if section not in VALID_SECTIONS:
            raise NotFoundError(f"Sección no encontrada: {section}")

    async def _check_history_gate(self, user_id: str) -> None:
        """Verify the acting user is entitled to access history under the active plan policy."""
        if not await self.policy.can_view_history(user_id):
            raise PlanGateError("plan_gate_history")

    async def _resolve_authors(self, author_ids: List[Any]) -> Dict[str, dict]:
        """Batch-resolve user documents for a list of author IDs."""
        valid_ids = [aid for aid in author_ids if aid]
        if not valid_ids:
            return {}
        return await self.users_repo.get_by_ids(valid_ids)

    async def list_history(
        self,
        composition_id: str,
        section: str,
        user_id: str,
        limit: int = 20,
        before_rev: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List version snapshots for a section with pagination, newest first."""
        self._validate_section(section)
        await self._check_history_gate(user_id)

        raw_items = await self.revisions_repo.list_revisions(
            composition_id=composition_id,
            section=section,
            limit=limit + 1,
            before_rev=before_rev,
        )

        if len(raw_items) > limit:
            page_items = raw_items[:limit]
            next_before_rev = page_items[-1]["rev"]
        else:
            page_items = raw_items
            next_before_rev = None

        author_ids = list({d["author_id"] for d in page_items if d.get("author_id")})
        user_map = await self._resolve_authors(author_ids)

        items = []
        for d in page_items:
            aid = d.get("author_id")
            author_info: Optional[Dict[str, Optional[str]]] = None
            if aid:
                aid_str = str(aid)
                u = user_map.get(aid_str)
                author_info = {
                    "id": aid_str,
                    "display_name": u.get("display_name") if u else None,
                }
            items.append(
                {
                    "rev": d["rev"],
                    "author": author_info,
                    "created_at": d["created_at"],
                }
            )

        return {"items": items, "next_before_rev": next_before_rev}

    async def get_history_revision(
        self,
        composition_id: str,
        section: str,
        rev: int,
        user_id: str,
    ) -> Dict[str, Any]:
        """Fetch a specific historical snapshot with author details."""
        self._validate_section(section)
        await self._check_history_gate(user_id)

        snap = await self.revisions_repo.get_by_rev(
            composition_id=composition_id,
            section=section,
            rev=rev,
        )
        if not snap:
            raise NotFoundError("Versión no encontrada")

        author_info: Optional[Dict[str, Optional[str]]] = None
        aid = snap.get("author_id")
        if aid:
            aid_str = str(aid)
            u = await self.users_repo.get_by_id(aid)
            author_info = {
                "id": aid_str,
                "display_name": u.get("display_name") if u else None,
            }

        return {
            "rev": snap["rev"],
            "content": snap["content"],
            "author": author_info,
            "created_at": snap["created_at"],
        }

    async def restore_history_revision(
        self,
        composition_id: str,
        section: str,
        rev: int,
        user_id: str,
        expected_rev: int,
    ) -> Tuple[Any, int]:
        """Restore a historical snapshot by saving its content as a new revision."""
        self._validate_section(section)
        await self._check_history_gate(user_id)

        snap = await self.revisions_repo.get_by_rev(
            composition_id=composition_id,
            section=section,
            rev=rev,
        )
        if not snap:
            raise NotFoundError("Versión no encontrada")

        return await self.update_versioned_section(
            composition_id=composition_id,
            section_name=section,
            content=snap["content"],
            author_id=user_id,
            expected_rev=expected_rev,
        )

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
