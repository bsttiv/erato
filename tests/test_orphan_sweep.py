from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from app.routers.maintenance import filter_orphan_assets_for_sweep


def test_orphan_sweep_filter_logic():
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Asset tagged 'pending' and 25 hours old -> MUST be swept
    old_pending = {
        "public_id": "erato/compositions/c1/old_orphan",
        "created_at": (now - timedelta(hours=25)).isoformat(),
        "tags": ["pending"],
    }

    # 2. Asset tagged 'pending' and only 2 hours old -> MUST NOT be swept
    young_pending = {
        "public_id": "erato/compositions/c1/young_pending",
        "created_at": (now - timedelta(hours=2)).isoformat(),
        "tags": ["pending"],
    }

    # 3. Confirmed asset (without 'pending' tag), even if 30 days old -> MUST NOT be swept
    old_confirmed = {
        "public_id": "erato/compositions/c1/confirmed_take",
        "created_at": (now - timedelta(days=30)).isoformat(),
        "tags": [],
    }

    assets = [old_pending, young_pending, old_confirmed]
    to_delete = filter_orphan_assets_for_sweep(assets, now=now, max_age_hours=24)

    assert to_delete == ["erato/compositions/c1/old_orphan"]
    assert "erato/compositions/c1/young_pending" not in to_delete
    assert "erato/compositions/c1/confirmed_take" not in to_delete


@pytest.mark.asyncio
async def test_orphan_sweep_endpoint_guard(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "my_cron_secret_123")
    from app.settings import get_settings
    get_settings.cache_clear()

    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Request without header -> 401
        res_unauth = await client.get("/api/cron/orphan-sweep")
        assert res_unauth.status_code == 401

        # Request with wrong secret -> 401
        res_wrong = await client.get(
            "/api/cron/orphan-sweep",
            headers={"Authorization": "Bearer wrong_secret"},
        )
        assert res_wrong.status_code == 401

        # Any client can send x-vercel-cron, so it never authorizes on its own -> 401
        with patch("app.routers.maintenance.execute_orphan_sweep", return_value=[]) as sweep:
            res_cron_header = await client.get(
                "/api/cron/orphan-sweep",
                headers={"x-vercel-cron": "1"},
            )
            assert res_cron_header.status_code == 401
            sweep.assert_not_called()

        # Request with correct secret -> 200
        with patch("app.routers.maintenance.execute_orphan_sweep", return_value=["erato/c1/orphan"]):
            res_auth = await client.get(
                "/api/cron/orphan-sweep",
                headers={"Authorization": "Bearer my_cron_secret_123"},
            )
            assert res_auth.status_code == 200
            assert "deleted_count" in res_auth.json() or "deleted" in res_auth.json()


@pytest.mark.asyncio
async def test_orphan_sweep_endpoint_guard_no_secret(monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)
    from app.settings import get_settings
    get_settings.cache_clear()

    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Request without header -> 401
        res_unauth = await client.get("/api/cron/orphan-sweep")
        assert res_unauth.status_code == 401

        # Request with arbitrary Bearer when no secret configured -> 401
        res_bearer = await client.get(
            "/api/cron/orphan-sweep",
            headers={"Authorization": "Bearer some_token"},
        )
        assert res_bearer.status_code == 401

        # Without CRON_SECRET the endpoint stays closed, even with x-vercel-cron -> 401
        with patch("app.routers.maintenance.execute_orphan_sweep", return_value=[]) as sweep:
            res_cron = await client.get(
                "/api/cron/orphan-sweep",
                headers={"x-vercel-cron": "1"},
            )
            assert res_cron.status_code == 401
            sweep.assert_not_called()
