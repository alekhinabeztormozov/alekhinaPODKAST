from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.content import INTENSIVE_TEXT, NO_INTENSIVE
from bot.keyboards.common import back_to_menu, intensive_kb
from bot.services import catalog, users
from bot.ui import show

router = Router(name="intensive")


@router.callback_query(F.data == "intensive")
async def show_intensive(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    product = await catalog.active_main_product()
    if product is None:
        await show(callback, NO_INTENSIVE, back_to_menu())
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    price = product["price_subscriber"] if subscribed else product["price"]
    text = INTENSIVE_TEXT.format(title=product["title"], description=product["description"], price=price)
    await show(callback, text, intensive_kb(product["payment_link"]))
