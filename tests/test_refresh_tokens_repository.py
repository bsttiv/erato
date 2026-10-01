from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId
from app.core.errors import UnauthorizedError
from app.db.client import get_db
from app.db.repositories.refresh_tokens import RefreshTokensRepository


@pytest.fixture(autouse=True)
async def clean_refresh_tokens_collection():
    db = get_db()
    await db.refresh_tokens.drop()
    repo = RefreshTokensRepository(db)
    await repo.ensure_indexes()
    yield
    await db.refresh_tokens.drop()


@pytest.mark.asyncio
async def test_ttl_index_exists():
    repo = RefreshTokensRepository()
    indexes = await repo.collection.index_information()

    # Find an index that covers 'expires_at' and has expireAfterSeconds == 0
    ttl_index = None
    for idx_name, idx_info in indexes.items():
        key_fields = [k[0] for k in idx_info.get("key", [])]
        if "expires_at" in key_fields and "expireAfterSeconds" in idx_info:
            ttl_index = idx_info
            break

    assert ttl_index is not None
    assert ttl_index["expireAfterSeconds"] == 0


@pytest.mark.asyncio
async def test_store_and_redeem_unexpired_unrevoked_token():
    repo = RefreshTokensRepository()
    user_id = ObjectId()
    family_id = "family_123"
    token_hash = "sha256_dummy_hash_1"
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    created = await repo.create_token(
        token_hash=token_hash,
        user_id=user_id,
        family_id=family_id,
        expires_at=expires_at,
    )
    assert created["token_hash"] == token_hash
    assert created["family_id"] == family_id
    assert created["revoked"] is False

    # Redeem unexpired, unrevoked token -> succeeds and marks it as revoked (consumed)
    redeemed = await repo.redeem_token(token_hash)
    assert redeemed is not None
    assert redeemed["token_hash"] == token_hash
    assert redeemed["family_id"] == family_id
    assert redeemed["user_id"] == user_id

    # Verify that in database it is now revoked
    doc_in_db = await repo.collection.find_one({"token_hash": token_hash})
    assert doc_in_db["revoked"] is True


@pytest.mark.asyncio
async def test_redeeming_already_revoked_token_invalidates_family():
    repo = RefreshTokensRepository()
    user_id = ObjectId()
    family_id = "family_reuse_test"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    # First token in family
    t1_hash = "hash_token_1"
    await repo.create_token(
        token_hash=t1_hash,
        user_id=user_id,
        family_id=family_id,
        expires_at=expires_at,
    )

    # Redeem t1 -> succeeds, marks t1 revoked
    await repo.redeem_token(t1_hash)

    # Successor token in same family issued during rotation
    t2_hash = "hash_token_2"
    await repo.create_token(
        token_hash=t2_hash,
        user_id=user_id,
        family_id=family_id,
        expires_at=expires_at,
    )

    # t2 is currently unrevoked
    t2_doc = await repo.collection.find_one({"token_hash": t2_hash})
    assert t2_doc["revoked"] is False

    # Attempting to redeem t1 again (reuse of consumed token) must fail AND invalidate entire family
    with pytest.raises(UnauthorizedError):
        await repo.redeem_token(t1_hash)

    # Verify that ALL tokens in the family are now revoked (t2 is now revoked)
    t2_doc_after = await repo.collection.find_one({"token_hash": t2_hash})
    assert t2_doc_after["revoked"] is True


@pytest.mark.asyncio
async def test_redeeming_expired_or_nonexistent_token_fails():
    repo = RefreshTokensRepository()
    user_id = ObjectId()
    family_id = "family_expired"
    past = datetime.now(timezone.utc) - timedelta(days=1)

    expired_hash = "hash_expired"
    await repo.create_token(
        token_hash=expired_hash,
        user_id=user_id,
        family_id=family_id,
        expires_at=past,
    )

    with pytest.raises(UnauthorizedError, match="expirado"):
        await repo.redeem_token(expired_hash)

    with pytest.raises(UnauthorizedError, match="inválido"):
        await repo.redeem_token("nonexistent_token_hash")
