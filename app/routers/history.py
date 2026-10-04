from typing import Any, Optional, Union
from fastapi import APIRouter, Depends, Path, Query, status

from app.core.permissions import Action
from app.core.plan_policy import PlanPolicy
from app.deps import AuthContext, get_plan_policy, require
from app.schemas.compositions import (
    ChordsWriteResponse,
    LyricsWriteResponse,
    TablatureWriteResponse,
)
from app.schemas.history import (
    HistoryDetailResponse,
    HistoryListResponse,
)
from app.services.versioning_service import VersioningService

router = APIRouter(prefix="/api/compositions/{composition_id}/history", tags=["history"])


def get_versioning_service(policy: PlanPolicy = Depends(get_plan_policy)) -> VersioningService:
    return VersioningService(policy=policy)


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
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    return await versioning_service.list_history(
        composition_id=composition_id,
        section=section,
        user_id=auth.user["id"],
        limit=limit,
        before_rev=before_rev,
    )


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
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    return await versioning_service.get_history_revision(
        composition_id=composition_id,
        section=section,
        rev=rev,
        user_id=auth.user["id"],
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
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    content, new_rev = await versioning_service.restore_history_revision(
        composition_id=composition_id,
        section=section,
        rev=rev,
        user_id=auth.user["id"],
        expected_rev=expected_rev,
    )

    if section == "lyrics":
        return LyricsWriteResponse(**content, rev=new_rev)
    elif section == "chords":
        return ChordsWriteResponse(**content, rev=new_rev)
    else:
        return TablatureWriteResponse(**content, rev=new_rev)
