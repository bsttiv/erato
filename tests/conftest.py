import pytest
from app.settings import get_settings


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    import os
    default_uri = "mongodb://erato_admin:erato_password@localhost:27017/erato_test?authSource=admin"
    monkeypatch.setenv("MONGODB_URI", os.getenv("TEST_MONGODB_URI", default_uri))
    monkeypatch.setenv("MONGODB_DB", "erato_test")

    monkeypatch.setenv("JWT_SECRET", "test_jwt_secret_key_at_least_32_bytes_long_12345")
    monkeypatch.setenv("ACCESS_TOKEN_TTL_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_TTL_DAYS", "30")
    monkeypatch.setenv("INVITE_TOKEN_TTL_DAYS", "14")
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "test-api-key")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "test-api-secret")
    monkeypatch.setenv("CLOUDINARY_FOLDER_PREFIX", "erato/test")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:5173")

    get_settings.cache_clear()
    from app.main import app
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    get_settings.cache_clear()

