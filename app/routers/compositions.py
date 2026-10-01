from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.deps import AuthContext, current_user_required, require
from app.schemas.compositions import (
    CompositionListItem,
    CompositionResponse,
    CreateCompositionRequest,
    MemberItem,
    UpdateCompositionRequest,
)
from app.services.composition_service import CompositionService

router = APIRouter(prefix="/api/compositions", tags=["compositions"])


def get_service() -> CompositionService:
    return CompositionService()


def _to_response(doc: dict) -> CompositionResponse:
    demos_raw = doc.get("demos") or []
    formatted_demos = [
        {
            **d,
            "uploaded_by": str(d.get("uploaded_by", "")),
        }
        for d in demos_raw
    ]
    return CompositionResponse(
        id=str(doc["_id"]),
        owner_id=str(doc["owner_id"]),
        title=doc["title"],
        visibility=doc["visibility"],
        share_slug=doc.get("share_slug"),
        chords=doc.get("chords"),
        tablature=doc.get("tablature"),
        lyrics=doc.get("lyrics"),
        todos=doc.get("todos") or [],
        demos=formatted_demos,
        members=[
            MemberItem(user_id=str(m["user_id"]), role=m.get("role", "editor"))
            for m in doc.get("members", [])
        ],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.post(
    "",
    response_model=CompositionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_composition(
    body: CreateCompositionRequest,
    current_user: dict = Depends(current_user_required),
    service: CompositionService = Depends(get_service),
) -> CompositionResponse:
    """Create a new composition (owner-only, authenticated)."""
    doc = await service.create_composition(
        owner_id=current_user["id"],
        title=body.title,
        visibility=body.visibility,
    )
    return _to_response(doc)


@router.get(
    "",
    response_model=List[CompositionListItem],
    status_code=status.HTTP_200_OK,
)
async def list_compositions(
    current_user: dict = Depends(current_user_required),
    service: CompositionService = Depends(get_service),
) -> List[CompositionListItem]:
    """List compositions owned by or shared with current user."""
    docs = await service.list_for_user(current_user["id"])
    return [
        CompositionListItem(
            id=str(d["_id"]),
            owner_id=str(d["owner_id"]),
            title=d["title"],
            visibility=d["visibility"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )
        for d in docs
    ]


@router.get(
    "/by-slug/{slug}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_by_slug(
    slug: str,
    service: CompositionService = Depends(get_service),
) -> CompositionResponse:
    """Anonymous or authenticated read of a public composition by its unguessable share slug."""
    doc = await service.get_by_slug(slug)
    return _to_response(doc)


@router.get(
    "/{composition_id}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_composition(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> CompositionResponse:
    """Read a composition by ID, enforced by require(Action.VIEW)."""
    return _to_response(auth.composition)


@router.patch(
    "/{composition_id}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_composition(
    composition_id: str,
    body: UpdateCompositionRequest,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: CompositionService = Depends(get_service),
) -> CompositionResponse:
    """Update composition top-level fields, enforced by require(Action.EDIT)."""
    updated = await service.update_composition(composition_id, title=body.title)
    return _to_response(updated)


@router.delete(
    "/{composition_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_composition(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.DELETE)),
    service: CompositionService = Depends(get_service),
) -> dict:
    """Delete a composition, enforced by require(Action.DELETE) (owner only)."""
    await service.delete_composition(composition_id)
    return {"message": "Composición eliminada correctamente"}
