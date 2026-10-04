from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from fastapi import APIRouter, Depends, Path, Query, status

from app.core.errors import NotFoundError, PlanGateError
from app.core.permissions import Action
from app.core.plan_policy import PlanPolicy
from app.deps import AuthContext, get_plan_policy, require
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository
from app.schemas.compositions import (
    ChordsWriteResponse,
    LyricsWriteResponse,
    TablatureWriteResponse,
)
from app.schemas.history import (
    HistoryAuthor,
    HistoryDetailResponse,
    HistoryItemSummary,
    HistoryListResponse,
)
from app.services.versioning_service import VersioningService

router = APIRouter(prefix="/api/compositions/{composition_id}/history", tags=["history"])

VALID_SECTIONS = {"lyrics", "chords", "tablature"}


def get_versioning_service() -> VersioningService:
    return VersioningService()


def get_revisions_repo() -> SectionRevisionsRepository:
    return SectionRevisionsRepository()


def get_users_repo() -> UsersRepository:
    return UsersRepository()


def _validate_section(section: str) -> None:
    if section not in VALID_SECTIONS:
        raise NotFoundError(f"Sección no encontrada: {section}")


@router.get(
    "/{section}",
    response_model=HistoryListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_history(
    composition_id: str,
    section: str = Path(...),
    limit: int = Query(20, ge=1, le=50),
    before_rev: Optional[int] = Query(None, ge=1),
    auth: AuthContext = Depends(require(Action.EDIT)),
    policy: PlanPolicy = Depends(get_plan_policy),
    revisions_repo: SectionRevisionsRepository = Depends(get_revisions_repo),
    users_repo: UsersRepository = Depends(get_users_repo),
) -> Any:
    _validate_section(section)

    user_id = auth.user["id"]
    if not await policy.can_view_history(user_id):
        raise PlanGateError("plan_gate_history")

    raw_items = await revisions_repo.list_revisions(
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
    user_map: Dict[str, dict] = {}
    if author_ids:
        user_map = await users_repo.get_by_ids(author_ids)

    items: List[HistoryItemSummary] = []
    for d in page_items:
        aid = d.get("author_id")
        author: Optional[HistoryAuthor] = None
        if aid:
            aid_str = str(aid)
            u = user_map.get(aid_str)
            author = HistoryAuthor(
                id=aid_str,
                display_name=u.get("display_name") if u else None,
            )
        items.append(
            HistoryItemSummary(
                rev=d["rev"],
                author=author,
                created_at=d["created_at"],
            )
        )

    return HistoryListResponse(items=items, next_before_rev=next_before_rev)


@router.get(
    "/{section}/{rev}",
    response_model=HistoryDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_history_revision(
    composition_id: str,
    section: str = Path(...),
    rev: int = Path(..., ge=1),
    auth: AuthContext = Depends(require(Action.EDIT)),
    policy: PlanPolicy = Depends(get_plan_policy),
    revisions_repo: SectionRevisionsRepository = Depends(get_revisions_repo),
    users_repo: UsersRepository = Depends(get_users_repo),
) -> Any:
    _validate_section(section)

    user_id = auth.user["id"]
    if not await policy.can_view_history(user_id):
        raise PlanGateError("plan_gate_history")

    snap = await revisions_repo.get_by_rev(
        composition_id=composition_id,
        section=section,
        rev=rev,
    )
    if not snap:
        raise NotFoundError("Versión no encontrada")

    author: Optional[HistoryAuthor] = None
    aid = snap.get("author_id")
    if aid:
        aid_str = str(aid)
        u = await users_repo.get_by_id(aid)
        author = HistoryAuthor(
            id=aid_str,
            display_name=u.get("display_name") if u else None,
        )

    return HistoryDetailResponse(
        rev=snap["rev"],
        content=snap["content"],
        author=author,
        created_at=snap["created_at"],
    )


@router.post(
    "/{section}/{rev}/restore",
    response_model=Union[LyricsWriteResponse, ChordsWriteResponse, TablatureWriteResponse],
    status_code=status.HTTP_200_OK,
)
async def restore_history_revision(
    composition_id: str,
    section: str = Path(...),
    rev: int = Path(..., ge=1),
    expected_rev: int = Query(..., ge=0),
    auth: AuthContext = Depends(require(Action.EDIT)),
    policy: PlanPolicy = Depends(get_plan_policy),
    revisions_repo: SectionRevisionsRepository = Depends(get_revisions_repo),
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    _validate_section(section)

    user_id = auth.user["id"]
    if not await policy.can_view_history(user_id):
        raise PlanGateError("plan_gate_history")

    snap = await revisions_repo.get_by_rev(
        composition_id=composition_id,
        section=section,
        rev=rev,
    )
    if not snap:
        raise NotFoundError("Versión no encontrada")

    content, new_rev = await versioning_service.update_versioned_section(
        composition_id=composition_id,
        section_name=section,
        content=snap["content"],
        author_id=user_id,
        expected_rev=expected_rev,
    )

    if section == "lyrics":
        return LyricsWriteResponse(**content, rev=new_rev)
    elif section == "chords":
        return ChordsWriteResponse(**content, rev=new_rev)
    else:
        return TablatureWriteResponse(**content, rev=new_rev)
