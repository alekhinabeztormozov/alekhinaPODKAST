from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from bot.handlers import admin, closed_channel, payments, pdf_bonus, producer, quiz, shop, start
from bot.middlewares.throttling import ThrottlingMiddleware
from config import Settings, get_settings


def build_storage(settings: Settings) -> BaseStorage:
    if settings.use_redis and settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        return RedisStorage.from_url(settings.redis_url)
    return MemoryStorage()


def build_bot(settings: Settings) -> Bot:
    session = None
    if settings.telegram_proxy:
        from aiogram.client.session.aiohttp import AiohttpSession

        session = AiohttpSession(proxy=settings.telegram_proxy)
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )


def build_dispatcher(settings: Settings) -> Dispatcher:
    dispatcher = Dispatcher(storage=build_storage(settings))
    dispatcher.message.middleware(ThrottlingMiddleware())
    dispatcher.callback_query.middleware(ThrottlingMiddleware())
    dispatcher.include_routers(
        start.router,
        pdf_bonus.router,
        quiz.router,
        closed_channel.router,
        shop.router,
        payments.router,
        producer.router,
        admin.router,
    )
    return dispatcher


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан — заполни .env")

    bot = build_bot(settings)
    dispatcher = build_dispatcher(settings)

    logger.info("Бот запускается")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
