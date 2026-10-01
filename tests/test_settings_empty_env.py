import pytest
from pydantic import ValidationError

from app.settings import Settings


def load_settings() -> Settings:
    # _env_file=None: results must not depend on a developer's local .env file.
    return Settings(_env_file=None)


def test_empty_optional_values_fall_back_to_their_defaults(monkeypatch):
    # A blank `KEY=` line in .env or an empty variable in the hosting panel must not crash the app.
    monkeypatch.setenv("ACCESS_TOKEN_TTL_MINUTES", "")
    monkeypatch.setenv("REFRESH_TOKEN_TTL_DAYS", "")
    monkeypatch.setenv("INVITE_TOKEN_TTL_DAYS", "")
    monkeypatch.setenv("CLOUDINARY_FOLDER_PREFIX", "")

    settings = load_settings()

    assert settings.access_token_ttl_minutes == 15
    assert settings.refresh_token_ttl_days == 30
    assert settings.invite_token_ttl_days == 14
    assert settings.cloudinary_folder_prefix == "erato"


def test_an_empty_required_secret_is_rejected_as_missing(monkeypatch):
    # An empty JWT secret must never be accepted silently.
    monkeypatch.setenv("JWT_SECRET", "")

    with pytest.raises(ValidationError) as error:
        load_settings()

    assert "jwt_secret" in str(error.value)


def test_real_values_still_override_the_defaults(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_TTL_MINUTES", "5")

    assert load_settings().access_token_ttl_minutes == 5
