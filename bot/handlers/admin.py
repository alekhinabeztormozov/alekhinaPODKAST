from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger
from sqlalchemy import func, select

from bot.content import ADMIN_DENIED
from bot.services import notion, sheets
from config import Settings, get_settings
from db.models import Contact, ProcessedPayment, Sale
from db.session import DatabaseNotConfigured, session_scope

router = Router(name="admin")


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_ids


@router.message(Command("admin"))
async def admin_stats(message: Message) -> None:
    settings = get_settings()
    if not _is_admin(message, settings):
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


@router.message(Command("setup_sheets"))
async def setup_sheets(message: Message) -> None:
    settings = get_settings()
    if not _is_admin(message, settings):
        await message.answer(ADMIN_DENIED)
        return
    ok = await sheets.bootstrap()
    await message.answer("Таблицы созданы." if ok else "Sheets не настроен — проверь GOOGLE_SA_JSON и доступ.")


@router.message(Command("setup_notion"))
async def setup_notion(message: Message, command: CommandObject) -> None:
    settings = get_settings()
    if not _is_admin(message, settings):
        await message.answer(ADMIN_DENIED)
        return
    parent_page_id = (command.args or "").strip()
    if not parent_page_id:
        await message.answer("Пришли id родительской страницы: /setup_notion <page_id>")
        return
    database_id = await notion.create_episodes_db(parent_page_id)
    if database_id:
        await message.answer(f"База «Эпизоды» создана.\nID: {database_id}\nВпиши его в NOTION_DB_EPISODES.")
    else:
        await message.answer("Не создал базу — проверь NOTION_TOKEN и доступ интеграции к странице.")


async def _week_stats() -> dict[str, int]:
    since = datetime.now(UTC) - timedelta(days=7)
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
