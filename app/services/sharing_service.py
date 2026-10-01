from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.errors import NotFoundError
from app.core.security.tokens import hash_opaque_token, mint_opaque_token
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.invitations import InvitationsRepository
from app.services.composition_service import generate_share_slug
from app.settings import get_settings


class SharingService:
    """Framework-agnostic business logic for composition visibility and member invitations."""

    def __init__(
        self,
        compositions_repo: Optional[CompositionsRepository] = None,
        invitations_repo: Optional[InvitationsRepository] = None,
    ) -> None:
        self.compositions_repo = compositions_repo or CompositionsRepository()
        self.invitations_repo = invitations_repo or InvitationsRepository()

    async def update_visibility(
        self,
        composition_id: str,
        visibility: str,
    ) -> Dict[str, Any]:
        """Toggle composition visibility. Mints an unguessable 128-bit slug when going public."""
        share_slug = None
        if visibility == "public":
            # Check if composition already has a share slug
            comp = await self.compositions_repo.get_by_id(composition_id)
            if comp and comp.get("share_slug"):
                share_slug = comp["share_slug"]
            else:
                share_slug = generate_share_slug()

        updated = await self.compositions_repo.update_visibility(
            composition_id=composition_id,
            visibility=visibility,
            share_slug=share_slug,
        )
        if not updated:
            raise NotFoundError("Composición no encontrada")
        return updated

    async def create_invite(
        self,
        composition_id: str,
        created_by: str,
        invited_email: Optional[str] = None,
        role: str = "editor",
    ) -> Tuple[Dict[str, Any], str]:
        """Mint a 256-bit opaque invite token, persist its SHA-256 digest, and return the plaintext once."""
        settings = get_settings()
        plaintext, digest = mint_opaque_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.invite_token_ttl_days)

        inv = await self.invitations_repo.create_invitation(
            composition_id=composition_id,
            token_hash=digest,
            expires_at=expires_at,
            created_by=created_by,
            invited_email=invited_email,
            role=role,
        )
        return inv, plaintext

    async def list_invites(self, composition_id: str) -> List[Dict[str, Any]]:
        """List active or historical invitations for a composition."""
        return await self.invitations_repo.list_by_composition(composition_id)

    async def revoke_invite(self, invitation_id: str) -> bool:
        """Revoke an invitation by ID."""
        deleted = await self.invitations_repo.revoke_invitation(invitation_id)
        if not deleted:
            raise NotFoundError("Invitación no encontrada")
        return True

    async def redeem_invite(self, plaintext_token: str, user_id: str) -> str:
        """Redeem an invitation using its plaintext token and add user as a member.
        
        Returns the composition_id.
        """
        digest = hash_opaque_token(plaintext_token)
        invitation = await self.invitations_repo.redeem_invitation(digest)
        comp_id = str(invitation["composition_id"])

        await self.compositions_repo.add_member(
            composition_id=comp_id,
            user_id=user_id,
            role=invitation.get("role", "editor"),
        )
        return comp_id
