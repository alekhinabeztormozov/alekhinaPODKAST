from __future__ import annotations

from aiogram.types import CallbackQuery, InlineKeyboardMarkup


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
