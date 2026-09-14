"""
Central application settings.

All values are placeholders for architecture (Phase 0). Real credentials
and production thresholds must never be committed here; they arrive via
environment variables / secret store at deploy time.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_ENV: str = Field(default="Development")
    API_KEY: str = Field(default="dev-local-key")
    LOG_LEVEL: str = Field(default="INFO")

    # --- AWS / S3 ---
    AWS_REGION: str = Field(default="ap-south-1")
    S3_BUCKET: str = Field(default="")
    S3_ALLOWED_PREFIX: str = Field(default="org/")
    S3_MAX_OBJECT_MB: int = Field(default=15)
    S3_ALLOWED_CONTENT_TYPES: List[str] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )

    # --- OCR ---
    OCR_MAX_PAGES: int = Field(default=10)
    OCR_LANG: str = Field(default="eng")
    TESSERACT_CMD: str = Field(default="")

    # --- Pricing model ---
    MODEL_DIR: str = Field(default="./app/models/price-model-dev")
    MODEL_VERSION: str = Field(default="price-model-dev")
    ANOMALY_LOW_MAX: int = Field(default=30)
    ANOMALY_MEDIUM_MAX: int = Field(default=70)

    # --- Networking ---
    REQUEST_TIMEOUT_SECONDS: int = Field(default=60)


@lru_cache
def get_settings() -> Settings:
    """Settings are cached: read once per process, not once per request."""
    return Settings()
