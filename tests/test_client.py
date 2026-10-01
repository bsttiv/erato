import asyncio
import pytest
from unittest.mock import patch, MagicMock

# 1.11 RED: Assert client reuse within same loop and rebuild on changed/closed loop.

@pytest.mark.asyncio
async def test_get_db_warm_reuse(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("JWT_SECRET", "dummysecret12345678901234567890")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "dummysecret")

    from app.db import client as db_client

    db1 = db_client.get_db()
    db2 = db_client.get_db()

    assert db1 is not None
    assert db2 is not None
    assert db1.client is db2.client


@pytest.mark.asyncio
async def test_get_db_rebuilds_on_loop_change(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("JWT_SECRET", "dummysecret12345678901234567890")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "dummysecret")

    from app.db import client as db_client

    # Get client in current loop
    db_first = db_client.get_db()
    client_first = db_first.client

    # Simulate loop changed by tampering with stored loop or running in a different loop
    old_loop = db_client._client_loop
    fake_loop = MagicMock()
    fake_loop.is_closed.return_value = True
    db_client._client_loop = fake_loop

    db_second = db_client.get_db()
    client_second = db_second.client

    assert client_first is not client_second
    assert db_client._client_loop is not fake_loop
