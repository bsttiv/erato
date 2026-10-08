from datetime import datetime, timezone
import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.db.client import get_db
from app.db.repositories.compositions import CompositionsRepository


@pytest.fixture(autouse=True)
async def clean_compositions():
    db = get_db()
    await db.compositions.drop()
    repo = CompositionsRepository(db)
    await repo.ensure_indexes()
    yield
    await db.compositions.drop()


@pytest.mark.asyncio
async def test_create_and_lookup_by_id_owner_and_members():
    repo = CompositionsRepository()
    owner_id = ObjectId()
    comp = await repo.create_composition(
        owner_id=owner_id,
        title="Canción 1",
        visibility="private",
    )

    assert comp["_id"] is not None
    assert comp["title"] == "Canción 1"
    assert comp["owner_id"] == owner_id
    assert comp["visibility"] == "private"
    assert "share_slug" not in comp or comp.get("share_slug") is None

    # Lookup by id
    found_by_id = await repo.get_by_id(comp["_id"])
    assert found_by_id is not None
    assert found_by_id["title"] == "Canción 1"

    # Lookup by user (as owner)
    owned_list = await repo.list_by_user(owner_id)
    assert len(owned_list) == 1
    assert owned_list[0]["_id"] == comp["_id"]


@pytest.mark.asyncio
async def test_embed_and_update_sections():
    repo = CompositionsRepository()
    owner_id = ObjectId()
    comp = await repo.create_composition(owner_id=owner_id, title="Test Sections")
    cid = comp["_id"]

    # Update chords
    chords_data = {"instrument": "guitar", "entries": [{"bar": 1, "notes": [0, 4, 7], "name": "C"}]}
    updated = await repo.update_section(cid, "chords", chords_data)
    assert updated["chords"] == chords_data

    # Update tablature
    tab_data = {"strings": 6, "content": "e|---|"}
    updated = await repo.update_section(cid, "tablature", tab_data)
    assert updated["tablature"] == tab_data

    # Update lyrics
    lyrics_data = {"content": "[Am7]Bajo el farol..."}
    updated = await repo.update_section(cid, "lyrics", lyrics_data)
    assert updated["lyrics"] == lyrics_data

    # Update todos
    todos_data = [{"text": "Grabar bajo", "done": False}]
    updated = await repo.update_section(cid, "todos", todos_data)
    assert updated["todos"] == todos_data

    # Update demos
    demo_doc = {
        "demo_id": "d1",
        "cloudinary_public_id": "erato/compositions/123/demo1",
        "title": "Toma 1",
        "duration_s": 182,
        "uploaded_by": owner_id,
        "uploaded_at": datetime.now(timezone.utc),
    }
    updated = await repo.update_section(cid, "demos", [demo_doc])
    assert len(updated["demos"]) == 1
    assert updated["demos"][0]["demo_id"] == "d1"


@pytest.mark.asyncio
async def test_share_slug_unique_sparse_index():
    repo = CompositionsRepository()
    owner1 = ObjectId()
    owner2 = ObjectId()

    # Two private compositions without share_slug should not collide
    comp1 = await repo.create_composition(owner_id=owner1, title="Private 1", visibility="private")
    comp2 = await repo.create_composition(owner_id=owner2, title="Private 2", visibility="private")
    assert comp1["_id"] != comp2["_id"]

    # Public composition with unique slug
    slug = "random_slug_128bit"
    public_comp = await repo.create_composition(
        owner_id=owner1,
        title="Public 1",
        visibility="public",
        share_slug=slug,
    )
    assert public_comp["share_slug"] == slug

    # Lookup by slug
    found_by_slug = await repo.get_by_slug(slug)
    assert found_by_slug is not None
    assert found_by_slug["_id"] == public_comp["_id"]

    # Duplicate slug raises DuplicateKeyError
    with pytest.raises(DuplicateKeyError):
        await repo.create_composition(
            owner_id=owner2,
            title="Public 2",
            visibility="public",
            share_slug=slug,
        )


@pytest.mark.asyncio
async def test_add_and_remove_member():
    repo = CompositionsRepository()
    owner_id = ObjectId()
    member_id = ObjectId()

    comp = await repo.create_composition(owner_id=owner_id, title="Collab")
    cid = comp["_id"]

    # Member cannot find it initially
    assert len(await repo.list_by_user(member_id)) == 0

    # Add member
    await repo.add_member(cid, user_id=member_id, role="editor")
    updated = await repo.get_by_id(cid)
    assert len(updated["members"]) == 1
    assert updated["members"][0]["user_id"] == member_id
    assert updated["members"][0]["role"] == "editor"

    # Member now sees it in their list
    member_list = await repo.list_by_user(member_id)
    assert len(member_list) == 1
    assert member_list[0]["_id"] == cid

    # Remove member
    await repo.remove_member(cid, user_id=member_id)
    final_doc = await repo.get_by_id(cid)
    assert len(final_doc["members"]) == 0
    assert len(await repo.list_by_user(member_id)) == 0


@pytest.mark.asyncio
async def test_set_member_role_concurrent_no_duplicates():
    import asyncio
    repo = CompositionsRepository()
    comp = await repo.create_composition(ObjectId(), 'Roles')
    uid = ObjectId()
    await asyncio.gather(repo.set_member_role(comp['_id'], uid, 'editor'),
                         repo.set_member_role(comp['_id'], uid, 'viewer'))
    members = (await repo.get_by_id(comp['_id']))['members']
    assert len(members) == 1 and members[0]['user_id'] == uid
    assert members[0]['role'] in ('editor', 'viewer')
    await repo.set_member_role(comp['_id'], uid, 'viewer')
    assert (await repo.get_by_id(comp['_id']))['members'] == [{'user_id': uid, 'role': 'viewer'}]
