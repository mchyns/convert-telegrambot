import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "DocPDF Bot"
    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./docpdf.db",
        description="Async SQLAlchemy database URL (PostgreSQL or SQLite)"
    )

    # Queue & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS_QUEUE: bool = False  # Default to false for standalone local testing, true in production docker

    # File & Processing Limits
    MAX_FILE_SIZE_MB: int = 25
    MAX_CONCURRENT_JOBS: int = 3
    JOB_TIMEOUT_SECONDS: int = 120
    MAX_QUEUE_SIZE: int = 100
    MAX_JOBS_PER_USER_PER_HOUR: int = 30

    # Storage & Temporary Files
    TEMP_DIR: str = "./tmp/docpdf"
    FILE_TTL_MINUTES: int = 30
    CLEANUP_INTERVAL_MINUTES: int = 15

    # Logging
    LOG_LEVEL: str = "INFO"

    # Admin Telegram IDs (comma-separated integers string e.g. "12345,67890")
    ADMIN_TELEGRAM_IDS: str = ""

    # Converter paths
    LIBREOFFICE_PATH: Optional[str] = None

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        ids = []
        for item in self.ADMIN_TELEGRAM_IDS.split(","):
            cleaned = item.strip()
            if cleaned.isdigit():
                ids.append(int(cleaned))
        return ids

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def temp_path(self) -> Path:
        p = Path(self.TEMP_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
