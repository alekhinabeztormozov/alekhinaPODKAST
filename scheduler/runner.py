from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from bot.main import build_bot
from config import get_settings
from scheduler.jobs import (
    notify_finale,
    notify_ready,
    notify_season_ending,
    poll_rss,
    publish_due,
    pull_notion,
    revoke_expired,
)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан — заполни .env")

    bot = build_bot(settings)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(poll_rss, "interval", minutes=10, args=[bot, settings])
    scheduler.add_job(pull_notion, "interval", minutes=5, args=[bot, settings])
    scheduler.add_job(publish_due, "interval", minutes=1, args=[bot])
    scheduler.add_job(notify_ready, "interval", minutes=5, args=[bot, settings])
    scheduler.add_job(revoke_expired, "interval", hours=6, args=[bot, settings])
    scheduler.add_job(notify_season_ending, "interval", hours=12, args=[bot, settings])
    scheduler.add_job(notify_finale, "interval", hours=12, args=[bot, settings])
    scheduler.start()

    logger.info("Планировщик запущен")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
