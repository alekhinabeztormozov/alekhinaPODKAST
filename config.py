"""Central config. Loads secrets from .env via pydantic-settings.

Никаких секретов в коде — только имена переменных. Реальные значения в .env
(в .gitignore). См. PROJECT.md р.10.1.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram bot ---
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    admin_tg_ids: str = Field(default="", alias="ADMIN_TG_IDS")  # csv
    open_channel_id: str = Field(default="", alias="OPEN_CHANNEL_ID")
    closed_channel_id: str = Field(default="", alias="CLOSED_CHANNEL_ID")

    # --- Google Sheets ---
    google_sa_json: str = Field(default="", alias="GOOGLE_SA_JSON")
    google_sheets_id: str = Field(default="", alias="GOOGLE_SHEETS_ID")

    # --- Notion ---
    notion_token: str = Field(default="", alias="NOTION_TOKEN")
    notion_db_episodes: str = Field(default="", alias="NOTION_DB_EPISODES")

    # --- Podster / RSS ---
    podster_rss_url: str = Field(default="", alias="PODSTER_RSS_URL")

    # --- Payments (Telegram-native: Stars или ЮKassa provider token) ---
    payment_provider_token: str = Field(default="", alias="PAYMENT_PROVIDER_TOKEN")

    # --- storage ---
    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # --- media / paths ---
    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    ffprobe_bin: str = Field(default="ffprobe", alias="FFPROBE_BIN")

    @property
    def admin_ids(self) -> list[int]:
        """Parsed whitelist of admin Telegram IDs."""
        return [int(x) for x in self.admin_ids_raw]

    @property
    def admin_ids_raw(self) -> list[str]:
        return [p.strip() for p in self.admin_tg_ids.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
