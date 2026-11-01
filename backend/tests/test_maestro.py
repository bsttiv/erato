"""Approved MAE cases: tests_md/propuesta-maestro-real-2026-11-01.md."""
import hashlib
import os
import time

from app.database import create_indexes
from app.main import create_app
from fastapi.testclient import TestClient
import httpx
import jwt
import pytest

from test_accounts import api, decode, headers, maestro, refresh_cookie, register

ROUTES = ("/mint", "/validate", "/refresh", "/revoke")
LOGIN = {"email": "alice@example.com", "password": "aaaaaaaa"}


def pair(client, fingerprint="device"):
    response = client.post("/mint", json={"userId": "alice", "context": fingerprint})
    assert response.status_code == 200
    return response.json()


def validate(client, token, fingerprint="device"):
    return client.post("/validate", json={"token": token, "fingerprint": fingerprint})


def rotate(client, token, fingerprint="device"):
    return client.post("/refresh", json={"refresh": token, "fingerprint": fingerprint})


def fault(client, endpoint, mode, body=None):
    payload = {"endpoint": endpoint, "mode": mode}
    if mode == "body":
        payload["body"] = body
    assert client.post("/__control/fault", json=payload).status_code == 204


def calls(client):
    return client.get("/__control/calls").json()


def login(api, device="device"):
    response = api.post("/auth/login", headers={"X-Device-Id": device}, json=LOGIN)
    assert response.status_code == 200
    return {**response.json(), "refresh_token": response.cookies["refresh_token"]}


def signed(**claims):
    return jwt.encode(claims, "k" * 32, algorithm="HS256")


@pytest.mark.parametrize("route", ROUTES)
def test_mae_001_missing_api_key(route):
    response = httpx.post(os.environ["MAESTRO_URL"] + route, json={})
    assert response.status_code == 401 and response.text == "Missing API Key"


@pytest.mark.parametrize("route", ROUTES)
def test_mae_002_wrong_api_key(route):
    response = httpx.post(os.environ["MAESTRO_URL"] + route, json={},
                          headers={"X-Api-Key": "wrong"})
    assert response.status_code == 401 and response.text == "Invalid API Key"


def test_mae_003_mint_claims(maestro):
    tokens = pair(maestro)
    access, refresh = decode(tokens["accessToken"]), decode(tokens["refreshToken"])
    assert set(access) == {"typ", "iss", "sub", "sid", "ctx", "iat", "exp"}
    assert set(refresh) == set(access) | {"jti"}
    assert access["typ"] == "access" and refresh["typ"] == "refresh"
    assert access["sub"] == refresh["sub"] == "sub_alice"
    assert access["sid"] == refresh["sid"]
    assert access["ctx"] != "device" and refresh["ctx"] != "device"
    assert access["exp"] - time.time() == pytest.approx(900, abs=5)
    assert refresh["exp"] - time.time() == pytest.approx(604800, abs=5)


def test_mae_004_validate_returns_the_session(maestro):
    token = pair(maestro)["accessToken"]
    response = validate(maestro, token)
    assert response.status_code == 200
    assert response.json() == {"userId": "alice", "sessionId": decode(token)["sid"]}


@pytest.mark.parametrize("case", ["malformed", "expired", "revoked", "refresh", "fingerprint"])
def test_mae_005_invalid_tokens_answer_401(maestro, case):
    tokens = pair(maestro)
    token, fingerprint = tokens["accessToken"], "device"
    if case == "malformed":
        token = "invalid"
    elif case == "expired":
        assert maestro.post("/__control/expire", json={"token": token}).status_code == 204
    elif case == "revoked":
        assert maestro.post("/revoke", json={"token": token}).status_code == 204
    elif case == "refresh":
        token = tokens["refreshToken"]
    else:
        fingerprint = "other-device"
    response = validate(maestro, token, fingerprint)
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("text/plain")


