from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, status


from app.core.errors import UnauthorizedError
from app.settings import get_settings

logger = logging.getLogger("erato.maintenance")

router = APIRouter(prefix="/api/cron", tags=["maintenance"])


def filter_orphan_assets_for_sweep(
    assets: List[Dict[str, Any]],
    now: Optional[datetime] = None,
    max_age_hours: int = 24,
) -> List[str]:
    """Filter Cloudinary assets for orphan sweep.
    
    Conditions:
    - Must be tagged 'pending'.
    - Must be older than max_age_hours (default 24h).
    Confirmed assets (without 'pending' tag) or recent pending uploads are never touched.
    """
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(hours=max_age_hours)
    to_delete: List[str] = []

    for asset in assets:
        tags = asset.get("tags") or []
        if "pending" not in tags:
            continue

        created_at_raw = asset.get("created_at")
        if not created_at_raw:
            continue

        if isinstance(created_at_raw, str):
            created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        else:
            created_at = created_at_raw


        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if created_at < cutoff:
            to_delete.append(asset["public_id"])

    return to_delete


def execute_orphan_sweep() -> List[str]:
    """Query Cloudinary for pending assets, filter orphans older than 24h, and delete them."""
    try:
        import cloudinary.api
        response = cloudinary.api.resources_by_tag(
            "pending",
            resource_type="video",
            type="authenticated",
            max_results=500,
        )
        resources = response.get("resources", [])
        to_delete = filter_orphan_assets_for_sweep(resources)

        if to_delete:
            cloudinary.api.delete_resources(
                to_delete,
                resource_type="video",
                type="authenticated",
            )
            logger.info("Swept %d orphan Cloudinary assets: %s", len(to_delete), to_delete)
        return to_delete
    except Exception as e:
        logger.warning("Error during orphan sweep execution: %s", e)
        return []


@router.get("/orphan-sweep", status_code=status.HTTP_200_OK)
async def orphan_sweep(
    authorization: Optional[str] = Header(None),
    x_vercel_cron: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Vercel Cron target for daily orphan Cloudinary asset cleanup.
    
    Protected by CRON_SECRET bearer token or Vercel cron header.
    """
    settings = get_settings()

    is_vercel_cron = x_vercel_cron == "1"
    is_secret_valid = bool(
        settings.cron_secret and authorization == f"Bearer {settings.cron_secret}"
    )

    if not (is_vercel_cron or is_secret_valid):
        raise UnauthorizedError("No autorizado para ejecutar el sweep de mantenimiento")

    deleted = execute_orphan_sweep()
    return {
        "status": "ok",
        "deleted_count": len(deleted),
        "deleted": deleted,
    }
