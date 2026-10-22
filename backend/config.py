"""
Application configuration for UtsavAI via pydantic-settings.
Reads from environment variables / .env file.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: str = Field(default="http://localhost:8000,http://127.0.0.1:8000")
    cors_origin_regex: str = Field(default=r"^https://.*\.vercel\.app$")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── AI Provider ───────────────────────────────────────────
    ai_provider: str = Field(default="none")  # gemini | openai | anthropic | none

    # API keys & model identifiers — never log keys
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-3.8-flash")
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit_rpm: int = Field(default=30)

    # ── LLM Cache ─────────────────────────────────────────────
    llm_cache_size: int = Field(default=128)
    llm_timeout_seconds: int = Field(default=30)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


__all__ = ["Settings", "get_settings"]
