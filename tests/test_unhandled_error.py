import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter

# 1.9 RED: Assert unexpected exception returns structured 5xx with no stack trace or internal message leaked.

@pytest.mark.asyncio
async def test_unhandled_exception_returns_structured_500():
    from app.main import app

    test_router = APIRouter()

    @test_router.get("/api/test-crash")
    async def crash_endpoint():
        raise RuntimeError("super_secret_internal_database_password_12345 in /var/internal/path.py")

    app.include_router(test_router)

    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        response = await client.get("/api/test-crash")

    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "internal_error"
    assert data["message"] == "Error interno del servidor"
    assert "super_secret_internal_database_password_12345" not in response.text
    assert "/var/internal/path.py" not in response.text
