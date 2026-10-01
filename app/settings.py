from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict



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

    # Application Base URL
    app_base_url: str = "http://localhost:5173"

    # Maintenance Cron
    cron_secret: Optional[str] = None



@lru_cache
def get_settings() -> Settings:
    return Settings()
