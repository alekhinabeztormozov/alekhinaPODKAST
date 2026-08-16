from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger
from sqlalchemy import func, select

from bot.content import ADMIN_DENIED
from bot.services import admin_content, notion, sheets
from config import Settings, get_settings
from db.models import Contact, ProcessedPayment, Sale
from db.session import DatabaseNotConfigured, session_scope

router = Router(name="admin")


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_ids


@router.message(Command("admin"))
async def admin_stats(message: Message) -> None:
    if not _is_admin(message, get_settings()):
        await message.answer(ADMIN_DENIED)
        return
    await message.answer(await week_stats_text())


async def week_stats_text() -> str:
    try:
        stats = await _week_stats()
    except DatabaseNotConfigured:
        return "Статистика появится после подключения базы данных."
    except Exception as exc:
        logger.error("Статистика упала: {}", exc)
        return "Не удалось собрать статистику."
    return (
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


async def _run_add(message: Message, command: CommandObject, expected: int, func, usage: str) -> None:
    if not _is_admin(message, get_settings()):
        await message.answer(ADMIN_DENIED)
        return
    parts = [p.strip() for p in (command.args or "").split("|")]
    if len(parts) != expected:
        await message.answer("Формат:\n" + usage)
        return
    try:
        result = await func(parts)
    except Exception as exc:
        logger.error("Добавление контента упало: {}", exc)
        await message.answer(f"Ошибка: {exc}")
        return
    await message.answer(f"✅ {result}")


@router.message(Command("add_season"))
async def add_season(message: Message, command: CommandObject) -> None:
    await _run_add(message, command, 6, admin_content.add_season,
                   "/add_season id | Название | 299 | 179 | ссылка_на_архив | 1")


@router.message(Command("add_bonus"))
async def add_bonus(message: Message, command: CommandObject) -> None:
    await _run_add(message, command, 6, admin_content.add_bonus,
                   "/add_bonus id | season_id | КЛЮЧ | Название | pdf_ссылка | аудио_ссылка")


@router.message(Command("add_episode"))
async def add_episode(message: Message, command: CommandObject) -> None:
    await _run_add(message, command, 5, admin_content.add_episode,
                   "/add_episode id | season_id | Название | аудио_ссылка | тег1,тег2")


@router.message(Command("add_product"))
async def add_product(message: Message, command: CommandObject) -> None:
    await _run_add(message, command, 7, admin_content.add_product,
                   "/add_product id | season_id | Название | 3900 | 2730 | ссылка_оплаты | 1")


@router.message(Command("set_workbook"))
async def set_workbook(message: Message, command: CommandObject) -> None:
    await _run_add(message, command, 2, admin_content.set_workbook,
                   "/set_workbook season_id | ссылка_на_тетрадь")


@router.message(Command("content"))
async def content_counts(message: Message) -> None:
    if not _is_admin(message, get_settings()):
        await message.answer(ADMIN_DENIED)
        return
    c = await admin_content.counts()
    await message.answer(
        f"Контент:\nСезоны: {c['seasons']}\nЭпизоды: {c['episodes']}\n"
        f"Бонусы: {c['bonuses']}\nПродукты: {c['products']}"
    )


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
