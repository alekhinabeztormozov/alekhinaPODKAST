from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from config import get_settings
from scheduler.jobs import notify_ready, poll_rss, publish_due, revoke_expired


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан — заполни .env")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(poll_rss, "interval", minutes=10, args=[bot, settings])
    scheduler.add_job(publish_due, "interval", minutes=1, args=[bot])
    scheduler.add_job(notify_ready, "interval", minutes=5, args=[bot, settings])
    scheduler.add_job(revoke_expired, "interval", hours=6, args=[bot, settings])
    scheduler.start()

    logger.info("Планировщик запущен")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
