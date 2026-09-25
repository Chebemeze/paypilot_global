"""
PayPilot Global — Configuration
Loads environment variables and exposes typed settings.
"""
from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_env: str = Field(default="demo", alias="APP_ENV")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    database_url: str = Field(
        default="sqlite:///./paypilot.db", alias="DATABASE_URL"
    )

    bmoni_base_url: str = Field(
        default="https://embedded-dev.bmoni.com", alias="BMONI_BASE_URL"
    )
    bmoni_api_key: str = Field(default="", alias="BMONI_API_KEY")
    bmoni_webhook_secret: str = Field(default="", alias="BMONI_WEBHOOK_SECRET")

    flutterwave_base_url: str = Field(
        default="https://api.flutterwave.com/v3", alias="FLUTTERWAVE_BASE_URL"
    )
    flutterwave_secret_key: str = Field(default="", alias="FLUTTERWAVE_SECRET_KEY")
    flutterwave_public_key: str = Field(default="", alias="FLUTTERWAVE_PUBLIC_KEY")
    flutterwave_webhook_secret: str = Field(default="", alias="FLUTTERWAVE_WEBHOOK_SECRET")

    redis_url: str = Field(default="", alias="REDIS_URL")

    jwt_secret: str = Field(default="dev-secret", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")

    demo_employer_id: str = Field(
        default="demo-employer-001", alias="DEMO_EMPLOYER_ID"
    )

    csv_max_rows: int = Field(default=5000, alias="CSV_MAX_ROWS")
    csv_max_size_mb: int = Field(default=5, alias="CSV_MAX_SIZE_MB")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
