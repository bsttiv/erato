import logging
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status

from app.core.errors import NotFoundError, UnauthorizedError
from app.core.security.tokens import hash_opaque_token
from app.db.repositories.invitations import InvitationsRepository
from app.routers.bands import get_service as get_bands_service
from app.services.bands_service import BandsService
from app.deps import current_user_required
from app.db.repositories.users import UsersRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.compositions import RedeemInviteRequest

from app.services.auth_service import AuthService
from app.settings import get_settings

logger = logging.getLogger("erato.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


def get_users_repository() -> UsersRepository:
    return UsersRepository()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    max_age_seconds = int(settings.refresh_token_ttl_days * 24 * 60 * 60)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/auth",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account with email and password."""
    user = await service.register(
        email=body.email,
        password=body.password,
        display_name=body.display_name,
    )
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        display_name=user["display_name"],
        created_at=user["created_at"],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with email and password, issuing an access JWT and refresh cookie."""
    access_token, refresh_plaintext, user = await service.login(
        email=body.email,
        password=body.password,
    )
    _set_refresh_cookie(response, refresh_plaintext)

    user_resp = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        display_name=user["display_name"],
        created_at=user["created_at"],
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Rotate single-use refresh token and issue a new access token."""
    if not refresh_token:
        raise UnauthorizedError("Token de actualización ausente")

    new_access_token, new_refresh_plaintext, user = await service.refresh_tokens(refresh_token)
    _set_refresh_cookie(response, new_refresh_plaintext)

    user_resp = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        display_name=user["display_name"],
        created_at=user["created_at"],
    )
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        user=user_resp,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    """Revoke refresh token family and delete refresh cookie."""
    await service.logout(refresh_token)
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
    )
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user(
    current_identity: dict = Depends(current_user_required),
    users_repo: UsersRepository = Depends(get_users_repository),
) -> UserResponse:
    """Return the currently authenticated user's profile."""
    user = await users_repo.get_by_id(current_identity["id"])
    if not user:
        raise UnauthorizedError("Usuario no encontrado")

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        display_name=user["display_name"],
        created_at=user["created_at"],
    )


@router.post(
    "/redeem-invite",
    status_code=status.HTTP_200_OK,
)
async def redeem_invite(
    body: "RedeemInviteRequest",
    current_identity: dict = Depends(current_user_required),
    bands: BandsService = Depends(get_bands_service),
) -> dict:
    """Dispatch band invitations while preserving the legacy composition flow."""
    digest = hash_opaque_token(body.token)
    invitation = await InvitationsRepository().get_by_hash(digest)
    if invitation is None:
        raise NotFoundError("Invitación no encontrada")
    if (invitation.get("target") or {}).get("type") == "band":
        return await bands.redeem_invite(digest, current_identity["id"])
    from app.services.sharing_service import SharingService
    service = SharingService()
    comp_id = await service.redeem_invite(
        plaintext_token=body.token,
        user_id=current_identity["id"],
    )
    return {
        "message": "Invitación canjeada con éxito",
        "composition_id": comp_id,
    }

