from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, PlanGateError
from app.core.plan_policy import PlanPolicy, UnlimitedPlanPolicy
from app.core.security.tokens import hash_opaque_token, mint_opaque_token
from app.db.repositories.bands import BandsRepository
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
        policy: Optional[PlanPolicy] = None,
    ) -> None:
        self.compositions_repo = compositions_repo or CompositionsRepository()
        self.invitations_repo = invitations_repo or InvitationsRepository()
        self.policy = policy or UnlimitedPlanPolicy()

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

    async def _require_band_member(self, band_id: Optional[str], user_id: str) -> None:
        band = await BandsRepository(self.compositions_repo.db).get_by_id(band_id) if band_id else None
        if band is None or not any(str(m["user_id"]) == user_id for m in band["members"]):
            raise ConflictError("El usuario no pertenece a la banda", code="not_a_band_member")

    async def _require_active_band(self, band_id: str) -> None:
        if not await self.policy.is_band_active(band_id):
            raise ForbiddenError("La banda está inactiva", code="band_inactive")

    async def _require_sharing(self, user_id: str, band_id: str) -> None:
        if not await self.policy.can_share_with_people(user_id):
            raise PlanGateError("plan_gate_sharing")
        await self._require_active_band(band_id)

    async def set_band(self, composition_id: str, owner_id: str,
                       band_id: Optional[str], band_editable: bool) -> Dict[str, Any]:
        if band_id is not None:
            await self._require_band_member(band_id, owner_id)
            await self._require_sharing(owner_id, band_id)
        updated = await self.compositions_repo.set_band(composition_id, band_id, band_editable)
        if updated is None:
            raise NotFoundError("Composición no encontrada")
        return updated

    async def set_member_role(self, composition: Dict[str, Any], owner_id: str,
                              user_id: str, role: str) -> None:
        band_id = str(composition["band_id"]) if composition.get("band_id") else None
        await self._require_band_member(band_id, user_id)
        await self._require_sharing(owner_id, band_id)
        await self.compositions_repo.set_member_role(str(composition["_id"]), user_id, role)

    async def remove_member(self, composition: Dict[str, Any], user_id: str) -> None:
        if composition.get("band_id"):
            await self._require_active_band(str(composition["band_id"]))
        await self.compositions_repo.remove_member(str(composition["_id"]), user_id)
