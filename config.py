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

    vk_group_token: str = ""
    vk_group_id: int = 0
    vk_confirmation_token: str = ""
    vk_secret: str = ""
    vk_api_version: str = "5.199"

    podster_rss_url: str = ""

    payment_provider_token: str = ""
    payment_currency: str = "XTR"
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_proxy: str = ""

    database_url: str = ""
    redis_url: str = ""
    use_redis: bool = False

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    subscription_price: int = 790
    subscription_days: int = 30
    subscription_price_3m: int = 1890
    subscription_days_3m: int = 90
    trial_hours: int = 24

    workbook_price: int = 599
    workbook_price_subscriber: int = 359
    all_seasons_price: int = 999
    all_seasons_price_subscriber: int = 599
    all_seasons_season_id: str = "all"

    bot_username: str = "AlekhinaU_bot"

    anthropic_api_key: str = ""
    reels_model: str = "claude-opus-5-5"
    groq_api_key: str = ""
    transcribe_model: str = "whisper-large-v3"
    heygen_api_key: str = ""
    heygen_avatar_id: str = ""
    heygen_voice_id: str = ""
    heygen_test_mode: bool = False
    vk_user_token: str = ""
    reels_per_episode: int = 6
    reels_slots_msk: str = "12:00,19:00"
    reels_targets: str = "tg,vk,ig"
    report_tg_ids: str = ""

    @property
    def reel_slots(self) -> list[tuple[int, int]]:
        slots = []
        for chunk in self.reels_slots_msk.split(","):
            hours, _, minutes = chunk.strip().partition(":")
            if hours.isdigit():
                slots.append((int(hours), int(minutes or 0)))
        return sorted(slots)

    @property
    def reel_targets(self) -> list[str]:
        return [part.strip() for part in self.reels_targets.split(",") if part.strip()]

    @property
    def report_ids(self) -> list[int]:
        raw = [p.strip() for p in self.report_tg_ids.split(",") if p.strip()]
        return [int(x) for x in raw] or self.admin_ids

    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.admin_ids_raw]

    @property
    def admin_ids_raw(self) -> list[str]:
        return [p.strip() for p in self.admin_tg_ids.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
