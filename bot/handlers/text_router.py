from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from bot.content import SEARCH_NONE
from bot.handlers.bonus import deliver
from bot.keyboards.common import main_menu, search_results_kb
from bot.services import catalog, users
from config import get_settings

router = Router(name="text_router")


@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def route_text(message: Message) -> None:
    if message.from_user is None:
        return
    if message.from_user.id in get_settings().admin_ids:
        return

    query = (message.text or "").strip()
    await users.get_or_create(message.from_user.id, message.from_user.username or message.from_user.full_name)

    bonus = await catalog.bonus_by_keyword(query)
    if bonus is not None:
        await deliver(message, message.from_user.id, bonus)
        return

    results = await catalog.search(query)
    if not results:
        await message.answer(SEARCH_NONE, reply_markup=main_menu())
        return

    lines = [f"🔍 Нашёл по запросу «{query}»:", ""]
    for index, item in enumerate(results, 1):
        kind = "эпизод" if item["kind"] == "episode" else "бонус"
        lines.append(f"{index}. {item['title']} — {kind}")
    await message.answer("\n".join(lines), reply_markup=search_results_kb(results))
