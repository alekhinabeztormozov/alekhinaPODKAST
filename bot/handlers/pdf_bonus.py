from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from bot.content import PDF_ASK_EMAIL, PDF_DELIVERED
from bot.keyboards.common import offer_closed, pdf_skip
from bot.services import sheets
from bot.states.flows import PdfBonus
from bot.ui import show

router = Router(name="pdf_bonus")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BONUS_LINK = "https://example.com/bonus.pdf"


@router.callback_query(F.data == "pdf")
async def start_pdf(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PdfBonus.waiting_email)
    await show(callback, PDF_ASK_EMAIL, pdf_skip())


@router.callback_query(F.data == "pdf:skip", PdfBonus.waiting_email)
async def skip_email(callback: CallbackQuery, state: FSMContext) -> None:
    await _deliver(callback.from_user, state, email="")
    await show(callback, PDF_DELIVERED.format(link=BONUS_LINK), offer_closed())


@router.message(PdfBonus.waiting_email)
async def got_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer("Не похоже на email. Пришли ещё раз или нажми «Пропустить».")
        return
    await _deliver(message.from_user, state, email=email)
    await message.answer(PDF_DELIVERED.format(link=BONUS_LINK), reply_markup=offer_closed())


async def _deliver(user: User | None, state: FSMContext, email: str) -> None:
    await state.clear()
    if user is not None:
        await sheets.add_contact(
            tg_id=user.id,
            name=user.full_name,
            email=email,
            source="pdf_bonus",
        )
