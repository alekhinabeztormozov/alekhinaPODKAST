from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: str = ""
    telegram_proxy: str = ""
    admin_tg_ids: str = ""
    open_channel_id: str = ""
    closed_channel_id: str = ""

    google_sa_json: str = ""
    google_sheets_id: str = ""

    notion_token: str = ""
    notion_db_episodes: str = ""

    podster_rss_url: str = ""

    payment_provider_token: str = ""
    payment_currency: str = "XTR"
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""

    database_url: str = ""
    redis_url: str = ""
    use_redis: bool = False

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    subscription_price: int = 790
    subscription_days: int = 30
    trial_days: int = 1
    bot_username: str = "AlekhinaU_bot"

    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.admin_ids_raw]

    @property
    def admin_ids_raw(self) -> list[str]:
        return [p.strip() for p in self.admin_tg_ids.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
