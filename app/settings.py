from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.errors import ConfigurationError



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # Blank values (`KEY=` in .env, empty variable in the host panel) count as unset.
        env_ignore_empty=True,
        # Validation errors must not echo the received environment (secrets) into logs.
        hide_input_in_errors=True,
    )

    # Database
    mongodb_uri: str
    mongodb_db: str = "erato"

    # Authentication & Tokens
    jwt_secret: str
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    invite_token_ttl_days: int = 14

    # Cloudinary Media Storage
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_folder_prefix: str = "erato"

    # Application Base URL (fail-closed, must be explicitly set)
    app_base_url: Optional[str] = None

    # Maintenance Cron
    cron_secret: Optional[str] = None

    def build_app_url(self, path: str) -> str:
        """Construct an absolute application URL, failing closed if APP_BASE_URL is not set."""
        if not self.app_base_url:
            raise ConfigurationError(
                message="La variable de entorno APP_BASE_URL no está configurada",
                code="config_missing",
            )
        base = self.app_base_url.rstrip("/")
        clean_path = path.lstrip("/")
        return f"{base}/{clean_path}" if clean_path else base



@lru_cache
def get_settings() -> Settings:
    return Settings()


def build_app_url(path: str, settings: Optional[Settings] = None) -> str:
    """Construct an absolute application URL using the active or provided settings."""
    target_settings = settings or get_settings()
    return target_settings.build_app_url(path)

