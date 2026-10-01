from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient

# 1.1 RED: Assert GET /api/health returns 200 with structured JSON body and performs no database round trip.

@pytest.mark.asyncio
async def test_health_endpoint():
    with patch("app.db.client.get_db") as mock_get_db:
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        # Assert Mongo client is never invoked
        mock_get_db.assert_not_called()
