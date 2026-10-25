from __future__ import annotations

import asyncio
import io
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.handlers.producer import MAX_TG_DOWNLOAD, OUT_DIR, _is_owner, owner_only
from config import get_settings
from pdf import workbook_writer
from pdf.workbook import WorkbookDoc, render_workbook
from reels import store
from reels.transcribe import load_transcript, transcript_text

router = Router(name="workbooks")

PDF_MIME = "application/pdf"
DEFAULT_CODE = "1.1"


def episode_pdf_kb(reel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Сделать PDF к выпуску", callback_data=f"wb:ep:{reel_id}")
    return builder.as_markup()


async def send_workbook(bot: Bot, chat_id: int, doc: WorkbookDoc) -> None:
    out = OUT_DIR / f"wb_{uuid.uuid4().hex[:12]}.pdf"
    await asyncio.to_thread(render_workbook, doc, out)
    try:
        await bot.send_document(chat_id, FSInputFile(out, filename=f"PDF {doc.code} {doc.title}.pdf"))
    finally:
        out.unlink(missing_ok=True)


@router.message(StateFilter(None), owner_only, F.document.mime_type == PDF_MIME)
async def restyle_pdf(message: Message, bot: Bot) -> None:
    document = message.document
    if (document.file_size or 0) > MAX_TG_DOWNLOAD:
        await message.answer("PDF больше 20 МБ, Telegram не отдаст его боту.")
        return
    await message.answer("Оформляю в фирменном стиле, пару минут…")
    buffer = io.BytesIO()
    await bot.download(document.file_id, destination=buffer)
    try:
        doc = await workbook_writer.restyle(workbook_writer.pdf_text(buffer.getvalue()))
        await send_workbook(bot, message.chat.id, doc)
    except Exception as exc:
        logger.error("Оформление PDF упало: {}", exc)
        await message.answer("Не получилось оформить PDF. Лев посмотрит.")


@router.callback_query(F.data.startswith("wb:ep:"))
async def episode_pdf(callback: CallbackQuery, bot: Bot) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    reel = await store.get(int(callback.data.rsplit(":", 1)[1]))
    transcript = transcript_text(load_transcript(reel.episode_ref)) if reel else ""
    if not transcript:
        await callback.answer("Расшифровки выпуска нет", show_alert=True)
        return
    await callback.answer("Собираю PDF…")
    try:
        doc = await workbook_writer.from_transcript(reel.episode_title, DEFAULT_CODE, transcript)
        await send_workbook(bot, callback.from_user.id, doc)
    except Exception as exc:
        logger.error("PDF к выпуску {} упал: {}", reel.episode_ref, exc)
        await bot.send_message(callback.from_user.id, "Не получилось собрать PDF. Лев посмотрит.")
