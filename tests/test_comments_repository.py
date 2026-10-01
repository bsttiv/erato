from bson import ObjectId
import pytest

from app.db.client import get_db
from app.db.repositories.comments import CommentsRepository


@pytest.fixture(autouse=True)
async def clean_comments():
    db = get_db()
    await db.composition_comments.drop()
    repo = CommentsRepository(db)
    await repo.ensure_indexes()
    yield
    await db.composition_comments.drop()


@pytest.mark.asyncio
async def test_compound_index_exists():
    repo = CommentsRepository()
    indexes = await repo.collection.index_information()

    compound_found = False
    for name, info in indexes.items():
        keys = info.get("key", [])
        if keys == [("composition_id", 1), ("demo_id", 1), ("created_at", 1)]:
            compound_found = True
            break
    assert compound_found is True


@pytest.mark.asyncio
async def test_create_and_list_demo_comments():
    repo = CommentsRepository()
    comp_id = ObjectId()
    demo_id = "demo_take_1"
    author1 = ObjectId()
    author2 = ObjectId()

    # Create timestamp-anchored comments
    c1 = await repo.create_comment(
        composition_id=comp_id,
        demo_id=demo_id,
        author_id=author1,
        timestamp_s=12.5,
        text="Aca entra la guitarra",
    )
    assert c1["_id"] is not None
    assert c1["timestamp_s"] == 12.5
    assert c1["text"] == "Aca entra la guitarra"

    c2 = await repo.create_comment(
        composition_id=comp_id,
        demo_id=demo_id,
        author_id=author2,
        timestamp_s=45.0,
        text="Subir el volumen aca",
    )
    assert c2["_id"] is not None

    # Another comment on a different demo should not appear in this list
    await repo.create_comment(
        composition_id=comp_id,
        demo_id="other_demo",
        author_id=author1,
        timestamp_s=5.0,
        text="Ignored comment",
    )

    # List comments for demo_id in order
    comments = await repo.list_comments(comp_id, demo_id)
    assert len(comments) == 2
    assert comments[0]["_id"] == c1["_id"]
    assert comments[1]["_id"] == c2["_id"]
