from bson import ObjectId
from datetime import datetime, timezone
import pytest
from pymongo.errors import DuplicateKeyError

from app.db.client import get_db
from app.db.repositories.section_revisions import SectionRevisionsRepository


@pytest.fixture(autouse=True)
async def clean_section_revisions():
    db = get_db()
    await db.section_revisions.drop()
    repo = SectionRevisionsRepository(db)
    await repo.ensure_indexes()
    yield
    await db.section_revisions.drop()


@pytest.mark.asyncio
async def test_unique_compound_index():
    repo = SectionRevisionsRepository()
    indexes = await repo.collection.index_information()

    assert "uq_section_revisions_comp_section_rev" in indexes
    idx_info = indexes["uq_section_revisions_comp_section_rev"]
    assert idx_info["unique"] is True
    assert idx_info["key"] == [("composition_id", 1), ("section", 1), ("rev", -1)]

    cid = ObjectId()
    author_id = ObjectId()
    await repo.insert_revision(cid, "lyrics", 1, {"content": "v1"}, author_id)

    with pytest.raises(DuplicateKeyError):
        await repo.insert_revision(cid, "lyrics", 1, {"content": "v1 duplicate"}, author_id)


@pytest.mark.asyncio
async def test_insert_and_get_by_rev():
    repo = SectionRevisionsRepository()
    cid = ObjectId()
    author_id = ObjectId()

    doc = await repo.insert_revision(
        composition_id=cid,
        section="chords",
        rev=1,
        content={"instrument": "guitar", "entries": []},
        author_id=author_id,
    )
    assert doc["_id"] is not None
    assert doc["composition_id"] == cid
    assert doc["section"] == "chords"
    assert doc["rev"] == 1
    assert doc["author_id"] == author_id
    assert isinstance(doc["created_at"], datetime)

    retrieved = await repo.get_by_rev(cid, "chords", 1)
    assert retrieved is not None
    assert retrieved["_id"] == doc["_id"]
    assert retrieved["rev"] == 1

    missing = await repo.get_by_rev(cid, "chords", 99)
    assert missing is None


@pytest.mark.asyncio
async def test_prune_revisions():
    repo = SectionRevisionsRepository()
    cid = ObjectId()
    author_id = ObjectId()

    for r in range(1, 56):
        await repo.insert_revision(cid, "lyrics", r, {"content": f"line {r}"}, author_id)

    # Prune rev <= 55 - 50 = 5
    deleted_count = await repo.prune_revisions(cid, "lyrics", max_rev=5)
    assert deleted_count == 5

    remaining = await repo.list_revisions(cid, "lyrics", limit=100)
    assert len(remaining) == 50
    assert remaining[0]["rev"] == 55
    assert remaining[-1]["rev"] == 6


@pytest.mark.asyncio
async def test_list_revisions_pagination_and_ordering():
    repo = SectionRevisionsRepository()
    cid = ObjectId()
    author_id = ObjectId()

    for r in range(1, 11):
        await repo.insert_revision(cid, "tablature", r, {"strings": 6}, author_id)

    # Page 1: newest first
    page1 = await repo.list_revisions(cid, "tablature", skip=0, limit=5)
    assert len(page1) == 5
    assert [d["rev"] for d in page1] == [10, 9, 8, 7, 6]

    # Page 2
    page2 = await repo.list_revisions(cid, "tablature", skip=5, limit=5)
    assert len(page2) == 5
    assert [d["rev"] for d in page2] == [5, 4, 3, 2, 1]


@pytest.mark.asyncio
async def test_get_newest_at_or_below():
    repo = SectionRevisionsRepository()
    cid = ObjectId()
    author_id = ObjectId()

    await repo.insert_revision(cid, "lyrics", 1, {"content": "one"}, author_id)
    await repo.insert_revision(cid, "lyrics", 3, {"content": "three"}, author_id)
    await repo.insert_revision(cid, "lyrics", 7, {"content": "seven"}, author_id)

    # Exact match
    rev3 = await repo.get_newest_at_or_below(cid, "lyrics", 3)
    assert rev3 is not None
    assert rev3["rev"] == 3

    # Match below
    rev5 = await repo.get_newest_at_or_below(cid, "lyrics", 5)
    assert rev5 is not None
    assert rev5["rev"] == 3

    # None below 1
    rev0 = await repo.get_newest_at_or_below(cid, "lyrics", 0)
    assert rev0 is None


@pytest.mark.asyncio
async def test_delete_by_composition():
    repo = SectionRevisionsRepository()
    cid1 = ObjectId()
    cid2 = ObjectId()
    author_id = ObjectId()

    await repo.insert_revision(cid1, "lyrics", 1, {"content": "c1"}, author_id)
    await repo.insert_revision(cid1, "chords", 1, {"content": "c1 chords"}, author_id)
    await repo.insert_revision(cid2, "lyrics", 1, {"content": "c2"}, author_id)

    deleted = await repo.delete_by_composition(cid1)
    assert deleted == 2

    assert len(await repo.list_revisions(cid1, "lyrics")) == 0
    assert len(await repo.list_revisions(cid1, "chords")) == 0
    assert len(await repo.list_revisions(cid2, "lyrics")) == 1
