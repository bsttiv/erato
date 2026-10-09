from bson import ObjectId
import pytest

from app.core.errors import NotFoundError, PlanGateError, SectionConflictError

from app.db.client import get_db
from app.db.repositories.compositions import CompositionsRepository
from app.db.repositories.section_revisions import SectionRevisionsRepository
from app.db.repositories.users import UsersRepository
from app.services.composition_service import CompositionService
from app.services.versioning_service import VersioningService


@pytest.fixture(autouse=True)
async def clean_db():
    db = get_db()
    await db.users.drop()
    await db.compositions.drop()
    await db.section_revisions.drop()
    await UsersRepository(db).ensure_indexes()
    await CompositionsRepository(db).ensure_indexes()
    await SectionRevisionsRepository(db).ensure_indexes()
    yield
    await db.users.drop()
    await db.compositions.drop()
    await db.section_revisions.drop()


@pytest.mark.asyncio
async def test_update_versioned_section_expected_rev_zero_matches_missing_counter():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user = await users_repo.create_user("owner@test.com", "hash", "Owner")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Song 1")
    cid = str(comp["_id"])
    author_id = str(user["_id"])

    service = VersioningService()

    # expected_rev=0 on a fresh composition with no section_revs
    content = {"content": "First lyrics line"}
    updated, new_rev = await service.update_versioned_section(
        composition_id=cid,
        section_name="lyrics",
        content=content,
        author_id=author_id,
        expected_rev=0,
    )

    assert new_rev == 1
    assert updated["content"] == "First lyrics line"

    # Verify composition document in DB has section_revs.lyrics == 1
    stored = await compositions_repo.get_by_id(cid)
    assert stored["section_revs"]["lyrics"] == 1
    assert stored["lyrics"]["content"] == "First lyrics line"

    # Verify a snapshot was created
    revisions_repo = SectionRevisionsRepository()
    snaps = await revisions_repo.list_revisions(cid, "lyrics")
    assert len(snaps) == 1
    assert snaps[0]["rev"] == 1
    assert snaps[0]["content"] == content
    assert snaps[0]["author_id"] == user["_id"]


@pytest.mark.asyncio
async def test_update_versioned_section_matching_expected_rev_bumps():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user = await users_repo.create_user("owner2@test.com", "hash", "Owner 2")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Song 2")
    cid = str(comp["_id"])
    author_id = str(user["_id"])
    service = VersioningService()

    # Save v1
    await service.update_versioned_section(cid, "lyrics", {"content": "v1"}, author_id, expected_rev=0)

    # Save v2 with expected_rev=1
    updated, new_rev = await service.update_versioned_section(
        cid, "lyrics", {"content": "v2"}, author_id, expected_rev=1
    )
    assert new_rev == 2
    assert updated["content"] == "v2"

    stored = await compositions_repo.get_by_id(cid)
    assert stored["section_revs"]["lyrics"] == 2


@pytest.mark.asyncio
async def test_update_versioned_section_stale_raises_conflict_with_author_details():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user1 = await users_repo.create_user("u1@test.com", "hash", "Alice Writer")
    user2 = await users_repo.create_user("u2@test.com", "hash", "Bob Writer")
    comp = await compositions_repo.create_composition(owner_id=user1["_id"], title="Conflict Song")
    cid = str(comp["_id"])

    service = VersioningService()
    # Save v1 by Alice
    await service.update_versioned_section(cid, "lyrics", {"content": "Alice line"}, str(user1["_id"]), expected_rev=0)

    # Bob tries to save with expected_rev=0 (stale)
    with pytest.raises(SectionConflictError) as exc_info:
        await service.update_versioned_section(
            cid, "lyrics", {"content": "Bob line"}, str(user2["_id"]), expected_rev=0
        )

    err = exc_info.value
    assert err.status_code == 409
    assert err.code == "section_conflict"
    assert err.section == "lyrics"
    assert err.current_rev == 1
    assert err.content == {"content": "Alice line"}
    assert err.author == {"id": str(user1["_id"]), "display_name": "Alice Writer"}
    assert err.updated_at is not None

    payload = err.to_dict()
    assert payload["error"] == "section_conflict"
    assert payload["section"] == "lyrics"
    assert payload["current_rev"] == 1
    assert payload["author"]["display_name"] == "Alice Writer"


@pytest.mark.asyncio
async def test_update_versioned_section_without_expected_rev_last_write_wins():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user = await users_repo.create_user("u3@test.com", "hash", "Carol")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="LWW Song")
    cid = str(comp["_id"])
    author_id = str(user["_id"])
    service = VersioningService()

    # Save v1 without expected_rev
    _, rev1 = await service.update_versioned_section(cid, "chords", {"instrument": "guitar"}, author_id)
    assert rev1 == 1

    # Save v2 without expected_rev
    _, rev2 = await service.update_versioned_section(cid, "chords", {"instrument": "piano"}, author_id)
    assert rev2 == 2

    stored = await compositions_repo.get_by_id(cid)
    assert stored["section_revs"]["chords"] == 2
    assert stored["chords"]["instrument"] == "piano"


@pytest.mark.asyncio
async def test_identical_content_creates_no_snapshot():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user = await users_repo.create_user("u4@test.com", "hash", "Dave")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Identical Song")
    cid = str(comp["_id"])
    author_id = str(user["_id"])
    service = VersioningService()
    revisions_repo = SectionRevisionsRepository()

    # Save v1
    content = {"content": "same content"}
    await service.update_versioned_section(cid, "lyrics", content, author_id, expected_rev=0)
    assert len(await revisions_repo.list_revisions(cid, "lyrics")) == 1

    # Save identical content with expected_rev=1 -> rev bumps to 2, but NO new snapshot
    _, rev2 = await service.update_versioned_section(cid, "lyrics", content, author_id, expected_rev=1)
    assert rev2 == 2

    snaps = await revisions_repo.list_revisions(cid, "lyrics")
    assert len(snaps) == 1
    assert snaps[0]["rev"] == 1


