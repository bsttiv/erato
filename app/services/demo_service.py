import time
from typing import Any, Dict, List, Optional
import uuid

from app.core.errors import NotFoundError, PlanGateError, ValidationError
from app.core.plan_policy import PlanPolicy, UnlimitedPlanPolicy
from app.core.security.cloudinary_sign import (
    mint_delivery_url,
    sign_upload_params,
    verify_upload_response,
)
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.compositions import CompositionsRepository
from app.settings import get_settings


class DemoService:
    """Framework-agnostic business logic for demos, Cloudinary upload handshakes, and comments."""

    def __init__(
        self,
        compositions_repo: Optional[CompositionsRepository] = None,
        comments_repo: Optional[CommentsRepository] = None,
        policy: Optional[PlanPolicy] = None,
    ) -> None:
        self.compositions_repo = compositions_repo or CompositionsRepository()
        self.comments_repo = comments_repo or CommentsRepository()
        self.policy = policy or UnlimitedPlanPolicy()

    async def get_upload_signature(self, composition_id: str, user_id: str) -> Dict[str, Any]:
        """Mint signed upload parameters for direct-to-Cloudinary upload."""
        limit = await self.policy.demo_limit(user_id)
        if limit is not None:
            demos = await self.compositions_repo.list_demos(composition_id)
            if len(demos) >= limit:
                raise PlanGateError("plan_gate_demo_limit")
        return sign_upload_params(composition_id=composition_id)

    async def confirm_upload(
        self,
        composition_id: str,
        uploader_id: str,
        public_id: str,
        version: str,
        signature: str,
        title: str,
        duration_s: float,
    ) -> Dict[str, Any]:
        """Verify Cloudinary result signature, verify folder, and record demo reference."""
        settings = get_settings()
        expected_folder = f"{settings.cloudinary_folder_prefix}/compositions/{composition_id}"
        params_to_sign = {
            "public_id": public_id,
            "version": str(version),
        }

        is_valid = verify_upload_response(
            params_to_sign=params_to_sign,
            signature=signature,
            expected_folder_prefix=expected_folder,
            public_id=public_id,
        )
        if not is_valid:
            raise ValidationError("Firma de subida inválida o identificador fuera de la carpeta autorizada")

        limit = await self.policy.demo_limit(uploader_id)
        demo_id = uuid.uuid4().hex[:12]
        updated = await self.compositions_repo.add_demo_if_below(
            composition_id=composition_id,
            demo_id=demo_id,
            cloudinary_public_id=public_id,
            title=title,
            duration_s=duration_s,
            uploaded_by=uploader_id,
            limit=limit,
        )
        if not updated:
            if limit is not None:
                raise PlanGateError("plan_gate_demo_limit")
            raise NotFoundError("Composición no encontrada")

        # Keep quota-rejected assets pending so the orphan sweep can remove them.
        try:
            import cloudinary.uploader
            cloudinary.uploader.remove_tag("pending", [public_id], type="authenticated")
        except Exception:
            # Non-blocking for offline tests or when credentials are dummy
            pass

        demo = await self.compositions_repo.get_demo(composition_id, demo_id)
        if not demo:
            raise NotFoundError("Error al registrar la toma")
        return demo

    async def mint_playback_url(
        self,
        composition_id: str,
        demo_id: str,
        ttl_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """Mint a short-lived signed delivery URL for a demo without applying on-the-fly transformations."""
        demo = await self.compositions_repo.get_demo(composition_id, demo_id)
        if not demo:
            raise NotFoundError("Demo no encontrado")

        public_id = demo["cloudinary_public_id"]
        expires_at = int(time.time()) + ttl_seconds
        signed_url = mint_delivery_url(public_id=public_id, expires_at_or_ttl=expires_at)

        return {
            "url": signed_url,
            "expires_at": expires_at,
        }

    async def add_comment(
        self,
        composition_id: str,
        demo_id: str,
        author_id: str,
        timestamp_s: float,
        text: str,
    ) -> Dict[str, Any]:
        """Record a timestamp-anchored comment on a demo."""
        demo = await self.compositions_repo.get_demo(composition_id, demo_id)
        if not demo:
            raise NotFoundError("Demo no encontrado")

        return await self.comments_repo.create_comment(
            composition_id=composition_id,
            demo_id=demo_id,
            author_id=author_id,
            timestamp_s=timestamp_s,
            text=text,
        )

    async def list_comments(
        self,
        composition_id: str,
        demo_id: str,
    ) -> List[Dict[str, Any]]:
        """List comments for a demo ordered by timestamp."""
        demo = await self.compositions_repo.get_demo(composition_id, demo_id)
        if not demo:
            raise NotFoundError("Demo no encontrado")

        return await self.comments_repo.list_comments(composition_id, demo_id)
