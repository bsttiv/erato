import logging
import pytest
from httpx import ASGITransport, AsyncClient
from app.core.security.tokens import mint_access_token
from app.db.client import get_db
from app.db.repositories.users import UsersRepository
from app.db.repositories.refresh_tokens import RefreshTokensRepository


@pytest.fixture(autouse=True)
async def clean_db():
    db = get_db()
    await db.users.drop()
    await db.refresh_tokens.drop()
    await UsersRepository(db).ensure_indexes()
    await RefreshTokensRepository(db).ensure_indexes()
    yield
    await db.users.drop()
    await db.refresh_tokens.drop()


@pytest.mark.asyncio
async def test_successful_registration():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "email": "banda@ejemplo.com",
            "password": "Password123!",
            "display_name": "Juani",
        }
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "banda@ejemplo.com"
        assert data["display_name"] == "Juani"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

        # Verify password is not in plaintext in the database
        db = get_db()
        user_doc = await db.users.find_one({"email": "banda@ejemplo.com"})
        assert user_doc is not None
        assert "Password123!" not in user_doc["password_hash"]
        assert user_doc["password_hash"].startswith("$argon2id$")


@pytest.mark.asyncio
async def test_duplicate_email_rejected():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "email": "banda@ejemplo.com",
            "password": "Password123!",
            "display_name": "Juani",
        }
        res1 = await client.post("/api/auth/register", json=payload)
        assert res1.status_code == 201

        # Attempt to register with the same email
        res2 = await client.post("/api/auth/register", json=payload)
        assert res2.status_code == 409
        data = res2.json()
        assert data["error"] == "conflict"


@pytest.mark.asyncio
async def test_malformed_email_and_weak_password_rejected():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid email
        res_email = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "ValidPassword123!",
            "display_name": "Juani",
        })
        assert res_email.status_code == 422
        assert res_email.json()["error"] == "validation_error"

        # Weak password (< 8 chars)
        res_weak = await client.post("/api/auth/register", json={
            "email": "valid@ejemplo.com",
            "password": "weak",
            "display_name": "Juani",
        })
        assert res_weak.status_code == 422
        assert res_weak.json()["error"] == "validation_error"


@pytest.mark.asyncio
async def test_successful_login_issues_jwt_and_refresh_cookie():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user first
        await client.post("/api/auth/register", json={
            "email": "banda@ejemplo.com",
            "password": "Password123!",
            "display_name": "Juani",
        })

        # Login
        login_res = await client.post("/api/auth/login", json={
            "email": "banda@ejemplo.com",
            "password": "Password123!",
        })
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "banda@ejemplo.com"

        # Check cookie
        assert "refresh_token" in login_res.cookies
        cookie_header = login_res.headers.get("set-cookie", "").lower()
        assert "httponly" in cookie_header
        assert "samesite=lax" in cookie_header
        assert "path=/api/auth" in cookie_header


@pytest.mark.asyncio
async def test_login_failure_is_generic():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/register", json={
            "email": "banda@ejemplo.com",
            "password": "Password123!",
            "display_name": "Juani",
        })

        # Wrong password
        res_wrong_pw = await client.post("/api/auth/login", json={
            "email": "banda@ejemplo.com",
            "password": "WrongPassword999!",
        })
        assert res_wrong_pw.status_code == 401
        data_wrong_pw = res_wrong_pw.json()
        assert data_wrong_pw["error"] == "unauthorized"

        # Non-existent user
        res_no_user = await client.post("/api/auth/login", json={
            "email": "nonexistent@ejemplo.com",
            "password": "AnyPassword123!",
        })
        assert res_no_user.status_code == 401
        data_no_user = res_no_user.json()
        assert data_no_user["error"] == "unauthorized"

        # Error messages must be generic and identical to prevent username enumeration
        assert data_wrong_pw["message"] == data_no_user["message"]


@pytest.mark.asyncio
async def test_protected_route_rejection_and_success():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and get access token
        reg_res = await client.post("/api/auth/register", json={
            "email": "banda@ejemplo.com",
            "password": "Password123!",
            "display_name": "Juani",
        })
        user_id = reg_res.json()["id"]

        login_res = await client.post("/api/auth/login", json={
            "email": "banda@ejemplo.com",
            "password": "Password123!",
        })
        valid_token = login_res.json()["access_token"]

        # Missing token -> 401
        res_missing = await client.get("/api/auth/me")
        assert res_missing.status_code == 401

        # Malformed token -> 401
        res_malformed = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert res_malformed.status_code == 401

        # Expired token -> 401
        expired_token = mint_access_token(user_id=user_id, token_version=1, ttl_minutes=-5)
        res_expired = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res_expired.status_code == 401

        # Valid token -> 200
        res_valid = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["email"] == "banda@ejemplo.com"


@pytest.mark.asyncio
async def test_plaintext_password_never_appears_in_logs(caplog):
    caplog.set_level(logging.DEBUG)
    secret_pass = "P@ssw0rdNeverLeakMe12345!"

    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        await client.post("/api/auth/register", json={
            "email": "logging_test@ejemplo.com",
            "password": secret_pass,
            "display_name": "Log Tester",
        })

        # Login
        await client.post("/api/auth/login", json={
            "email": "logging_test@ejemplo.com",
            "password": secret_pass,
        })

        # Failed login attempt
        await client.post("/api/auth/login", json={
            "email": "logging_test@ejemplo.com",
            "password": secret_pass + "_wrong",
        })

    # Assert secret never appears in any log entry
    assert secret_pass not in caplog.text
    assert secret_pass + "_wrong" not in caplog.text


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_logout():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register & login
        await client.post("/api/auth/register", json={
            "email": "rotation@ejemplo.com",
            "password": "Password123!",
            "display_name": "Rotation User",
        })
        login_res = await client.post("/api/auth/login", json={
            "email": "rotation@ejemplo.com",
            "password": "Password123!",
        })
        first_cookie = login_res.cookies.get("refresh_token")
        assert first_cookie is not None

        # Refresh
        client.cookies.set("refresh_token", first_cookie)
        refresh_res = await client.post("/api/auth/refresh")
        assert refresh_res.status_code == 200
        data = refresh_res.json()
        assert "access_token" in data

        second_cookie = refresh_res.cookies.get("refresh_token")
        assert second_cookie is not None
        assert second_cookie != first_cookie

        # Attempt to reuse first cookie -> triggers reuse detection -> 401
        client.cookies.set("refresh_token", first_cookie)
        reuse_res = await client.post("/api/auth/refresh")
        assert reuse_res.status_code == 401

        # The family has been invalidated, so second cookie must now also fail -> 401
        client.cookies.set("refresh_token", second_cookie)
        second_attempt_res = await client.post("/api/auth/refresh")
        assert second_attempt_res.status_code == 401

        # Re-login to test logout
        login2_res = await client.post("/api/auth/login", json={
            "email": "rotation@ejemplo.com",
            "password": "Password123!",
        })
        logout_res = await client.post("/api/auth/logout")
        assert logout_res.status_code == 200

        # After logout, refresh must fail
        refresh_after_logout = await client.post("/api/auth/refresh")
        assert refresh_after_logout.status_code == 401
