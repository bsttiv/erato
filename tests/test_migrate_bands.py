"""Integration coverage for AD14 migration and restoration safety."""
import importlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from bson import ObjectId, json_util
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from app.settings import get_settings

TEST_DB = "erato_migration_test"


@pytest.fixture(autouse=True)
async def legacy_db(monkeypatch, set_test_env, tmp_path):
    monkeypatch.setenv("MONGODB_DB", TEST_DB)
    get_settings.cache_clear()
    monkeypatch.chdir(tmp_path)
    client = AsyncMongoClient(get_settings().mongodb_uri)
    await client.drop_database(TEST_DB)
    db = client[TEST_DB]
    member = {"user_id": ObjectId(), "role": "editor"}
    await db.compositions.insert_many([
        {"_id": ObjectId(), "members": [member]},
        {"_id": ObjectId(), "band_id": None, "members": [member]},
        {"_id": ObjectId(), "band_id": ObjectId(), "members": [member]},
        {"_id": ObjectId(), "members": []},
        {"_id": ObjectId()},
    ])
    await db.invitations.insert_many([
        {"_id": ObjectId(), "composition_id": ObjectId(), "role": "editor",
         "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc), "count": 2},
        {"_id": ObjectId(), "target": {"type": "band", "id": ObjectId()}},
        {"_id": ObjectId(), "composition_id": ObjectId(), "target": None},
        {"_id": ObjectId(), "token_hash": "unrelated"},
    ])
    await db.invitations.create_index("composition_id", name="idx_invitations_composition_id")
    yield db
    await client.drop_database(TEST_DB)
    await client.close()


async def snapshot(db):
    return {name: await db[name].find().sort("_id", 1).to_list(None)
            for name in ("compositions", "invitations")}


def migration():
    return importlib.import_module("scripts.migrate_bands")


def restoration():
    return importlib.import_module("scripts.restore_bands_migration")


def backup_file():
    files = list(Path("backups").glob("migrate_bands-*.json"))
    assert len(files) == 1
    return files[0]


@pytest.mark.asyncio
async def test_default_dry_run(legacy_db, capsys):
    before = await snapshot(legacy_db)
    indexes = await legacy_db.invitations.index_information()
    assert await migration().run() == 0
    output = capsys.readouterr().out
    assert "DRY RUN" in output
    for doc in before["compositions"] + before["invitations"]:
        legacy_composition = doc.get("band_id") is None and bool(doc.get("members"))
        legacy_invitation = "composition_id" in doc and "target" not in doc
        if legacy_composition or legacy_invitation:
            assert str(doc["_id"]) in output
    assert await snapshot(legacy_db) == before
    assert await legacy_db.invitations.index_information() == indexes
    assert not Path("backups").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("confirm", [None, "wrong_database"])
async def test_apply_requires_matching_confirmation(legacy_db, confirm):
    before = await snapshot(legacy_db)
    assert await migration().run(apply=True, confirm_db=confirm) == 1
    assert await snapshot(legacy_db) == before
    assert not Path("backups").exists()


@pytest.mark.asyncio
async def test_apply_backup_precedes_every_mutation_and_is_idempotent(legacy_db, monkeypatch, capsys):
    module = migration()
    before = await snapshot(legacy_db)
    synced = []
    real_fsync = module.os.fsync

    def fsync(fd):
        real_fsync(fd)
        synced.append(True)

    monkeypatch.setattr(module.os, "fsync", fsync)
    for name in ("update_one", "delete_many", "drop_index", "create_index"):
        original = getattr(AsyncCollection, name)

        async def guarded(self, *args, _original=original, **kwargs):
            assert synced, "Database mutation before durable backup"
            return await _original(self, *args, **kwargs)

        monkeypatch.setattr(AsyncCollection, name, guarded)
    assert await module.run(apply=True, confirm_db=TEST_DB) == 0
    path = backup_file()
    raw = path.read_text()
    backup = json_util.loads(raw)
    expected = {"compositions": [{"_id": d["_id"], "members": d["members"]}
                                 for d in before["compositions"] if d.get("band_id") is None and d.get("members")],
                "invitations": [d for d in before["invitations"] if "composition_id" in d and "target" not in d]}
    assert backup == expected
    assert raw == json_util.dumps(backup, json_options=json_util.CANONICAL_JSON_OPTIONS)
    assert "$numberInt" in raw and "$date" in raw
    after = await snapshot(legacy_db)
    for doc in before["compositions"]:
        actual = next(d for d in after["compositions"] if d["_id"] == doc["_id"])
        legacy = doc.get("band_id") is None and bool(doc.get("members"))
        assert actual == (dict(doc, members=[]) if legacy else doc)
    assert after["invitations"] == [d for d in before["invitations"] if d not in expected["invitations"]]
    indexes = await legacy_db.invitations.index_information()
    assert "idx_invitations_composition_id" not in indexes
    assert indexes["idx_invitations_target"]["key"] == [("target.type", 1), ("target.id", 1)]
    assert await module.run(apply=True, confirm_db=TEST_DB) == 0
    assert "nada que migrar" in capsys.readouterr().out
    assert await snapshot(legacy_db) == after
    assert backup_file() == path


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["directory", "fsync"])
async def test_failed_backup_has_zero_mutations(legacy_db, monkeypatch, failure):
    module = migration()
    before = await snapshot(legacy_db)
    indexes = await legacy_db.invitations.index_information()
    if failure == "directory":
        # A file in place of the directory fails reliably even when running as root.
        Path("backups").write_text("blocked")
    else:
        def fail(fd):
            raise OSError("fsync failed")
        monkeypatch.setattr(module.os, "fsync", fail)
    assert await module.run(apply=True, confirm_db=TEST_DB) == 1
    assert await snapshot(legacy_db) == before
    assert await legacy_db.invitations.index_information() == indexes


@pytest.mark.asyncio
async def test_restore_round_trip_and_duplicate_ids(legacy_db):
    restore = restoration()
    before = await snapshot(legacy_db)
    assert await migration().run(apply=True, confirm_db=TEST_DB) == 0
    assert await restore.run(backup=backup_file(), confirm_db=TEST_DB) == 0
    assert await snapshot(legacy_db) == before
    assert "idx_invitations_composition_id" in await legacy_db.invitations.index_information()
    assert await restore.run(backup=backup_file(), confirm_db=TEST_DB) == 0
    assert await snapshot(legacy_db) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("confirm", [None, "wrong_database"])
async def test_restore_requires_matching_confirmation(legacy_db, confirm):
    restore = restoration()
    before = await snapshot(legacy_db)
    assert await restore.run(backup=Path("missing.json"), confirm_db=confirm) == 1
    assert await snapshot(legacy_db) == before
