"""Application settings and configuration helpers."""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration loaded from env vars or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Congresscape API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = 10

    # Congress.gov / data.gov API key
    congress_api_key: str | None = Field(default=None, alias="CONGRESS_API_KEY")

    # CORS and client apps
    backend_cors_origins: List[AnyHttpUrl] = []

    # Feature flags
    enable_realtime: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance to avoid re-parsing env."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
