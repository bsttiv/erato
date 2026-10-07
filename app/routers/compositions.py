from typing import Any, List, Optional
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.core.plan_policy import PlanPolicy
from app.deps import AuthContext, current_user_required, get_plan_policy, require
from app.schemas.compositions import (
    CompositionCounts,
    CompositionListItem,
    CompositionResponse,
    CreateCompositionRequest,
    MemberItem,
    SectionRevs,
    SectionsEnabled,
    UpdateCompositionRequest,
)
from app.db.repositories.users import UsersRepository

from app.services.composition_service import CompositionService

router = APIRouter(prefix="/api/compositions", tags=["compositions"])


def get_service() -> CompositionService:
    return CompositionService()


def compute_initials(name: Optional[str]) -> Optional[str]:
    """Derive 1-2 uppercase characters from display name."""
    if not name:
        return None
    parts = name.strip().split()
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _to_response(
    doc: dict,
    role: Optional[Any] = None,
    user_map: Optional[dict] = None,
) -> CompositionResponse:
    demos_raw = doc.get("demos") or []
    formatted_demos = [
        {
            **d,
            "uploaded_by": str(d.get("uploaded_by", "")),
        }
        for d in demos_raw
    ]

    user_role_str: Optional[str] = None
    if role is not None:
        user_role_str = role.value if hasattr(role, "value") else str(role)
    elif "user_role" in doc:
        user_role_str = doc["user_role"]

    sections_enabled_data = doc.get("sections_enabled")
    if isinstance(sections_enabled_data, dict):
        sections_enabled = SectionsEnabled(**sections_enabled_data)
    elif isinstance(sections_enabled_data, SectionsEnabled):
        sections_enabled = sections_enabled_data
    else:
        sections_enabled = SectionsEnabled()

    members_list: List[MemberItem] = []
    for m in doc.get("members", []):
        uid_str = str(m["user_id"])
        u = user_map.get(uid_str) if user_map else None
        d_name = u.get("display_name") if u else m.get("display_name")
        init = compute_initials(d_name) if d_name else m.get("initials")
        members_list.append(
            MemberItem(
                user_id=uid_str,
                role=m.get("role", "editor"),
                display_name=d_name,
                initials=init,
            )
        )

    return CompositionResponse(
        band_id=str(doc["band_id"]) if doc.get("band_id") else None,
        band_editable=doc.get("band_editable", False),
        band_active=doc.get("band_active"),
        id=str(doc["_id"]),
        owner_id=str(doc["owner_id"]),
        title=doc["title"],
        visibility=doc["visibility"],
        share_slug=doc.get("share_slug"),
        key=doc.get("key"),
        bpm=doc.get("bpm"),
        time_signature=doc.get("time_signature"),
        style_tags=doc.get("style_tags") or [],
        status=doc.get("status") or "idea",
        sections_enabled=sections_enabled,
        user_role=user_role_str,
        section_revs=SectionRevs(**(doc.get("section_revs") or {})),
        chords=doc.get("chords"),
        tablature=doc.get("tablature"),
        lyrics=doc.get("lyrics"),

        todos=doc.get("todos") or [],
        demos=formatted_demos,
        members=members_list,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def _to_response_async(
    doc: dict, role: Optional[Any] = None, policy: Optional[PlanPolicy] = None,
) -> CompositionResponse:
    if doc.get("band_id") and policy is not None:
        doc = {**doc, "band_active": await policy.is_band_active(str(doc["band_id"]))}
    user_ids = [m["user_id"] for m in doc.get("members", []) if "user_id" in m]
    user_map = {}
    if user_ids:
        user_map = await UsersRepository().get_by_ids(user_ids)
    return _to_response(doc, role=role, user_map=user_map)


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
    sections_dict = body.sections_enabled.model_dump() if body.sections_enabled else None
    doc = await service.create_composition(
        owner_id=current_user["id"],
        title=body.title,
        visibility=body.visibility,
        key=body.key,
        bpm=body.bpm,
        time_signature=body.time_signature,
        style_tags=body.style_tags,
        status=body.status,
        sections_enabled=sections_dict,
    )
    return _to_response(doc, role="owner")


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
    items: List[CompositionListItem] = []

    for d in docs:
        chords_dict = d.get("chords") or {}
        entries = chords_dict.get("entries") or []
        chord_names = [e["name"] for e in entries if isinstance(e, dict) and "name" in e][:4]

        tablature_dict = d.get("tablature") or {}
        tabs = tablature_dict.get("tabs")
        if isinstance(tabs, list):
            tabs_count = len(tabs)
        elif tablature_dict.get("content"):
            tabs_count = 1
        else:
            tabs_count = 0

        demos = d.get("demos") or []
        todos = d.get("todos") or []
        todos_done = sum(1 for t in todos if isinstance(t, dict) and t.get("done"))

        counts = CompositionCounts(
            chords=len(entries),
            tabs=tabs_count,
            demos=len(demos),
            todos_done=todos_done,
            todos_total=len(todos),
        )

        sections_enabled_data = d.get("sections_enabled")
        if isinstance(sections_enabled_data, dict):
            sections_enabled = SectionsEnabled(**sections_enabled_data)
        elif isinstance(sections_enabled_data, SectionsEnabled):
            sections_enabled = sections_enabled_data
        else:
            sections_enabled = SectionsEnabled()

        items.append(
            CompositionListItem(
                band_id=str(d["band_id"]) if d.get("band_id") else None,
                via_band=d.get("via_band", False),
                id=str(d["_id"]),
                owner_id=str(d["owner_id"]),
                title=d["title"],
                visibility=d["visibility"],
                key=d.get("key"),
                bpm=d.get("bpm"),
                time_signature=d.get("time_signature"),
                style_tags=d.get("style_tags") or [],
                status=d.get("status") or "idea",
                sections_enabled=sections_enabled,
                counts=counts,
                chord_names=chord_names,
                created_at=d["created_at"],
                updated_at=d["updated_at"],
            )
        )

    return items


@router.get(
    "/by-slug/{slug}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_by_slug(
    slug: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
    policy: PlanPolicy = Depends(get_plan_policy),
) -> CompositionResponse:
    """Read a public composition by slug using the same authorization path as ID reads."""
    return await _to_response_async(
        auth.composition, role=auth.role if auth.user else None, policy=policy,
    )


@router.get(
    "/{composition_id}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_composition(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
    policy: PlanPolicy = Depends(get_plan_policy),
) -> CompositionResponse:
    """Read a composition by ID, enforced by require(Action.VIEW)."""
    return await _to_response_async(auth.composition, role=auth.role, policy=policy)


@router.patch(
    "/{composition_id}",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_composition(
    composition_id: str,
    body: UpdateCompositionRequest,
    auth: AuthContext = Depends(require(Action.EDIT)),
    policy: PlanPolicy = Depends(get_plan_policy),
    service: CompositionService = Depends(get_service),
) -> CompositionResponse:
    """Update composition top-level fields, enforced by require(Action.EDIT)."""
    update_data = body.model_dump(exclude_unset=True)
    if "sections_enabled" in update_data and update_data["sections_enabled"] is not None:
        if hasattr(body.sections_enabled, "model_dump"):
            update_data["sections_enabled"] = body.sections_enabled.model_dump()

    updated = await service.update_composition(composition_id, **update_data)
    return await _to_response_async(updated, role=auth.role, policy=policy)


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
