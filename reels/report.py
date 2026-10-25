from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot
from loguru import logger
from sqlalchemy import func, select

from bot.services import users
from config import Settings
from db.models import Sale, User
from db.session import session_scope
from reels import store

PERIOD = timedelta(days=7)
TARGET_TITLES = {"tg": "Telegram", "vk": "VK", "ig": "Instagram"}


async def _sales_since(moment: datetime) -> tuple[int, int]:
    async with session_scope() as session:
        result = await session.execute(
            select(func.count(Sale.id), func.coalesce(func.sum(Sale.amount), 0))
            .where(Sale.status == "paid")
            .where(Sale.created_at >= moment)
        )
        count, total = result.one()
    return int(count), int(total)


async def _new_users_since(moment: datetime) -> int:
    async with session_scope() as session:
        result = await session.execute(select(func.count(User.id)).where(User.registered_at >= moment))
        return int(result.scalar_one())


def _reel_line(reel) -> str:
    where = ", ".join(TARGET_TITLES.get(target, target) for target in reel.published) or "никуда"
    return f"- {reel.scenario.get('title', 'ролик')} ({where})"


async def weekly_report_text(now: datetime | None = None) -> str:
    since = (now or datetime.now(UTC)) - PERIOD
    reels = await store.published_since(since)
    sales_count, sales_total = await _sales_since(since)
    new_users = await _new_users_since(since)
    subscribers = len(await users.subscriber_ids())
    lines = [
        "Отчет за неделю",
        "",
        f"Роликов вышло: {len(reels)}",
        *[_reel_line(reel) for reel in reels],
        "",
        f"Продажи: {sales_count} на {sales_total} ₽",
        f"Новых людей в боте: {new_users}",
        f"Подписчиков клуба сейчас: {subscribers}",
    ]
    waiting = await store.counts()
    if waiting.get(store.DRAFT):
        lines.append(f"\nСценариев ждут вашей проверки: {waiting[store.DRAFT]}")
    return "\n".join(lines)


async def send_weekly_report(bot: Bot, settings: Settings) -> int:
    text = await weekly_report_text()
    sent = 0
    for chat_id in settings.admin_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode=None)
            sent += 1
        except Exception as exc:
            logger.error("Отчет {} не дошел: {}", chat_id, exc)
    return sent
