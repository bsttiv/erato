from datetime import datetime, timezone
import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.errors import UnauthorizedError
from app.settings import get_settings


def mint_access_token(
    user_id: str,
    token_version: int = 1,
    ttl_minutes: Optional[int] = None,
) -> str:
    """Mint an access JWT using HS256.
    
    Claims: sub (subject), iat (issued-at), exp (expiry), token_version.
    Strictly nothing else per design.md.
    """
    settings = get_settings()
    ttl = ttl_minutes if ttl_minutes is not None else settings.access_token_ttl_minutes

    now = int(datetime.now(timezone.utc).timestamp())
    exp = now + int(ttl * 60)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": exp,
        "token_version": token_version,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_access_token(
    token: str,
    expected_token_version: Optional[int] = None,
) -> Dict[str, Any]:
    """Verify an access JWT.
    
    Enforces HS256 algorithm (rejecting 'none'), checks expiration,
    validates signature, and optionally checks token_version against current user version.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={
                "require": ["sub", "iat", "exp", "token_version"],
                "verify_exp": True,
            },
        )
    except ExpiredSignatureError:
        raise UnauthorizedError("Token expirado")
    except InvalidTokenError:
        raise UnauthorizedError("Token inválido o firma incorrecta")

    if expected_token_version is not None:
        if payload.get("token_version") != expected_token_version:
            raise UnauthorizedError("Token revocado")

    return payload


def hash_opaque_token(plaintext: str) -> str:
    """Compute the SHA-256 hex digest of an opaque token."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def mint_opaque_token() -> Tuple[str, str]:
    """Generate a high-entropy 256-bit URL-safe token.
    
    Returns a tuple of (plaintext, sha256_digest).
    The plaintext is returned once; only the digest should be persisted.
    """
    # 32 bytes = 256 bits of cryptographically secure random entropy
    plaintext = secrets.token_urlsafe(32)
    digest = hash_opaque_token(plaintext)
    return plaintext, digest


def verify_opaque_token(plaintext: str, digest: str) -> bool:
    """Constant-time verification of an opaque token against its stored SHA-256 digest."""
    candidate_digest = hash_opaque_token(plaintext)
    return secrets.compare_digest(candidate_digest, digest)
