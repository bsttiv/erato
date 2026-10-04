from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.core.plan_policy import HostCapabilities, PlanPolicy
from app.deps import current_user_required, get_host_capabilities, get_plan_policy
from app.schemas.entitlements import EntitlementsResponse

router = APIRouter(tags=["entitlements"])


@router.get("/api/me/entitlements", response_model=EntitlementsResponse)
async def get_my_entitlements(
    user: Dict[str, Any] = Depends(current_user_required),
    policy: PlanPolicy = Depends(get_plan_policy),
    host_caps: HostCapabilities = Depends(get_host_capabilities),
) -> EntitlementsResponse:
    """Return user-scoped plan entitlements and capabilities for the acting user."""
    user_id = str(user["id"])

    can_share = await policy.can_share_with_people(user_id)
    can_create = await policy.can_create_band(user_id)
    can_history = await policy.can_view_history(user_id)
    demo_limit = await policy.demo_limit(user_id)

    band_creation_mode = "direct" if can_create else "hand_off"

    return EntitlementsResponse(
        can_share_with_people=can_share,
        can_create_band=can_create,
        can_view_history=can_history,
        demo_limit_per_composition=demo_limit,
        extensions_available=host_caps.extensions_available,
        band_creation_mode=band_creation_mode,
    )
