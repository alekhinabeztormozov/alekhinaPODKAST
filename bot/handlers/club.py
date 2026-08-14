from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.content import (
    CLUB_ACTIVE,
    CLUB_OFFER,
    PAY_LINK,
    PAY_UNAVAILABLE,
    SEARCH_NONE,
)
from bot.keyboards.common import bonuses_list_kb, club_active_kb, club_offer_kb
from bot.services import catalog, users, yookassa
from bot.ui import show
from config import get_settings

router = Router(name="club")


def _return_url() -> str:
    return f"https://t.me/{get_settings().bot_username}"


@router.callback_query(F.data == "club")
async def show_club(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    if await users.is_subscribed(callback.from_user.id):
        await show(callback, CLUB_ACTIVE.format(until="—"), club_active_kb())
        return
    price = get_settings().subscription_price
    await show(callback, CLUB_OFFER.format(price=price), club_offer_kb(price))


@router.callback_query(F.data == "club:buy")
async def buy_club(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    price = get_settings().subscription_price
    try:
        payment = await yookassa.create_payment(
            price,
            "Подписка на клуб «Код Алёхиной»",
            {"kind": "sub", "tg_id": callback.from_user.id},
            _return_url(),
        )
    except yookassa.YooKassaNotConfigured:
        await callback.answer()
        await show(callback, PAY_UNAVAILABLE, club_offer_kb(price))
        return
    except Exception as exc:
        logger.error("Оплата клуба упала: {}", exc)
        await callback.answer("Не удалось создать оплату.", show_alert=True)
        return
    await callback.answer()
    await show(callback, PAY_LINK.format(url=yookassa.confirmation_url(payment)))


@router.callback_query(F.data == "club:bonuses")
async def club_bonuses(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    if not await users.is_subscribed(callback.from_user.id):
        price = get_settings().subscription_price
        await show(callback, CLUB_OFFER.format(price=price), club_offer_kb(price))
        return
    season = await catalog.current_season()
    bonuses = await catalog.season_bonuses(season["season_id"]) if season else []
    if not bonuses:
        await show(callback, SEARCH_NONE)
        return
    await show(callback, "🎁 Бонусы текущего сезона:", bonuses_list_kb(bonuses))
