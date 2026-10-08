from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId

from app.core.errors import NotFoundError
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


def test_legacy_repository_methods_removed():
    assert not hasattr(InvitationsRepository, 'create_invitation')
    assert not hasattr(InvitationsRepository, 'redeem_invitation')


@pytest.mark.asyncio
async def test_band_invitation_shape_multi_use_and_scoped_deletion():
    repo = InvitationsRepository()
    band, creator = ObjectId(), ObjectId()
    expiry = datetime.now(timezone.utc) + timedelta(days=14)
    invitation = await repo.create_band_invitation(str(band), "band-token", expiry, str(creator))
    assert set(invitation) == {"_id", "target", "token_hash", "expires_at", "created_by", "created_at"}
    assert invitation["target"] == {"type": "band", "id": band}
    assert invitation["created_by"] == creator
    for _ in range(2):
        redeemed = await repo.redeem_band_invitation("band-token")
        assert redeemed["_id"] == invitation["_id"]
        assert "used_at" not in redeemed
    assert "used_at" not in await repo.get_by_hash("band-token")
    await repo.create_band_invitation(ObjectId(), "other-band", expiry, creator)
    legacy = await repo.collection.insert_one({"composition_id": band, "token_hash": "legacy"})
    assert [doc["_id"] for doc in await repo.list_by_band(str(band))] == [invitation["_id"]]
    assert await repo.delete_by_band(str(band)) == 1
    assert await repo.delete_by_band(band) == 0
    assert await repo.get_by_hash("other-band") is not None
    assert await repo.get_by_id(legacy.inserted_id) is not None


@pytest.mark.asyncio
async def test_band_redeem_legacy_expired_and_unknown():
    from app.core.errors import GoneError

    repo = InvitationsRepository()
    now = datetime.now(timezone.utc)
    await repo.collection.insert_one({"composition_id": ObjectId(), "token_hash": "legacy",
                                      "expires_at": now + timedelta(days=14)})
    await repo.create_band_invitation(ObjectId(), "expired", now - timedelta(seconds=1), ObjectId())
    for token, code in (("legacy", "invitation_legacy"), ("expired", "invitation_expired")):
        with pytest.raises(GoneError) as caught:
            await repo.redeem_band_invitation(token)
        assert caught.value.status_code == 410
        assert caught.value.code == code
    with pytest.raises(NotFoundError):
        await repo.redeem_band_invitation("unknown")
