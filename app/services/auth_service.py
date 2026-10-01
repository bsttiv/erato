from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import uuid

from app.core.errors import UnauthorizedError
from app.core.security.passwords import hash_password, verify_password
from app.core.security.tokens import hash_opaque_token, mint_access_token, mint_opaque_token
from app.db.repositories.refresh_tokens import RefreshTokensRepository
from app.db.repositories.users import UsersRepository
from app.settings import get_settings


class AuthService:
    """Framework-agnostic business logic for authentication, tokens, and sessions."""

    def __init__(
        self,
        users_repo: Optional[UsersRepository] = None,
        tokens_repo: Optional[RefreshTokensRepository] = None,
    ) -> None:
        self.users_repo = users_repo or UsersRepository()
        self.tokens_repo = tokens_repo or RefreshTokensRepository()

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> Dict[str, Any]:
        """Register a new user: hash password using Argon2id and persist."""
        password_hash = hash_password(password)
        user = await self.users_repo.create_user(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        return user

    async def login(
        self,
        email: str,
        password: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Authenticate user by email and password.
        
        Returns:
            Tuple of (access_token, refresh_plaintext, user_dict).
        Raises:
            UnauthorizedError: Generic error without revealing whether email or password failed.
        """
        user = await self.users_repo.get_by_email(email)
        if not user:
            raise UnauthorizedError("Credenciales inválidas")

        if not verify_password(user["password_hash"], password):
            raise UnauthorizedError("Credenciales inválidas")

        access_token = mint_access_token(
            user_id=str(user["_id"]),
            token_version=user.get("token_version", 1),
        )

        settings = get_settings()
        family_id = uuid.uuid4().hex
        refresh_plaintext, refresh_digest = mint_opaque_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_ttl_days)

        await self.tokens_repo.create_token(
            token_hash=refresh_digest,
            user_id=user["_id"],
            family_id=family_id,
            expires_at=expires_at,
        )

        return access_token, refresh_plaintext, user

    async def refresh_tokens(
        self,
        refresh_plaintext: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Rotate refresh token: single-use redemption and issuance of a new token pair in the same family.
        
        If an already-redeemed token is presented, the repository invalidates the entire family.
        """
        if not refresh_plaintext:
            raise UnauthorizedError("Token de actualización ausente")

        digest = hash_opaque_token(refresh_plaintext)
        redeemed = await self.tokens_repo.redeem_token(digest)

        user = await self.users_repo.get_by_id(redeemed["user_id"])
        if not user:
            raise UnauthorizedError("Usuario no encontrado")

        access_token = mint_access_token(
            user_id=str(user["_id"]),
            token_version=user.get("token_version", 1),
        )

        settings = get_settings()
        new_plaintext, new_digest = mint_opaque_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_ttl_days)

        await self.tokens_repo.create_token(
            token_hash=new_digest,
            user_id=user["_id"],
            family_id=redeemed["family_id"],
            expires_at=expires_at,
        )

        return access_token, new_plaintext, user

    async def logout(self, refresh_plaintext: Optional[str]) -> None:
        """Revoke the refresh token family upon logout."""
        if not refresh_plaintext:
            return

        digest = hash_opaque_token(refresh_plaintext)
        doc = await self.tokens_repo.collection.find_one({"token_hash": digest})
        if doc and "family_id" in doc:
            await self.tokens_repo.invalidate_family(doc["family_id"])
