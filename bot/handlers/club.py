from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.content import (
    CLUB_ACTIVE,
    CLUB_OFFER,
    PAY_LINK,
    PAY_UNAVAILABLE,
    TRIAL_GRANTED,
    TRIAL_UNAVAILABLE,
)
from bot.keyboards.common import back_to_menu, bonuses_list_kb, club_active_kb, club_offer_kb
from bot.services import catalog, users, yookassa
from bot.ui import show
from config import get_settings

router = Router(name="club")


def _return_url() -> str:
    return f"https://t.me/{get_settings().bot_username}"


def _offer() -> tuple[str, object]:
    settings = get_settings()
    text = CLUB_OFFER.format(price=settings.subscription_price, price3=settings.subscription_price_3m)
    kb = club_offer_kb(settings.subscription_price, settings.subscription_price_3m)
    return text, kb


@router.callback_query(F.data == "club")
async def show_club(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    until = await users.subscription_until(callback.from_user.id)
    if until is not None:
        await show(callback, CLUB_ACTIVE.format(until=f"{until:%d.%m.%Y}"), club_active_kb())
        return
    text, kb = _offer()
    await show(callback, text, kb)


@router.callback_query(F.data.startswith("club:buy"))
async def buy_club(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    settings = get_settings()
    months = callback.data.split(":")[-1] if callback.data.count(":") >= 2 else "1"
    if months == "3":
        price = settings.subscription_price_3m
        days = settings.subscription_days_3m
        title = "Подписка на клуб «Код Алёхиной», 3 месяца"
    else:
        price = settings.subscription_price
        days = settings.subscription_days
        title = "Подписка на клуб «Код Алёхиной»"
    try:
        payment = await yookassa.create_payment(
            price, title,
            {"kind": "sub", "tg_id": callback.from_user.id, "days": days},
            _return_url(),
        )
    except yookassa.YooKassaNotConfigured:
        await callback.answer()
        _, kb = _offer()
        await show(callback, PAY_UNAVAILABLE, kb)
        return
    except Exception as exc:
        logger.error("Оплата клуба упала: {}", exc)
        await callback.answer("Не удалось создать оплату.", show_alert=True)
        return
    await callback.answer()
    await show(callback, PAY_LINK.format(url=yookassa.confirmation_url(payment)), back_to_menu())


@router.callback_query(F.data == "club:trial")
async def club_trial(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    settings = get_settings()
    until = await users.grant_trial(callback.from_user.id, settings.trial_hours)
    if until is None:
        _, kb = _offer()
        await show(callback, TRIAL_UNAVAILABLE, kb)
        return
    invite = await _trial_invite(bot, settings)
    tail = f"\nСсылка на клуб: {invite}" if invite else ""
    await show(callback, TRIAL_GRANTED.format(until=f"{until:%d.%m.%Y %H:%M}", invite=tail), club_active_kb())


async def _trial_invite(bot: Bot, settings) -> str:
    if not settings.closed_channel_id:
        return ""
    try:
        expire = datetime.now(UTC) + timedelta(hours=settings.trial_hours)
        link = await bot.create_chat_invite_link(
            chat_id=settings.closed_channel_id, member_limit=1, expire_date=expire,
        )
        return link.invite_link
    except Exception as exc:
        logger.error("Не создал trial-invite: {}", exc)
        return ""


@router.callback_query(F.data == "club:bonuses")
async def club_bonuses(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    if not await users.is_subscribed(callback.from_user.id):
        text, kb = _offer()
        await show(callback, text, kb)
        return
    season = await catalog.current_season()
    bonuses = await catalog.season_bonuses(season["season_id"]) if season else []
    if not bonuses:
        await show(callback, "Бонусы сезона появятся совсем скоро.", back_to_menu())
        return
    await show(callback, "🎁 Бонусы текущего сезона:", bonuses_list_kb(bonuses))
