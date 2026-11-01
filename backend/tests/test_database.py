"""Approved INFRA-011–014 real-database isolation and transaction checks."""
import os
from datetime import datetime, timezone, timedelta
import hashlib

from argon2 import PasswordHasher

from bson import ObjectId
import pytest


def documents():
    now = datetime.now(timezone.utc)
    user_id = ObjectId()
    return ({"_id": user_id, "email": "transaction@example.com", "username": "transaction",
             "display_name": "Transaction", "password_hash": PasswordHasher().hash("aaaaaaaa"),
             "created_at": now, "updated_at": now},
            {"_id": ObjectId(), "user_id": user_id, "sid": "transaction",
             "refresh_token_hash": hashlib.sha256(b"fixture-refresh").hexdigest(), "device": "Dispositivo desconocido",
             "last_access_at": now, "created_at": now, "expires_at": now + timedelta(days=7)})


def test_infra_011_transaction_commit(db):
    user, metadata = documents()
    with db.client.start_session() as session:
        with session.start_transaction():
            db.users.insert_one(user, session=session)
            db.sessions.insert_one(metadata, session=session)
    assert db.users.count_documents({"_id": user["_id"]}) == 1
    assert db.sessions.count_documents({"_id": metadata["_id"]}) == 1


def test_infra_012_transaction_abort(db):
    user, metadata = documents()
    with db.client.start_session() as session:
        with pytest.raises(RuntimeError, match="Abort"):
            with session.start_transaction():
                db.users.insert_one(user, session=session)
                db.sessions.insert_one(metadata, session=session)
                raise RuntimeError("Abort")
    assert db.users.count_documents({"_id": user["_id"]}) == 0
    assert db.sessions.count_documents({"_id": metadata["_id"]}) == 0


def test_infra_013_exclusive_database(db):
    assert db.name == os.environ["MONGODB_DB"]
    assert db.name.startswith("erato_test_") and len(db.name.rsplit("_", 1)[1]) == 32
    assert db.name not in ("erato_local", "erato_test")


def test_infra_014_clean_documents_preserved_indexes(db):
    for name in db.list_collection_names():
        assert db[name].count_documents({}) == 0
    assert db.users.index_information()["email_1"]["unique"] is True
    assert db.users.index_information()["username_1"]["unique"] is True
    assert db.sessions.index_information()["sid_1"]["unique"] is True
    assert db.sessions.index_information()["expires_at_1"]["expireAfterSeconds"] == 0
    assert db.login_attempts.index_information()["created_at_1"]["expireAfterSeconds"] == 900
    assert db.login_attempts.index_information()["email_hash_1_ip_1_created_at_1"]["key"] == [
        ("email_hash", 1), ("ip", 1), ("created_at", 1),
    ]
