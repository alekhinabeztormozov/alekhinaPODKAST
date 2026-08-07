from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.content import MENU_HINT, OWNER_PANEL, WELCOME
from bot.keyboards.common import main_menu, owner_menu
from bot.ui import show
from config import get_settings

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user is not None and message.from_user.id in get_settings().admin_ids:
        await message.answer(OWNER_PANEL, reply_markup=owner_menu())
        return
    await message.answer(WELCOME, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(callback, MENU_HINT, main_menu())