@pytest.mark.asyncio
async def test_snapshot_failure_is_swallowed_and_logged(monkeypatch):
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    user = await users_repo.create_user("u5@test.com", "hash", "Eve")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Swallow Song")
    cid = str(comp["_id"])
    author_id = str(user["_id"])
    service = VersioningService()

    async def boom(*args, **kwargs):
        raise RuntimeError("MongoDB disk full")

    monkeypatch.setattr(SectionRevisionsRepository, "insert_revision", boom)

    # Save must succeed despite snapshot failure
    updated, new_rev = await service.update_versioned_section(
        cid, "lyrics", {"content": "survives snapshot failure"}, author_id, expected_rev=0
    )
    assert new_rev == 1
    assert updated["content"] == "survives snapshot failure"


@pytest.mark.asyncio
async def test_missing_or_deleted_composition_raises_not_found_not_conflict():
    service = VersioningService()
    fake_cid = str(ObjectId())

    with pytest.raises(NotFoundError):
        await service.update_versioned_section(
            fake_cid, "lyrics", {"content": "hello"}, str(ObjectId()), expected_rev=0
        )


@pytest.mark.asyncio
async def test_cascade_delete_snapshots_on_composition_delete():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    revisions_repo = SectionRevisionsRepository()
    comp_service = CompositionService()

    user = await users_repo.create_user("u6@test.com", "hash", "Frank")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Cascade Song")
    cid = str(comp["_id"])

    # Create snapshots
    await revisions_repo.insert_revision(cid, "lyrics", 1, {"content": "snap 1"}, user["_id"])
    await revisions_repo.insert_revision(cid, "lyrics", 2, {"content": "snap 2"}, user["_id"])
    assert len(await revisions_repo.list_revisions(cid, "lyrics")) == 2

    # Delete composition
    await comp_service.delete_composition(cid)

    # Snapshots must be cascade deleted
    assert len(await revisions_repo.list_revisions(cid, "lyrics")) == 0


class DummyRecordingPolicy:
    def __init__(self, allow_history: bool = True) -> None:
        self.allow_history = allow_history
        self.calls = []

    async def can_share_with_people(self, user_id: str) -> bool:
        return True

    async def can_create_band(self, user_id: str) -> bool:
        return True

    async def can_view_history(self, user_id: str) -> bool:
        self.calls.append((user_id,))
        return self.allow_history

    async def demo_limit(self, user_id: str):
        return None

    async def seat_limit(self, band_id: str):
        return None

    async def is_band_active(self, band_id: str) -> bool:
        return True

    async def confirm_band_transfer(self, band_id: str, prev_id: str, new_id: str) -> bool:
        return True

    async def abort_band_transfer(self, band_id: str, previous_owner_id: str, new_owner_id: str) -> None:
        return None


@pytest.mark.asyncio
async def test_service_history_invalid_section_raises_not_found():
    service = VersioningService()
    cid = str(ObjectId())
    uid = str(ObjectId())

    for invalid_sec in ["todos", "title", "section_revs", "unknown"]:
        with pytest.raises(NotFoundError):
            await service.list_history(cid, invalid_sec, uid)

        with pytest.raises(NotFoundError):
            await service.get_history_revision(cid, invalid_sec, 1, uid)

        with pytest.raises(NotFoundError):
            await service.restore_history_revision(cid, invalid_sec, 1, uid, expected_rev=0)


@pytest.mark.asyncio
async def test_service_history_gate_denies_raises_plan_gate_error_and_preserves_content():
    compositions_repo = CompositionsRepository()
    users_repo = UsersRepository()
    revisions_repo = SectionRevisionsRepository()

    user = await users_repo.create_user("gate_user@test.com", "hash", "Gate User")
    comp = await compositions_repo.create_composition(owner_id=user["_id"], title="Gate Comp")
    cid = str(comp["_id"])
    uid = str(user["_id"])

    # Create one snapshot
    await revisions_repo.insert_revision(cid, "lyrics", 1, {"content": "initial snap"}, user["_id"])

    deny_policy = DummyRecordingPolicy(allow_history=False)
    service = VersioningService(policy=deny_policy)

    with pytest.raises(PlanGateError) as exc_list:
        await service.list_history(cid, "lyrics", uid)
    assert exc_list.value.code == "plan_gate_history"

    with pytest.raises(PlanGateError) as exc_get:
        await service.get_history_revision(cid, "lyrics", 1, uid)
    assert exc_get.value.code == "plan_gate_history"

    with pytest.raises(PlanGateError) as exc_res:
        await service.restore_history_revision(cid, "lyrics", 1, uid, expected_rev=0)
    assert exc_res.value.code == "plan_gate_history"

    # Policy must have received exactly (user_id,)
    assert len(deny_policy.calls) == 3
    for call in deny_policy.calls:
        assert call == (uid,)

    # Restore denial must not modify composition content or revision
    comp_after = await compositions_repo.get_by_id(cid)
    assert comp_after.get("lyrics") is None or comp_after.get("lyrics") == ""
    assert comp_after.get("section_revs") is None or comp_after.get("section_revs") == {}

