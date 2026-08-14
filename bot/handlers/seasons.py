from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.content import PAY_LINK, PAY_UNAVAILABLE, SHOP_TEXT
from bot.keyboards.common import back_to_menu, shop_kb
from bot.services import catalog, users, yookassa
from bot.ui import show
from config import get_settings

router = Router(name="seasons")


def _return_url() -> str:
    return f"https://t.me/{get_settings().bot_username}"


@router.callback_query(F.data == "shop")
async def show_shop(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    seasons = await catalog.all_seasons()
    if not seasons:
        await show(callback, "Сезоны появятся совсем скоро.", back_to_menu())
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    await show(callback, SHOP_TEXT, shop_kb(seasons, subscribed))


@router.callback_query(F.data.startswith("season:buy:"))
async def buy_season(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    season_id = callback.data.split(":", 2)[2]
    season = await catalog.get_season(season_id)
    if season is None:
        await callback.answer("Сезон не найден.", show_alert=True)
        return

    tg_id = callback.from_user.id
    if await users.has_season(tg_id, season_id):
        await show(callback, f"У тебя уже есть доступ к сезону «{season['title']}».\n{season['archive_link']}")
        return

    subscribed = await users.is_subscribed(tg_id)
    price = season["price_subscriber"] if subscribed else season["price"]
    try:
        payment = await yookassa.create_payment(
            price,
            f"Доступ к сезону «{season['title']}»",
            {"kind": "season", "season_id": season_id, "tg_id": tg_id},
            _return_url(),
        )
    except yookassa.YooKassaNotConfigured:
        await callback.answer()
        await show(callback, PAY_UNAVAILABLE, back_to_menu())
        return
    except Exception as exc:
        logger.error("Оплата сезона упала: {}", exc)
        await callback.answer("Не удалось создать оплату.", show_alert=True)
        return
    await callback.answer()
    await show(callback, PAY_LINK.format(url=yookassa.confirmation_url(payment)))
