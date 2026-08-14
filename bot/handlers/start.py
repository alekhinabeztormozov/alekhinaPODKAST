from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.content import MENU_HINT, OWNER_PANEL, SEARCH_PROMPT, START_TEXT
from bot.keyboards.common import back_to_menu, main_menu, owner_menu
from bot.ui import clear_recent, show
from config import get_settings

router = Router(name="start")


def _is_owner(user_id: int | None) -> bool:
    return user_id is not None and user_id in get_settings().admin_ids


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    await clear_recent(bot, message.chat.id, message.message_id)
    if message.from_user is not None and _is_owner(message.from_user.id):
        await message.answer(OWNER_PANEL, reply_markup=owner_menu())
        return
    await message.answer(START_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def back_to_menu_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.from_user is not None and _is_owner(callback.from_user.id):
        await show(callback, OWNER_PANEL, owner_menu())
        return
    await show(callback, MENU_HINT, main_menu())


@router.callback_query(F.data == "search")
async def search_prompt(callback: CallbackQuery) -> None:
    await show(callback, SEARCH_PROMPT, back_to_menu())