def test_mae_006_refresh_rotates_within_the_session(maestro):
    old = pair(maestro)
    response = rotate(maestro, old["refreshToken"])
    assert response.status_code == 200
    new = response.json()
    before, after = decode(old["refreshToken"]), decode(new["refreshToken"])
    assert after["sid"] == before["sid"] == decode(new["accessToken"])["sid"]
    assert after["jti"] != before["jti"]
    assert after["exp"] == before["exp"]
    assert validate(maestro, new["accessToken"]).status_code == 200
    assert validate(maestro, old["accessToken"]).status_code == 200


def test_mae_007_refresh_reuse_ends_the_session(maestro):
    old = pair(maestro)
    new = rotate(maestro, old["refreshToken"]).json()
    assert rotate(maestro, old["refreshToken"]).status_code == 401
    assert validate(maestro, new["accessToken"]).status_code == 401
    assert rotate(maestro, new["refreshToken"]).status_code == 401


def test_mae_008_refresh_from_another_device_ends_the_session(maestro):
    tokens = pair(maestro)
    assert rotate(maestro, tokens["refreshToken"], "other-device").status_code == 401
    assert validate(maestro, tokens["accessToken"]).status_code == 401
    assert rotate(maestro, tokens["refreshToken"]).status_code == 401


@pytest.mark.parametrize("name", ["accessToken", "refreshToken"])
def test_mae_009_revoke_with_either_token(maestro, name):
    tokens = pair(maestro)
    assert maestro.post("/revoke", json={"token": tokens[name]}).status_code == 204
    assert validate(maestro, tokens["accessToken"]).status_code == 401
    assert rotate(maestro, tokens["refreshToken"]).status_code == 401


def test_mae_010_revoke_rejects_invalid_token(maestro):
    assert maestro.post("/revoke", json={"token": "invalid"}).status_code == 401


@pytest.mark.parametrize("route, body", [
    ("/revoke", {"jti": "x"}), ("/refresh", {"refreshToken": "x", "fingerprint": "device"}),
])
def test_mae_011_old_bodies_are_rejected(maestro, route, body):
    assert maestro.post(route, json=body).status_code == 400


def test_mae_012_forced_faults(maestro):
    fault(maestro, "/mint", "error_503")
    assert maestro.post("/mint", json={"userId": "alice", "context": "device"}).status_code == 503
    fault(maestro, "/mint", "no_response")
    with pytest.raises(httpx.TimeoutException):
        maestro.post("/mint", json={"userId": "alice", "context": "device"})


def test_mae_020_every_call_carries_the_api_key(api, maestro):
    key = os.environ["MAESTRO_API_KEY"]
    tokens = register(api)
    responses = [api.get("/me", headers=headers(tokens)),
                 api.post("/auth/refresh", headers=refresh_cookie(tokens["refresh_token"]))]
    new = responses[-1].json()
    responses.append(api.post("/auth/logout", headers=headers(new)))
    # The mock logs a call only after admitting its key.
    assert {call["path"] for call in calls(maestro)} == set(ROUTES)
    assert all(key not in response.text for response in responses)


def test_mae_021_missing_api_key_stops_startup(monkeypatch):
    value = os.environ["MAESTRO_API_KEY"]
    monkeypatch.delenv("MAESTRO_API_KEY")
    with pytest.raises(ValueError, match="MAESTRO_API_KEY") as error:
        create_app()
    assert value not in str(error.value)


def test_mae_022_rejected_token_is_not_authenticated(api, maestro):
    tokens = register(api)
    assert maestro.post("/revoke", json={"token": tokens["access_token"]}).status_code == 204
    response = api.get("/me", headers=headers(tokens))
    assert response.status_code == 401 and response.json()["code"] == "not_authenticated"


@pytest.mark.parametrize("mode", ["error_429", "error_503"])
def test_mae_023_upstream_failure_on_validate(api, maestro, mode):
    tokens = register(api)
    fault(maestro, "/validate", mode)
    response = api.get("/me", headers=headers(tokens))
    assert response.status_code == 502 and response.json()["code"] == "session_upstream_error"


@pytest.mark.parametrize("body", [
    {}, [], {"userId": "x"}, {"sessionId": "x"}, {"userId": None, "sessionId": "x"},
    {"userId": "x", "sessionId": ""},
])
def test_mae_024_malformed_validate_response(api, maestro, body):
    tokens = register(api)
    fault(maestro, "/validate", "body", body)
    response = api.get("/me", headers=headers(tokens))
    assert response.status_code == 502 and response.json()["code"] == "session_upstream_error"


