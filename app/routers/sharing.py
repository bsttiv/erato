from typing import List
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.core.plan_policy import PlanPolicy
from app.deps import AuthContext, get_plan_policy, require
from app.db.repositories.users import UsersRepository
from app.routers.compositions import _to_response, compute_initials
from app.schemas.compositions import (
    CompositionResponse,
    MemberDetail,
    UpdateVisibilityRequest,
    UpdateBandRequest,
    UpdateMemberRoleRequest,
)
from app.services.sharing_service import SharingService

router = APIRouter(prefix="/api/compositions/{composition_id}", tags=["sharing"])


def get_service(policy: PlanPolicy = Depends(get_plan_policy)) -> SharingService:
    return SharingService(policy=policy)


@router.get(
    "/members",
    response_model=List[MemberDetail],
    status_code=status.HTTP_200_OK,
)
async def list_members(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
) -> List[MemberDetail]:
    """Return resolved owner and active member roles (owner only)."""
    users_repo = UsersRepository()
    owner_doc = await users_repo.get_by_id(auth.composition["owner_id"])

    active_uids = [m["user_id"] for m in auth.composition.get("members", []) if "user_id" in m]
    user_map = await users_repo.get_by_ids(active_uids)

    result: List[MemberDetail] = []

    # 1. Owner
    if owner_doc:
        result.append(
            MemberDetail(
                user_id=str(owner_doc["_id"]),
                display_name=owner_doc.get("display_name"),
                email=owner_doc.get("email"),
                initials=compute_initials(owner_doc.get("display_name")),
                role="owner",
                pending=False,
            )
        )
    else:
        result.append(
            MemberDetail(
                user_id=str(auth.composition["owner_id"]),
                role="owner",
                pending=False,
            )
        )

    # 2. Active members
    for m in auth.composition.get("members", []):
        uid_str = str(m["user_id"])
        u = user_map.get(uid_str)
        display_name = u.get("display_name") if u else None
        result.append(
            MemberDetail(
                user_id=uid_str,
                display_name=display_name,
                email=u.get("email") if u else None,
                initials=compute_initials(display_name),
                role=m.get("role", "editor"),
                pending=False,
            )
        )

    return result


@router.patch(
    "/visibility",
    response_model=CompositionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_visibility(
    composition_id: str,
    body: UpdateVisibilityRequest,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> CompositionResponse:
    """Toggle composition visibility between public and private (owner only)."""
    updated = await service.update_visibility(composition_id, body.visibility)
    return _to_response(updated, role=auth.role)


@router.patch("/band", response_model=CompositionResponse)
async def update_band(
    composition_id: str,
    body: UpdateBandRequest,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> CompositionResponse:
    updated = await service.set_band(
        composition_id, str(auth.composition["owner_id"]), body.band_id, body.band_editable,
    )
    if body.band_id is not None:
        updated["band_active"] = True
    return _to_response(updated, role=auth.role)


@router.put("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_member_role(
    composition_id: str,
    user_id: str,
    body: UpdateMemberRoleRequest,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> None:
    await service.set_member_role(
        auth.composition, str(auth.composition["owner_id"]), user_id, body.role,
    )


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    composition_id: str,
    user_id: str,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> None:
    await service.remove_member(auth.composition, user_id)
