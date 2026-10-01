import pytest

from pymongo import AsyncMongoClient

from app.db.repositories.refresh_tokens import RefreshTokensRepository
from app.settings import get_settings
from scripts.ensure_indexes import run

TEST_DB = "erato_indexes_test"


@pytest.fixture(autouse=True)
async def indexes_db(monkeypatch, set_test_env):
    monkeypatch.setenv("MONGODB_DB", TEST_DB)
    get_settings.cache_clear()
    # Independent client: run() closes the app's client when it finishes.
    client = AsyncMongoClient(get_settings().mongodb_uri)
    await client.drop_database(TEST_DB)
    yield client[TEST_DB]
    await client.drop_database(TEST_DB)
    await client.close()


async def _indexes(db, name):
    return await db[name].index_information()


@pytest.mark.asyncio
async def test_run_creates_expected_indexes(indexes_db, capsys):
    assert await run() == 0

    users = await _indexes(indexes_db, "users")
    assert users["uq_users_email"]["unique"] is True

    comps = await _indexes(indexes_db, "compositions")
    assert comps["uq_sparse_compositions_share_slug"]["unique"] is True

    for coll, ttl, uq in (
        ("refresh_tokens", "ttl_refresh_tokens_expires_at", "uq_refresh_tokens_hash"),
        ("invitations", "ttl_invitations_expires_at", "uq_invitations_token_hash"),
    ):
        info = await _indexes(indexes_db, coll)
        assert info[ttl]["expireAfterSeconds"] == 0
        assert info[uq]["unique"] is True

    comments = await _indexes(indexes_db, "composition_comments")
    assert "idx_composition_demo_comments_created" in comments

    out = capsys.readouterr().out
    assert "users: ok" in out
    assert "mongodb" not in out.lower()


@pytest.mark.asyncio
async def test_run_is_idempotent():
    assert await run() == 0
    assert await run() == 0


@pytest.mark.asyncio
async def test_failure_returns_1_and_continues(indexes_db, monkeypatch, capsys):
    async def boom(self):
        raise RuntimeError("duplicate key")

    monkeypatch.setattr(RefreshTokensRepository, "ensure_indexes", boom)

    assert await run() == 1

    out = capsys.readouterr().out
    assert "refresh_tokens: error" in out
    assert "duplicate key" in out
    assert "comments: ok" in out
    assert "idx_composition_demo_comments_created" in await _indexes(
        indexes_db, "composition_comments"
    )