def test_mae_025_session_stores_the_sid(api, db):
    register(api)
    db.sessions.delete_many({})
    tokens = login(api)
    session = db.sessions.find_one()
    assert session["sid"] == decode(tokens["access_token"])["sid"]
    assert "jti" not in session
    assert session["expires_at"].timestamp() == decode(tokens["refresh_token"])["exp"]


@pytest.mark.parametrize("access, refresh", [
    ({"sid": "a"}, {"sid": "b"}), ({}, {"sid": "a"}), ({"sid": "a"}, {}),
    ({"sid": "a", "sub": "sub_other"}, {"sid": "a", "sub": "sub_other"}),
])
def test_mae_026_issued_pair_is_checked(api, db, maestro, access, refresh):
    register(api)
    user_id = db.users.find_one()["_id"]
    db.sessions.delete_many({})
    common = {"sub": f"sub_{user_id}", "exp": int(time.time()) + 60}
    fault(maestro, "/mint", "body", {
        "accessToken": signed(**{**common, "typ": "access", **access}),
        "refreshToken": signed(**{**common, "typ": "refresh", "jti": "j", **refresh}),
    })
    response = api.post("/auth/login", headers={"X-Device-Id": "device"}, json=LOGIN)
    assert response.status_code == 502 and response.json()["code"] == "session_upstream_error"
    assert db.sessions.count_documents({}) == 0


def test_mae_027_session_comes_from_validate(api, db, maestro):
    first = register(api)
    second = login(api, "other-device")
    user_id = str(db.users.find_one()["_id"])
    target = decode(second["access_token"])["sid"]
    fault(maestro, "/validate", "body", {"userId": user_id, "sessionId": target})
    sessions = api.get("/me/sessions", headers=headers(first)).json()
    current = [item["id"] for item in sessions if item["current"]]
    assert current == [str(db.sessions.find_one({"sid": target})["_id"])]


def test_mae_028_refresh_keeps_the_session(api, db, maestro):
    tokens = register(api)
    old = db.sessions.find_one()
    response = api.post("/auth/refresh", headers=refresh_cookie(tokens["refresh_token"]))
    assert response.status_code == 200
    assert calls(maestro)[-1] == {"path": "/refresh", "body": {
        "refresh": tokens["refresh_token"], "fingerprint": "device"}}
    session = db.sessions.find_one()
    assert session["sid"] == old["sid"]
    assert session["expires_at"] == old["expires_at"]
    assert session["refresh_token_hash"] == hashlib.sha256(
        response.cookies["refresh_token"].encode()).hexdigest()


def test_mae_029_logout_revokes_with_the_access_token(api, db, maestro):
    tokens = register(api)
    response = api.post("/auth/logout", headers=headers(tokens))
    assert response.status_code == 204 and response.content == b""
    assert calls(maestro)[-1] == {"path": "/revoke", "body": {"token": tokens["access_token"]}}
    assert db.sessions.count_documents({}) == 0
    assert 'refresh_token=""' in response.headers["set-cookie"]
    assert api.get("/me", headers=headers(tokens)).status_code == 401
    assert api.post("/auth/refresh", headers=refresh_cookie(tokens["refresh_token"])).status_code == 401


def test_mae_030_logout_keeps_the_row_on_upstream_failure(api, db, maestro):
    tokens = register(api)
    fault(maestro, "/revoke", "error_503")
    response = api.post("/auth/logout", headers=headers(tokens))
    assert response.status_code == 502 and response.json()["code"] == "session_upstream_error"
    assert db.sessions.count_documents({}) == 1


def test_mae_031_other_device_closes_locally(api, db, maestro):
    first = register(api)
    second = login(api, "other-device")
    row = db.sessions.find_one({"sid": decode(second["access_token"])["sid"]})
    response = api.delete(f'/me/sessions/{row["_id"]}', headers=headers(first))
    assert response.status_code == 204
    assert "/revoke" not in [call["path"] for call in calls(maestro)]
    assert db.sessions.find_one({"_id": row["_id"]}) is None
    assert api.get("/me", headers=headers(second, "other-device")).status_code == 401
    refreshed = api.post("/auth/refresh", headers={
        **refresh_cookie(second["refresh_token"]), "X-Device-Id": "other-device"})
    assert refreshed.status_code == 401


