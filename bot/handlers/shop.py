from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from bot.content import SHOP_INTRO, SHOP_ITEMS, find_item
from bot.keyboards.common import shop_kb
from bot.services import payments
from bot.ui import show
from config import get_settings

router = Router(name="shop")


@router.callback_query(F.data == "shop")
async def show_shop(callback: CallbackQuery) -> None:
    await show(callback, SHOP_INTRO, shop_kb(SHOP_ITEMS))


@router.callback_query(F.data.startswith("shop:buy:"))
async def buy_item(callback: CallbackQuery, bot: Bot) -> None:
    item_id = callback.data.split(":", 2)[2]
    item = find_item(item_id)
    if item is None or callback.message is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    settings = get_settings()
    if settings.payment_currency != "XTR" and not settings.payment_provider_token:
        await callback.answer("Оплата скоро подключится.", show_alert=True)
        return

    await payments.send_item_invoice(bot, callback.message.chat.id, item, settings)
    await callback.answer()
