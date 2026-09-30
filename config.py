"""
Application configuration.

All secrets are loaded from environment variables (optionally via a local
.env file during development). Nothing here ever hardcodes a real API key.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

# Load variables from a .env file if present. In production, real
# environment variables (e.g. set by the hosting platform) take precedence
# over .env, since load_dotenv() by default does not override existing vars.
load_dotenv()


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """Centralized, read-only application settings.

    All values are read from the environment inside __init__ (not as class
    attributes), so that a fresh Settings() instance always reflects the
    current environment -- this matters both for real deployments and for
    tests that use monkeypatch to change env vars between cases.
    """

    APP_NAME: str = "FinSimplify AI"

    def __init__(self) -> None:
        # --- External API credentials (secrets) ---
        self.NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "").strip()
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()

        # --- Model / provider configuration ---
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.GROQ_API_BASE: str = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1").strip()
        self.NEWSAPI_BASE_URL: str = os.getenv("NEWSAPI_BASE_URL", "https://newsapi.org/v2").strip()

        # --- App behavior ---
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip()
        self.HOST: str = os.getenv("HOST", "0.0.0.0").strip()
        self.PORT: int = int(os.getenv("PORT", "8000"))

        self.DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "12"))
        self.MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "50"))

        self.HTTP_TIMEOUT_SECONDS: float = float(os.getenv("HTTP_TIMEOUT_SECONDS", "12"))

        # Max length allowed for text fields sent to the summarizer, to bound
        # cost/latency and reduce prompt-injection surface area.
        self.MAX_SUMMARIZE_FIELD_LENGTH: int = int(os.getenv("MAX_SUMMARIZE_FIELD_LENGTH", "6000"))

        # CORS: disabled by default because the frontend is served by FastAPI
        # itself (same-origin). Set CORS_ALLOWED_ORIGINS as a comma-separated
        # list to enable cross-origin access from specific domains only.
        raw_cors = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
        self.CORS_ALLOWED_ORIGINS: List[str] = _split_csv(raw_cors) if raw_cors else []
        self.CORS_ENABLED: bool = bool(self.CORS_ALLOWED_ORIGINS)

    @property
    def newsapi_configured(self) -> bool:
        return bool(self.NEWSAPI_KEY)

    @property
    def groq_configured(self) -> bool:
        return bool(self.GROQ_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton for the app lifetime)."""
    return Settings()
