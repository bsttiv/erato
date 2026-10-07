from datetime import datetime

import pytest
from bson import ObjectId

from app.db.client import get_db
from app.db.repositories.bands import BandsRepository


@pytest.fixture(autouse=True)
async def clean_bands():
    await get_db().bands.drop()
    yield
    await get_db().bands.drop()


@pytest.mark.asyncio
async def test_band_shape_lookup_members_rename_and_remove():
    repo = BandsRepository()
    owner, member = ObjectId(), ObjectId()
    band = await repo.insert(name="Quartet", owner_id=str(owner))
    assert set(band) == {"_id", "name", "owner_id", "members", "pending_transfer", "created_at", "updated_at"}
    assert band["owner_id"] == owner
    assert band["members"] == [{"user_id": owner, "role": "owner"}]
    assert band["pending_transfer"] is None
    assert isinstance(band["created_at"], datetime)
    assert band["created_at"] == band["updated_at"]
    bid = str(band["_id"])
    assert (await repo.get_by_id(bid))["name"] == "Quartet"
    assert await repo.get_by_id("invalid") is None
    assert await repo.get_by_id(ObjectId()) is None
    assert len(await repo.list_by_member(str(owner))) == 1
    assert await repo.list_by_member(member) == []
    await repo.collection.update_one({"_id": band["_id"]}, {"$push": {"members": {"user_id": member, "role": "member"}}})
    assert len(await repo.list_by_member(member)) == 1
    renamed = await repo.rename(bid, "Quintet")
    assert renamed["name"] == "Quintet"
    assert renamed["updated_at"] >= renamed["created_at"]
    await repo.remove_member(bid, str(member))
    await repo.remove_member(bid, str(member))
    await repo.remove_member(bid, str(owner))
    assert (await repo.get_by_id(bid))["members"] == [{"user_id": owner, "role": "owner"}]
    assert await repo.list_by_member(member) == []
    assert await repo.rename(str(ObjectId()), "Missing") is None


@pytest.mark.asyncio
async def test_band_indexes_allow_multiple_bands_per_owner():
    repo = BandsRepository()
    await repo.ensure_indexes()
    await repo.ensure_indexes()
    owner = ObjectId()
    await repo.insert("Same name", owner)
    await repo.insert("Same name", owner)
    assert len(await repo.list_by_member(owner)) == 2
    indexes = await repo.collection.index_information()
    assert indexes["idx_bands_owner_id"]["key"] == [("owner_id", 1)]
    assert indexes["idx_bands_members_user_id"]["key"] == [("members.user_id", 1)]
