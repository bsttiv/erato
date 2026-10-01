from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId

from app.core.errors import NotFoundError, UnauthorizedError
from app.db.client import get_db
from app.db.repositories.invitations import InvitationsRepository


@pytest.fixture(autouse=True)
async def clean_invitations():
    db = get_db()
    await db.invitations.drop()
    repo = InvitationsRepository(db)
    await repo.ensure_indexes()
    yield
    await db.invitations.drop()


@pytest.mark.asyncio
async def test_ttl_index_exists():
    repo = InvitationsRepository()
    indexes = await repo.collection.index_information()

    ttl_index = None
    for idx_name, idx_info in indexes.items():
        key_fields = [k[0] for k in idx_info.get("key", [])]
        if "expires_at" in key_fields and "expireAfterSeconds" in idx_info:
            ttl_index = idx_info
            break

    assert ttl_index is not None
    assert ttl_index["expireAfterSeconds"] == 0


@pytest.mark.asyncio
async def test_create_and_redeem_invitation_idempotent():
    repo = InvitationsRepository()
    comp_id = ObjectId()
    creator_id = ObjectId()
    token_hash = "sha256_invite_hash_123"
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)

    inv = await repo.create_invitation(
        composition_id=comp_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_by=creator_id,
        role="editor",
    )

    assert inv["_id"] is not None
    assert inv["composition_id"] == comp_id
    assert inv["used_at"] is None
    assert inv["role"] == "editor"

    # First redemption: marks used_at
    redeemed_1 = await repo.redeem_invitation(token_hash)
    assert redeemed_1["used_at"] is not None
    first_used_at = redeemed_1["used_at"]

    # Second redemption (replay): is idempotent, returns doc with original used_at intact
    redeemed_2 = await repo.redeem_invitation(token_hash)
    assert redeemed_2["used_at"] == first_used_at


@pytest.mark.asyncio
async def test_redeem_expired_or_nonexistent_invitation():
    repo = InvitationsRepository()
    comp_id = ObjectId()
    creator_id = ObjectId()
    past = datetime.now(timezone.utc) - timedelta(days=1)

    expired_hash = "sha256_expired_hash"
    await repo.create_invitation(
        composition_id=comp_id,
        token_hash=expired_hash,
        expires_at=past,
        created_by=creator_id,
    )

    with pytest.raises(UnauthorizedError, match="expirada"):
        await repo.redeem_invitation(expired_hash)

    with pytest.raises(NotFoundError):
        await repo.redeem_invitation("nonexistent_hash")
