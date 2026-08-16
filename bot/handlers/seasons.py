from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.content import (
    ALL_SEASONS_OFFER,
    PACK_UNAVAILABLE,
    PAY_LINK,
    PAY_UNAVAILABLE,
    SEASON_OFFER,
    SEASON_UPSELL_ALL,
    SEASON_UPSELL_CLUB,
    SHOP_TEXT,
    WORKBOOK_OFFER,
    WORKBOOK_PICK,
)
from bot.keyboards.common import (
    all_seasons_kb,
    back_to_menu,
    back_to_shop,
    season_offer_kb,
    seasons_list_kb,
    shop_kb,
    workbook_offer_kb,
    workbooks_list_kb,
)
from bot.services import catalog, users, yookassa
from bot.ui import show
from config import get_settings

router = Router(name="seasons")


def _return_url() -> str:
    return f"https://t.me/{get_settings().bot_username}"


async def _pay(callback: CallbackQuery, price: int, description: str, metadata: dict[str, Any]) -> None:
    try:
        payment = await yookassa.create_payment(price, description, metadata, _return_url())
    except yookassa.YooKassaNotConfigured:
        await callback.answer()
        await show(callback, PAY_UNAVAILABLE, back_to_menu())
        return
    except Exception as exc:
        logger.error("Оплата {} упала: {}", metadata, exc)
        await callback.answer("Не удалось создать оплату.", show_alert=True)
        return
    await callback.answer()
    await show(callback, PAY_LINK.format(url=yookassa.confirmation_url(payment)), back_to_menu())


def _all_price(pack: dict[str, Any] | None, subscribed: bool) -> int:
    settings = get_settings()
    if pack:
        return pack["price_subscriber"] if subscribed else pack["price"]
    return settings.all_seasons_price_subscriber if subscribed else settings.all_seasons_price


@router.callback_query(F.data == "shop")
async def show_shop(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    workbooks = await catalog.sellable_workbooks()
    pack = await catalog.all_seasons_pack()
    kb = shop_kb(
        all_seasons_price=_all_price(pack, subscribed),
        subscribed=subscribed,
        has_workbooks=bool(workbooks),
        has_pack=pack is not None,
    )
    await show(callback, SHOP_TEXT, kb)


@router.callback_query(F.data == "shop:seasons")
async def show_seasons(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    seasons = await catalog.all_seasons()
    if not seasons:
        await show(callback, "Сезоны появятся совсем скоро.", back_to_shop())
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    await show(callback, "📦 Выбери сезон:", seasons_list_kb(seasons, subscribed))


@router.callback_query(F.data == "shop:workbooks")
async def show_workbooks(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    workbooks = await catalog.sellable_workbooks()
    if not workbooks:
        await show(callback, "Рабочие тетради появятся совсем скоро.", back_to_shop())
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    await show(callback, WORKBOOK_PICK, workbooks_list_kb(workbooks, subscribed))


@router.callback_query(F.data == "shop:all")
async def show_all_seasons(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    pack = await catalog.all_seasons_pack()
    if pack is None:
        await show(callback, PACK_UNAVAILABLE, back_to_shop())
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    price = _all_price(pack, subscribed)
    note = "\nПодписчикам клуба — скидка 40%." if not subscribed else "\nЦена уже со скидкой подписчика."
    await show(callback, ALL_SEASONS_OFFER.format(price=price, note=note), all_seasons_kb(price))


@router.callback_query(F.data.startswith("season:show:"))
async def show_season(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    season_id = callback.data.split(":", 2)[2]
    season = await catalog.get_season(season_id)
    if season is None:
        await callback.answer("Сезон не найден.", show_alert=True)
        return
    tg_id = callback.from_user.id
    if await users.has_season(tg_id, season_id):
        await show(
            callback,
            f"У тебя уже есть доступ к сезону «{season['title']}».\n{season['archive_link']}",
            back_to_shop(),
        )
        return
    subscribed = await users.is_subscribed(tg_id)
    settings = get_settings()
    price = season["price_subscriber"] if subscribed else season["price"]
    text = SEASON_OFFER.format(title=season["title"], price=price)
    if not subscribed:
        text += SEASON_UPSELL_CLUB.format(club=settings.subscription_price, discounted=season["price_subscriber"])
    else:
        text += SEASON_UPSELL_ALL.format(price=settings.all_seasons_price_subscriber)
    await show(callback, text, season_offer_kb(season_id, price, subscribed))


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
        await show(
            callback,
            f"У тебя уже есть доступ к сезону «{season['title']}».\n{season['archive_link']}",
            back_to_shop(),
        )
        return

    subscribed = await users.is_subscribed(tg_id)
    price = season["price_subscriber"] if subscribed else season["price"]
    await _pay(
        callback, price, f"Доступ к сезону «{season['title']}»",
        {"kind": "season", "season_id": season_id, "tg_id": tg_id},
    )


@router.callback_query(F.data.startswith("wb:show:"))
async def show_workbook(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    season_id = callback.data.split(":", 2)[2]
    season = await catalog.get_season(season_id)
    if season is None or not season["workbook_link"]:
        await callback.answer("Тетрадь не найдена.", show_alert=True)
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    settings = get_settings()
    price = settings.workbook_price_subscriber if subscribed else settings.workbook_price
    await show(callback, WORKBOOK_OFFER.format(title=season["title"], price=price), workbook_offer_kb(season_id, price))


@router.callback_query(F.data.startswith("wb:buy:"))
async def buy_workbook(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    season_id = callback.data.split(":", 2)[2]
    season = await catalog.get_season(season_id)
    if season is None or not season["workbook_link"]:
        await callback.answer("Тетрадь не найдена.", show_alert=True)
        return
    subscribed = await users.is_subscribed(callback.from_user.id)
    settings = get_settings()
    price = settings.workbook_price_subscriber if subscribed else settings.workbook_price
    await _pay(
        callback, price, f"Рабочая тетрадь сезона «{season['title']}»",
        {"kind": "workbook", "season_id": season_id, "tg_id": callback.from_user.id},
    )


@router.callback_query(F.data == "all:buy")
async def buy_all_seasons(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    settings = get_settings()
    tg_id = callback.from_user.id
    if await users.has_season(tg_id, settings.all_seasons_season_id):
        await show(callback, "У тебя уже есть доступ ко всем сезонам.", back_to_shop())
        return
    pack = await catalog.all_seasons_pack()
    if pack is None:
        await show(callback, PACK_UNAVAILABLE, back_to_shop())
        return
    subscribed = await users.is_subscribed(tg_id)
    price = _all_price(pack, subscribed)
    await _pay(
        callback, price, "Доступ ко всем сезонам «Алёхина без тормозов»",
        {"kind": "all", "tg_id": tg_id},
    )
