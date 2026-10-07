from dataclasses import dataclass
from bson import ObjectId
from typing import Any, Dict, Optional
from fastapi import Depends, Header, Request

from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.permissions import Action, BandContext, Role, can, resolve_role
from app.core.plan_policy import HostCapabilities, PlanPolicy, UnlimitedPlanPolicy
from app.core.security.tokens import verify_access_token
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.bands import BandsRepository


@dataclass
class AuthContext:
    user: Optional[Dict[str, Any]]
    role: Role
    composition: Dict[str, Any]


async def current_user_optional(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[Dict[str, Any]]:
    """Resolve user identity statelessly from Authorization: Bearer <JWT> header.
    
    Per design.md, JWT verification is stateless with zero database round trips
    to protect Atlas M0 limits and stay well inside execution caps.
    """
    if not authorization:
        return None

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Formato de encabezado Authorization inválido")

    token = parts[1]
    payload = verify_access_token(token)

    return {
        "id": payload["sub"],
        "token_version": payload.get("token_version", 1),
    }


async def current_user_required(
    user: Optional[Dict[str, Any]] = Depends(current_user_optional),
) -> Dict[str, Any]:
    """Require an authenticated user; raises 401 if missing or invalid token."""
    if user is None:
        raise UnauthorizedError("No autenticado")
    return user


async def composition_access(
    request: Request,
) -> Dict[str, Any]:
    """Load composition access record once per request and cache it on request.state.
    
    Checks path parameters 'composition_id', 'id', or 'slug'.
    """
    if hasattr(request.state, "composition_access"):
        return request.state.composition_access

    comp_id = request.path_params.get("composition_id") or request.path_params.get("id")
    slug = request.path_params.get("slug")

    repo = CompositionsRepository()
    if comp_id:
        record = await repo.get_by_id(comp_id)
    elif slug:
        record = await repo.get_by_slug(slug)
    else:
        record = None

    if record is None:
        raise NotFoundError("Composición no encontrada")

    request.state.composition_access = record
    return record


def get_plan_policy() -> PlanPolicy:
    return UnlimitedPlanPolicy()


def get_host_capabilities() -> HostCapabilities:
    return HostCapabilities(extensions_available=False)


async def band_context(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(current_user_optional),
    access_record: Dict[str, Any] = Depends(composition_access),
) -> Optional[BandContext]:
    """Load only the membership fields needed for band-derived authorization."""
    band_id = access_record.get("band_id")
    if not band_id or user is None:
        return None
    band = await BandsRepository().collection.find_one(
        {"_id": ObjectId(band_id)}, {"owner_id": 1, "members.user_id": 1},
    )
    is_member = band is not None and any(
        str(member["user_id"]) == str(user["id"]) for member in band.get("members", [])
    )
    return BandContext(str(band_id), is_member)


def require(action: Action):
    """Dependency factory enforcing the 404-vs-403 permission model for the specified action."""
    async def dependency(
        request: Request,
        user: Optional[Dict[str, Any]] = Depends(current_user_optional),
        access_record: Dict[str, Any] = Depends(composition_access),
        band: Optional[BandContext] = Depends(band_context),
        policy: PlanPolicy = Depends(get_plan_policy),
    ) -> AuthContext:
        user_id = user["id"] if user else None
        # Direct callers may omit dependencies; FastAPI supplies the resolved context.
        resolved_band = band if isinstance(band, BandContext) else None
        role = resolve_role(user_id, access_record, resolved_band)

        # 404-vs-403 rule: If caller cannot even view, return 404 (prevents existence probing)
        if not can(role, Action.VIEW):
            raise NotFoundError("Composición no encontrada")

        band_id = access_record.get("band_id")
        if action != Action.VIEW and role != Role.OWNER and band_id:
            if not await policy.is_band_active(str(band_id)):
                raise ForbiddenError("La banda no está activa", code="band_inactive")

        # If caller can view but lacks permission for requested action, return 403
        if not can(role, action):
            raise ForbiddenError("No tienes permiso para realizar esta acción")

        return AuthContext(user=user, role=role, composition=access_record)

    return dependency
