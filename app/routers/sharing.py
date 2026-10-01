from typing import List
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.deps import AuthContext, require
from app.routers.compositions import _to_response
from app.schemas.compositions import (
    CompositionResponse,
    CreateInviteRequest,
    InviteResponse,
    UpdateVisibilityRequest,
)
from app.services.sharing_service import SharingService
from app.settings import get_settings

router = APIRouter(prefix="/api/compositions/{composition_id}", tags=["sharing"])


def get_service() -> SharingService:
    return SharingService()


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
    return _to_response(updated)


@router.post(
    "/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    composition_id: str,
    body: CreateInviteRequest,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> InviteResponse:
    """Mint an invitation token and return the full invite URL (owner only)."""
    inv, plaintext = await service.create_invite(
        composition_id=composition_id,
        created_by=auth.user["id"] if auth.user else str(auth.composition["owner_id"]),
        invited_email=body.invited_email,
        role=body.role,
    )
    settings = get_settings()
    invite_url = f"{settings.app_base_url}/invite/{plaintext}"

    return InviteResponse(
        id=str(inv["_id"]),
        composition_id=str(inv["composition_id"]),
        invite_url=invite_url,
        invited_email=inv.get("invited_email"),
        role=inv.get("role", "editor"),
        expires_at=inv["expires_at"],
        used_at=inv.get("used_at"),
    )


@router.get(
    "/invites",
    response_model=List[InviteResponse],
    status_code=status.HTTP_200_OK,
)
async def list_invites(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> List[InviteResponse]:
    """List all invitations for the composition (owner only)."""
    docs = await service.list_invites(composition_id)
    return [
        InviteResponse(
            id=str(d["_id"]),
            composition_id=str(d["composition_id"]),
            invite_url=None,  # Plaintext is only returned once at creation
            invited_email=d.get("invited_email"),
            role=d.get("role", "editor"),
            expires_at=d["expires_at"],
            used_at=d.get("used_at"),
        )
        for d in docs
    ]


@router.delete(
    "/invites/{invite_id}",
    status_code=status.HTTP_200_OK,
)
async def revoke_invite(
    composition_id: str,
    invite_id: str,
    auth: AuthContext = Depends(require(Action.MANAGE_SHARING)),
    service: SharingService = Depends(get_service),
) -> dict:
    """Revoke an active invitation (owner only)."""
    await service.revoke_invite(invite_id)
    return {"message": "Invitación revocada correctamente"}
