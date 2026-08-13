from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.content import PDF_DELIVERED
from bot.keyboards.common import offer_closed
from bot.services import sheets
from bot.ui import show

router = Router(name="pdf_bonus")

BONUS_LINK = "https://example.com/bonus.pdf"


@router.callback_query(F.data == "pdf")
async def give_bonus(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = callback.from_user
    if user is not None:
        await sheets.add_contact(tg_id=user.id, name=user.full_name, source="pdf_bonus")
    await show(callback, PDF_DELIVERED.format(link=BONUS_LINK), offer_closed())
