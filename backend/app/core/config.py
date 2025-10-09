"""Application settings and configuration helpers."""
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration loaded from env vars or `.env`."""

    project_name: str = "Congresscape API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = 10

    # pgvector settings
    vector_dimensions: int = Field(1536, description="Embedding vector size")

    # OpenAI / LLM provider
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4.1-mini"

    # CORS and client apps
    backend_cors_origins: List[AnyHttpUrl] = []

    # Feature flags
    enable_realtime: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance to avoid re-parsing env."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
