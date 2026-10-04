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
    assert settings.build_app_url("/invite/abc") == "http://localhost:5173/invite/abc"


def test_app_base_url_unset_fails_closed_with_configuration_error(monkeypatch):
    test_env = {
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB": "erato_test",
        "JWT_SECRET": "supersecretkey12345678901234567890",
        "CLOUDINARY_CLOUD_NAME": "erato-cloud",
        "CLOUDINARY_API_KEY": "123456789",
        "CLOUDINARY_API_SECRET": "abcdefsecret",
    }
    for k, v in test_env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("APP_BASE_URL", raising=False)

    from app.core.errors import ConfigurationError
    from app.settings import Settings, build_app_url

    settings = Settings(_env_file=None)
    assert settings.app_base_url is None

    # Calling build_app_url on settings without app_base_url must fail closed
    with pytest.raises(ConfigurationError) as exc_info:
        settings.build_app_url("/invite/x")
    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "config_missing"
    assert "APP_BASE_URL" in exc_info.value.message

    # Module-level helper build_app_url must also raise ConfigurationError
    with pytest.raises(ConfigurationError) as exc_info2:
        build_app_url("/invite/x", settings=settings)
    assert exc_info2.value.status_code == 500
    assert exc_info2.value.code == "config_missing"
    assert "APP_BASE_URL" in exc_info2.value.message


def test_build_app_url_never_derives_from_request_host(monkeypatch):
    """URL generation must fail closed if APP_BASE_URL is unset, never falling back to host headers."""
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    from app.core.errors import ConfigurationError
    from app.settings import Settings, build_app_url

    settings = Settings(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017",
        jwt_secret="supersecretkey12345678901234567890",
        cloudinary_cloud_name="erato-cloud",
        cloudinary_api_key="123",
        cloudinary_api_secret="abc",
    )
    assert settings.app_base_url is None

    # Even if an external caller or request host is simulated, build_app_url refuses to generate
    with pytest.raises(ConfigurationError) as exc_info:
        build_app_url("/invite/token-123", settings=settings)
    assert exc_info.value.code == "config_missing"
    assert "APP_BASE_URL" in exc_info.value.message

