from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from loguru import logger

from config import get_settings

CONTACTS_SHEET = "База контактов"
SALES_SHEET = "Продажи"
MARATHON_SHEET = "Участники марафона"
AMBASSADORS_SHEET = "Игры и амбассадоры"

SHEET_HEADERS: dict[str, list[str]] = {
    CONTACTS_SHEET: ["Telegram ID", "Имя", "Email", "Дата подписки", "Источник", "Результат квиза"],
    SALES_SHEET: ["Дата", "Telegram ID", "Товар", "Сумма", "Статус оплаты"],
    MARATHON_SHEET: ["Telegram ID", "Имя", "Название марафона", "Прогресс", "Задания"],
    AMBASSADORS_SHEET: ["Имя", "Контакты", "Статус", "Количество игр", "Комиссия"],
}


class SheetsNotConfigured(RuntimeError):
    pass


@lru_cache
def _client() -> Any:
    settings = get_settings()
    if not settings.google_sa_json or not settings.google_sheets_id:
        raise SheetsNotConfigured("GOOGLE_SA_JSON / GOOGLE_SHEETS_ID не заданы")
    import gspread

    return gspread.service_account(filename=settings.google_sa_json)


def _spreadsheet() -> Any:
    return _client().open_by_key(get_settings().google_sheets_id)


def _worksheet(title: str) -> Any:
    return _spreadsheet().worksheet(title)


def _append_sync(title: str, row: list[Any]) -> None:
    _worksheet(title).append_row(row, value_input_option="USER_ENTERED")


def _bootstrap_sync() -> None:
    import gspread

    spreadsheet = _spreadsheet()
    for title, headers in SHEET_HEADERS.items():
        try:
            worksheet = spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=title, rows=200, cols=max(len(headers), 5))
        worksheet.update([headers], "A1")


async def _append(title: str, row: list[Any]) -> bool:
    try:
        await asyncio.to_thread(_append_sync, title, row)
        return True
    except SheetsNotConfigured:
        logger.warning("Sheets не настроен — пропускаю запись в {}", title)
        return False
    except Exception as exc:
        logger.error("Sheets запись в {} упала: {}", title, exc)
        return False


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M")


async def bootstrap() -> bool:
    try:
        await asyncio.to_thread(_bootstrap_sync)
        return True
    except SheetsNotConfigured:
        logger.warning("Sheets не настроен — bootstrap пропущен")
        return False
    except Exception as exc:
        logger.error("Sheets bootstrap упал: {}", exc)
        return False


async def add_contact(
    tg_id: int,
    name: str,
    email: str = "",
    source: str = "",
    quiz_result: str = "",
) -> bool:
    return await _append(CONTACTS_SHEET, [tg_id, name, email, _now(), source, quiz_result])


async def add_sale(tg_id: int, item: str, amount: int, status: str = "paid") -> bool:
    return await _append(SALES_SHEET, [_now(), tg_id, item, amount, status])
