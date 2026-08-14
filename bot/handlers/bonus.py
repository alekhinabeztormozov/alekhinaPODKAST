from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.content import BONUS_DELIVERED, VOICE_DEMO_NOTE
from bot.keyboards.common import after_bonus_kb
from bot.services import catalog, users
from config import get_settings

router = Router(name="bonus")


async def deliver(message: Message, tg_id: int, bonus: dict[str, Any]) -> None:
    price = get_settings().subscription_price
    text = BONUS_DELIVERED.format(pdf=bonus["pdf_link"] or "—", audio=bonus["audio_link"] or "—")
    await message.answer(text, reply_markup=after_bonus_kb(price))
    if bonus.get("audio_link") and await users.take_voice_demo(tg_id):
        await message.answer(VOICE_DEMO_NOTE, reply_markup=after_bonus_kb(price))


@router.callback_query(F.data.startswith("bonus:"))
async def bonus_by_button(callback: CallbackQuery) -> None:
    bonus_id = callback.data.split(":", 1)[1]
    bonus = await catalog.bonus_by_id(bonus_id)
    if bonus is None or callback.message is None or callback.from_user is None:
        await callback.answer("Бонус не найден.", show_alert=True)
        return
    await callback.answer()
    await deliver(callback.message, callback.from_user.id, bonus)
