from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def clear_recent(bot: Bot, chat_id: int, up_to_id: int, window: int = 40) -> None:
    async def _delete(message_id: int) -> None:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass

    start = max(up_to_id - window, 1)
    await asyncio.gather(*[_delete(mid) for mid in range(up_to_id, start - 1, -1)])


async def show(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    message = callback.message
    if message is not None:
        try:
            await message.edit_text(text, reply_markup=reply_markup)
        except Exception:
            await message.answer(text, reply_markup=reply_markup)
    await callback.answer()
