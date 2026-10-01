import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter
from pymongo.errors import ServerSelectionTimeoutError

# 1.13 RED: Assert simulated connection failure surfaces as structured 5xx without leaking raw PyMongo exception.

@pytest.mark.asyncio
async def test_mongo_connection_failure_surfaces_as_structured_5xx():
    from app.main import app

    test_router = APIRouter()

    @test_router.get("/api/test-db-failure")
    async def failing_db_endpoint():
        raise ServerSelectionTimeoutError("No servers found yet: localhost:27017 connection refused cluster details host info")

    app.include_router(test_router)

    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        response = await client.get("/api/test-db-failure")

    assert response.status_code == 503
    data = response.json()
    assert data.get("error") == "database_unavailable"
    assert data.get("message") == "Servicio de base de datos no disponible temporalmente"
    # Verify no raw exception details leaked
    assert "No servers found yet" not in response.text
    assert "localhost:27017" not in response.text
    assert "connection refused" not in response.text
