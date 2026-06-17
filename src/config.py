"""Central configuration loaded from environment variables.

All modules import settings from here so behaviour is consistent between the
ETL pipeline, the analytics layer and the Streamlit dashboard.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class DBConfig:
    host: str = _env("POSTGRES_HOST", "localhost")
    port: int = int(_env("POSTGRES_PORT", "5432"))
    database: str = _env("POSTGRES_DB", "growth_analytics")
    user: str = _env("POSTGRES_USER", "analytics")
    password: str = _env("POSTGRES_PASSWORD", "analytics")

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class AIConfig:
    provider: str = _env("AI_PROVIDER", "openai").lower()
    openai_api_key: str = _env("OPENAI_API_KEY")
    openai_model: str = _env("OPENAI_MODEL", "gpt-4o-mini")
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = _env("GEMINI_MODEL", "gemini-1.5-flash")

    @property
    def enabled(self) -> bool:
        if self.provider == "openai":
            return bool(self.openai_api_key)
        if self.provider == "gemini":
            return bool(self.gemini_api_key)
        return False


@dataclass(frozen=True)
class Paths:
    raw_data: Path = PROJECT_ROOT / _env("RAW_DATA_PATH", "data/raw/ecommerce_events.csv")
    processed_dir: Path = PROJECT_ROOT / _env("PROCESSED_DATA_DIR", "data/processed")
    models_dir: Path = PROJECT_ROOT / "models"

    def ensure(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    db: DBConfig = field(default_factory=DBConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    paths: Paths = field(default_factory=Paths)

    # Business rules
    churn_inactivity_days: int = 30
    repeat_purchase_window_days: int = 90


settings = Settings()
