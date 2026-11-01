"""Only individually recoverable approved case IDs from decisions 07 and 15.

Original tests_md rows did not travel to this repository (decision 14).
No speculative mapping of the other AUTH/SES/USR/PERF IDs is made here.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import os

from argon2 import PasswordHasher
from bson import ObjectId
from fastapi.testclient import TestClient
import httpx
import jwt
import pytest

from app.main import create_app


@pytest.fixture
def maestro():
    with httpx.Client(base_url=os.environ["MAESTRO_URL"], timeout=2,
                      headers={"X-Api-Key": os.environ["MAESTRO_API_KEY"]}) as client:
        assert client.post("/__control/reset").status_code == 204
        yield client
        client.post("/__control/reset")


@pytest.fixture
def api(maestro):
    with TestClient(create_app(maestro_timeout=0.2)) as client:
        yield client


def register(api, username="alice", device="device"):
    response = api.post("/auth/register", headers={"X-Device-Id": device}, json={
        "username": username, "email": f"{username}@example.com",
        "display_name": username.title(), "password": "aaaaaaaa",
    })
    assert response.status_code == 201
    assert "refresh_token" not in response.json()
    return {**response.json(), "refresh_token": response.cookies["refresh_token"]}


def refresh_cookie(token):
    # The cookie is Secure, so the test client does not resend it over http.
    return {"X-Device-Id": "device", "Cookie": f"refresh_token={token}"}


def headers(tokens, device="device"):
    return {"Authorization": f'Bearer {tokens["access_token"]}', "X-Device-Id": device}


def decode(token):
    return jwt.decode(token, options={"verify_signature": False})


@pytest.mark.parametrize("mode", ["error_503", "no_response"])
def test_auth_027_mint_failure_leaves_no_session_or_attempts(api, db, maestro, mode):
    register(api)
    db.sessions.delete_many({})
    before = list(db.users.find())
    maestro.post("/__control/fault", json={"endpoint": "/mint", "mode": mode})
    response = api.post("/auth/login", headers={"X-Device-Id": "device"},
                        json={"email": "alice@example.com", "password": "aaaaaaaa"})
    assert response.status_code == 502
    assert response.json()["code"] == "session_upstream_error"
    assert list(db.users.find()) == before
    assert db.sessions.count_documents({}) == db.login_attempts.count_documents({}) == 0


def test_auth_028_existing_argon2id_hash_can_login(api, db):
    old_hash = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1).hash("aaaaaaaa")
    now = datetime.now(timezone.utc)
    user = {"_id": ObjectId(), "email": "old@example.com", "username": "old-user",
            "display_name": "Old User", "password_hash": old_hash,
            "created_at": now, "updated_at": now}
    db.users.insert_one(user)
    response = api.post("/auth/login", headers={"X-Device-Id": "device"},
                        json={"email": user["email"], "password": "aaaaaaaa"})
    assert response.status_code == 200
    assert db.users.find_one({"_id": user["_id"]})["password_hash"] == old_hash
    assert db.sessions.count_documents({"user_id": user["_id"]}) == 1


def test_ses_021_refresh_updates_same_session(api, db):
    tokens = register(api)
    old = db.sessions.find_one()
    response = api.post("/auth/refresh", headers=refresh_cookie(tokens["refresh_token"]))
    assert response.status_code == 200
    assert "refresh_token" not in response.json()
    new = {**response.json(), "refresh_token": response.cookies["refresh_token"]}
    session = db.sessions.find_one()
    assert db.sessions.count_documents({}) == 1
    assert session["_id"] == old["_id"] and session["created_at"] == old["created_at"]
    assert session["sid"] == old["sid"]
    assert session["refresh_token_hash"] == hashlib.sha256(new["refresh_token"].encode()).hexdigest()
    assert abs((session["expires_at"] - datetime.now(timezone.utc) - timedelta(days=7)).total_seconds()) < 5
    assert api.get("/me", headers=headers(new)).status_code == 200
    assert api.get("/me", headers=headers(tokens)).status_code == 200
    assert api.post("/auth/refresh", headers=refresh_cookie(tokens["refresh_token"])).status_code == 401


def test_ses_036_session_expiry_matches_refresh(api, db):
    tokens = register(api)
    session = db.sessions.find_one()
    assert session["expires_at"].timestamp() == decode(tokens["refresh_token"])["exp"]
    assert session["sid"] == decode(tokens["access_token"])["sid"]
    assert session["refresh_token_hash"] == hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    assert tokens["refresh_token"] not in repr(session)


def test_usr_024_no_private_fields_in_responses(api):
    tokens = register(api)
    auth = headers(tokens)
    responses = [tokens, api.get("/me", headers=auth).json(),
                 api.patch("/me", headers=auth, json={"display_name": "Alice New"}).json(),
                 api.patch("/me/email", headers=auth, json={"email": "new@example.com",
                           "current_password": "aaaaaaaa"}).json(),
                 api.get("/me/sessions", headers=auth).json()]
    for body in responses:
        assert "password_hash" not in str(body) and "refresh_token_hash" not in str(body)
    assert "email" not in str(tokens)
    assert set(responses[1]) == {"username", "display_name", "email"}
    assert "new@example.com" in str(responses[3])


def test_perf_010_update_returns_me_shape(api, db):
    tokens = register(api)
    response = api.patch("/me", headers=headers(tokens),
                         json={"username": "ALICE-NEW", "display_name": " Alice New "})
    assert response.status_code == 200
    assert response.json() == {"username": "alice-new", "display_name": "Alice New",
                               "email": "alice@example.com"}
    assert api.get("/me", headers=headers(tokens)).json() == response.json()
    user = db.users.find_one()
    assert user["username"] == "alice-new" and user["display_name"] == "Alice New"
    assert db.sessions.count_documents({}) == 1


def test_perf_030_session_list_includes_created_at(api, db):
    tokens = register(api)
    response = api.get("/me/sessions", headers=headers(tokens))
    assert response.status_code == 200
    assert len(response.json()) == 1
    item = response.json()[0]
    assert set(item) == {"id", "device", "last_access_at", "created_at", "current"}
    assert item["current"] is True
    session = db.sessions.find_one()
    assert item["id"] == str(session["_id"])
    assert datetime.fromisoformat(item["created_at"]) == session["created_at"]