def test_mae_032_current_session_revokes_in_maestro(api, db, maestro):
    tokens = register(api)
    row = db.sessions.find_one()
    response = api.delete(f'/me/sessions/{row["_id"]}', headers=headers(tokens))
    assert response.status_code == 204
    assert calls(maestro)[-1] == {"path": "/revoke", "body": {"token": tokens["access_token"]}}
    assert db.sessions.count_documents({}) == 0


def test_mae_033_password_change_closes_other_devices(api, db, maestro):
    first = register(api)
    second = login(api, "other-device")
    before = db.users.find_one()["password_hash"]
    response = api.patch("/me/password", headers=headers(first), json={
        "current_password": "aaaaaaaa", "new_password": "bbbbbbbb"})
    assert response.status_code == 204
    assert "/revoke" not in [call["path"] for call in calls(maestro)]
    assert api.get("/me", headers=headers(second, "other-device")).status_code == 401
    assert api.get("/me", headers=headers(first)).status_code == 200
    assert db.sessions.count_documents({}) == 1
    assert db.users.find_one()["password_hash"] != before


def test_mae_034_only_the_requesting_session_is_current(api, db):
    first = register(api)
    login(api, "other-device")
    sessions = api.get("/me/sessions", headers=headers(first)).json()
    own = db.sessions.find_one({"sid": decode(first["access_token"])["sid"]})
    assert len(sessions) == 2
    assert [item["id"] for item in sessions if item["current"]] == [str(own["_id"])]


def test_mae_040_session_indexes(db):
    indexes = db.sessions.index_information()
    assert indexes["sid_1"]["unique"] is True
    assert "jti_1" not in indexes


def test_mae_041_old_index_is_removed(db):
    db.sessions.create_index("jti", unique=True)
    create_indexes(db)
    create_indexes(db)
    indexes = db.sessions.index_information()
    assert "jti_1" not in indexes and indexes["sid_1"]["unique"] is True
    db.sessions.insert_many([{"sid": "a"}, {"sid": "b"}])
    assert db.sessions.count_documents({}) == 2


def test_mae_042_rows_without_sid_are_deleted(db):
    db.sessions.drop_index("sid_1")
    db.sessions.insert_many([{"jti": "a"}, {"jti": "b"}, {"sid": "current"}])
    create_indexes(db)
    assert [row["sid"] for row in db.sessions.find()] == ["current"]
    assert db.sessions.index_information()["sid_1"]["unique"] is True


def test_mae_043_index_already_removed_by_another_instance(db, monkeypatch):
    db.sessions.create_index("jti", unique=True)
    real = db.sessions.index_information()
    db.sessions.drop_index("jti_1")
    # The other instance drops it between this instance's check and its own drop.
    monkeypatch.setattr(type(db.sessions), "index_information", lambda self: real)
    create_indexes(db)
    monkeypatch.undo()
    assert "jti_1" not in db.sessions.index_information()


def test_mae_046_rejected_api_key_is_an_upstream_error(api, db, monkeypatch):
    tokens = register(api)
    before = db.sessions.find_one()
    monkeypatch.setenv("MAESTRO_API_KEY", "wrong")
    with TestClient(create_app(maestro_timeout=0.2)) as misconfigured:
        responses = [misconfigured.get("/me", headers=headers(tokens)),
                     misconfigured.post("/auth/refresh",
                                        headers=refresh_cookie(tokens["refresh_token"]))]
    for response in responses:
        assert response.status_code == 502
        assert response.json()["code"] == "session_upstream_error"
    assert db.sessions.find_one() == before


def test_mae_047_vercel_entrypoint_serves_the_api_prefix():
    from app.asgi import app

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        response = client.post("/api/auth/login", headers={"X-Device-Id": "device"}, json={})
    assert response.status_code == 422 and response.json()["code"] == "validation_error"
