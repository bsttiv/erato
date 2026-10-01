import pytest
from pydantic import ValidationError

# 1.3 RED: Assert missing required environment variable raises clear, structured error.

def test_missing_required_env_vars_fail(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("CLOUDINARY_API_SECRET", raising=False)

    from app.settings import Settings

    # Attempting to instantiate Settings without required env vars must fail fast
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    errors = exc_info.value.errors()
    missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
    assert "MONGODB_URI" in missing_fields or "mongodb_uri" in [str(f).lower() for f in missing_fields]
    assert "JWT_SECRET" in missing_fields or "jwt_secret" in [str(f).lower() for f in missing_fields]

def test_valid_settings_loaded(monkeypatch):
    test_env = {
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB": "erato_test",
        "JWT_SECRET": "supersecretkey12345678901234567890",
        "ACCESS_TOKEN_TTL_MINUTES": "15",
        "REFRESH_TOKEN_TTL_DAYS": "30",
        "INVITE_TOKEN_TTL_DAYS": "14",
        "CLOUDINARY_CLOUD_NAME": "erato-cloud",
        "CLOUDINARY_API_KEY": "123456789",
        "CLOUDINARY_API_SECRET": "abcdefsecret",
        "CLOUDINARY_FOLDER_PREFIX": "erato/dev",
        "APP_BASE_URL": "http://localhost:5173",
    }
    for k, v in test_env.items():
        monkeypatch.setenv(k, v)

    from app.settings import Settings
    settings = Settings(_env_file=None)

    assert settings.mongodb_uri == "mongodb://localhost:27017"
    assert settings.mongodb_db == "erato_test"
    assert settings.jwt_secret == "supersecretkey12345678901234567890"
    assert settings.access_token_ttl_minutes == 15
    assert settings.refresh_token_ttl_days == 30
    assert settings.invite_token_ttl_days == 14
    assert settings.cloudinary_cloud_name == "erato-cloud"
    assert settings.cloudinary_api_key == "123456789"
    assert settings.cloudinary_api_secret == "abcdefsecret"
    assert settings.cloudinary_folder_prefix == "erato/dev"
    assert settings.app_base_url == "http://localhost:5173"
