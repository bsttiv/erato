import pytest
from bson import ObjectId
from app.core.errors import ConflictError
from app.db.client import get_db
from app.db.repositories.users import UsersRepository


@pytest.fixture(autouse=True)
async def clean_users_collection():
    db = get_db()
    await db.users.drop()
    repo = UsersRepository(db)
    await repo.ensure_indexes()
    yield
    await db.users.drop()


@pytest.mark.asyncio
async def test_create_user_and_lookup_by_email_and_id():
    repo = UsersRepository()

    user = await repo.create_user(
        email="test@example.com",
        password_hash="argon2id$v=19$m=19456,t=2,p=1$hash123",
        display_name="Test User",
    )

    assert user["_id"] is not None
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test User"
    assert user["token_version"] == 1
    assert "created_at" in user

    # Lookup by email
    found_by_email = await repo.get_by_email("test@example.com")
    assert found_by_email is not None
    assert found_by_email["_id"] == user["_id"]

    # Lookup by case-insensitive email
    found_case_insensitive = await repo.get_by_email("TEST@EXAMPLE.COM")
    assert found_case_insensitive is not None
    assert found_case_insensitive["_id"] == user["_id"]

    # Lookup by id (string and ObjectId)
    found_by_id_str = await repo.get_by_id(str(user["_id"]))
    assert found_by_id_str is not None
    assert found_by_id_str["email"] == "test@example.com"

    found_by_id_obj = await repo.get_by_id(user["_id"])
    assert found_by_id_obj is not None
    assert found_by_id_obj["_id"] == user["_id"]


@pytest.mark.asyncio
async def test_duplicate_email_raises_conflict_error():
    repo = UsersRepository()

    await repo.create_user(
        email="unique@example.com",
        password_hash="hash1",
        display_name="User One",
    )

    with pytest.raises(ConflictError):
        await repo.create_user(
            email="unique@example.com",
            password_hash="hash2",
            display_name="User Two",
        )

    # Also case-insensitive duplicate
    with pytest.raises(ConflictError):
        await repo.create_user(
            email="UNIQUE@example.com",
            password_hash="hash3",
            display_name="User Three",
        )


@pytest.mark.asyncio
async def test_lookup_nonexistent_returns_none():
    repo = UsersRepository()

    assert await repo.get_by_email("nonexistent@example.com") is None
    assert await repo.get_by_id(str(ObjectId())) is None
    assert await repo.get_by_id("invalid-object-id") is None
