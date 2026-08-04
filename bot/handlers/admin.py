from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger
from sqlalchemy import func, select

from bot.content import ADMIN_DENIED
from config import get_settings
from db.models import Contact, ProcessedPayment, Sale
from db.session import DatabaseNotConfigured, session_scope

router = Router(name="admin")


@router.message(Command("admin"))
async def admin_stats(message: Message) -> None:
    settings = get_settings()
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        await message.answer(ADMIN_DENIED)
        return

    try:
        stats = await _week_stats()
    except DatabaseNotConfigured:
        await message.answer("Статистика появится после подключения базы данных.")
        return
    except Exception as exc:
        logger.error("Статистика упала: {}", exc)
        await message.answer("Не удалось собрать статистику.")
        return

    await message.answer(
        "Статистика за 7 дней\n\n"
        f"Новые контакты: {stats['contacts']}\n"
        f"Продажи: {stats['sales']}\n"
        f"Платежи всего: {stats['payments']}"
    )


async def _week_stats() -> dict[str, int]:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    async with session_scope() as session:
        contacts = await session.scalar(
            select(func.count()).select_from(Contact).where(Contact.created_at >= since)
        )
        sales = await session.scalar(
            select(func.count()).select_from(Sale).where(Sale.created_at >= since)
        )
        payments = await session.scalar(
            select(func.count()).select_from(ProcessedPayment).where(ProcessedPayment.created_at >= since)
        )
    return {"contacts": contacts or 0, "sales": sales or 0, "payments": payments or 0}
