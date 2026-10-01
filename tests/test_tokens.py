import time
import jwt
import pytest
from app.core.errors import UnauthorizedError
from app.core.security.tokens import (
    mint_access_token,
    verify_access_token,
    mint_opaque_token,
    hash_opaque_token,
    verify_opaque_token,
)
from app.settings import get_settings


def test_access_token_round_trip():
    user_id = "60f7b1b3b3f1c2a1d8e4f5a6"
    token = mint_access_token(user_id=user_id, token_version=1)

    payload = verify_access_token(token, expected_token_version=1)
    assert payload["sub"] == user_id
    assert payload["token_version"] == 1
    assert "iat" in payload
    assert "exp" in payload
    # Must only contain sub, iat, exp, token_version per design.md
    assert set(payload.keys()) == {"sub", "iat", "exp", "token_version"}


def test_expired_token_rejected():
    user_id = "60f7b1b3b3f1c2a1d8e4f5a6"
    # Negative TTL so token is already expired
    token = mint_access_token(user_id=user_id, token_version=1, ttl_minutes=-5)

    with pytest.raises(UnauthorizedError, match="expirado"):
        verify_access_token(token)


def test_tampered_signature_rejected():
    user_id = "60f7b1b3b3f1c2a1d8e4f5a6"
    token = mint_access_token(user_id=user_id, token_version=1)

    # Tamper with the signature portion of the JWT (split by '.')
    parts = token.split(".")
    tampered_sig = parts[2][:-4] + "AAAA"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    with pytest.raises(UnauthorizedError):
        verify_access_token(tampered_token)


def test_alg_none_rejected():
    user_id = "60f7b1b3b3f1c2a1d8e4f5a6"
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 900,
        "token_version": 1,
    }
    # Unsigned token with alg: none
    unsigned_token = jwt.encode(payload, key="", algorithm="none")

    with pytest.raises(UnauthorizedError):
        verify_access_token(unsigned_token)


def test_token_version_mismatch_rejected():
    user_id = "60f7b1b3b3f1c2a1d8e4f5a6"
    # Mint token with version 1
    token = mint_access_token(user_id=user_id, token_version=1)

    # Verify expecting version 2 (simulating global revocation after version increment)
    with pytest.raises(UnauthorizedError, match="revocado"):
        verify_access_token(token, expected_token_version=2)


def test_opaque_token_mint_and_verify():
    plaintext, digest = mint_opaque_token()

    # Plaintext should be non-empty and not equal to digest
    assert isinstance(plaintext, str)
    assert len(plaintext) >= 32
    assert plaintext != digest

    # Verify digest matches original plaintext
    assert verify_opaque_token(plaintext, digest) is True

    # Tampered or wrong plaintext fails
    assert verify_opaque_token(plaintext + "x", digest) is False
    assert verify_opaque_token("completelyWrongPlaintext", digest) is False

    # Direct hash matches digest
    assert hash_opaque_token(plaintext) == digest
