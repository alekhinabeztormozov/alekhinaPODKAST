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

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    admin_tg_ids: str = Field(default="", alias="ADMIN_TG_IDS")
    open_channel_id: str = Field(default="", alias="OPEN_CHANNEL_ID")
    closed_channel_id: str = Field(default="", alias="CLOSED_CHANNEL_ID")

    google_sa_json: str = Field(default="", alias="GOOGLE_SA_JSON")
    google_sheets_id: str = Field(default="", alias="GOOGLE_SHEETS_ID")

    notion_token: str = Field(default="", alias="NOTION_TOKEN")
    notion_db_episodes: str = Field(default="", alias="NOTION_DB_EPISODES")

    podster_rss_url: str = Field(default="", alias="PODSTER_RSS_URL")

    payment_provider_token: str = Field(default="", alias="PAYMENT_PROVIDER_TOKEN")
    payment_currency: str = Field(default="XTR", alias="PAYMENT_CURRENCY")

    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")
    use_redis: bool = Field(default=False, alias="USE_REDIS")

    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    ffprobe_bin: str = Field(default="ffprobe", alias="FFPROBE_BIN")

    subscription_price: int = Field(default=200, alias="SUBSCRIPTION_PRICE")
    subscription_days: int = Field(default=30, alias="SUBSCRIPTION_DAYS")
    trial_days: int = Field(default=1, alias="TRIAL_DAYS")

    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.admin_ids_raw]

    @property
    def admin_ids_raw(self) -> list[str]:
        return [p.strip() for p in self.admin_tg_ids.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
