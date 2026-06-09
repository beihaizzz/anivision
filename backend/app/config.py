"""
AniVision Application Configuration

Uses pydantic-settings BaseSettings to load configuration from
environment variables and .env file. Provides type-safe access
to all application settings.
"""

from typing import List
import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str

    # ── JWT Authentication ────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── File Storage ──────────────────────────────────────────────────
    UPLOAD_DIR: str = "../data/uploads"
    GENERATED_DIR: str = "../data/generated"

    # ── AI Model ──────────────────────────────────────────────────────
    MODEL_PATH: str = "../ai_engine/models/efficientnet_b3.pth"
    LABEL_MAP_PATH: str = "../ai_engine/models/label_map.json"

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @classmethod
    def _parse_cors_origins(cls, value: str | List[str]) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or list."""
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return [origin.strip() for origin in value.split(",")]


# Singleton settings instance
settings = Settings()
