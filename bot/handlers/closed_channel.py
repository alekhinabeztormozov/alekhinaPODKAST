from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.content import CLOSED_INTRO
from bot.keyboards.common import closed_channel_kb, offer_closed
from bot.services import payments, subscriptions
from bot.ui import show
from config import Settings, get_settings
from db.session import DatabaseNotConfigured

router = Router(name="closed_channel")


@router.callback_query(F.data == "closed")
async def show_closed(callback: CallbackQuery) -> None:
    settings = get_settings()
    await show(callback, CLOSED_INTRO.format(price=settings.subscription_price), closed_channel_kb())


@router.callback_query(F.data == "closed:trial")
async def start_trial(callback: CallbackQuery, bot: Bot) -> None:
    settings = get_settings()
    user_id = callback.from_user.id if callback.from_user else None
    if user_id is None:
        await callback.answer()
        return

    try:
        if await subscriptions.has_used_trial(user_id):
            await show(callback, "Пробный день уже был. Оформи подписку, чтобы остаться.", closed_channel_kb())
            return
        await subscriptions.grant(user_id, days=settings.trial_days, status="trial")
    except DatabaseNotConfigured:
        await show(callback, "Триал скоро будет доступен. Загляни в меню позже.", offer_closed())
        return
    except Exception as exc:
        logger.error("Триал упал: {}", exc)
        await callback.answer("Не получилось, попробуй позже.", show_alert=True)
        return

    link = await _invite_link(bot, settings)
    if link:
        await show(callback, f"День бесплатно активирован. Заходи: {link}", offer_closed())
    else:
        await show(callback, "Доступ активирован. Ссылку пришлём, как только канал будет готов.", offer_closed())


@router.callback_query(F.data == "closed:buy")
async def buy_subscription(callback: CallbackQuery, bot: Bot) -> None:
    settings = get_settings()
    if not _payments_ready(settings):
        await show(callback, "Оплата скоро подключится. Пока доступен бесплатный день.", closed_channel_kb())
        return
    if callback.message is not None:
        await payments.send_subscription_invoice(bot, callback.message.chat.id, settings)
    await callback.answer()


def _payments_ready(settings: Settings) -> bool:
    return settings.payment_currency == "XTR" or bool(settings.payment_provider_token)


async def _invite_link(bot: Bot, settings: Settings) -> str | None:
    if not settings.closed_channel_id:
        return None
    try:
        expire = datetime.now(UTC) + timedelta(days=1)
        link = await bot.create_chat_invite_link(
            chat_id=settings.closed_channel_id,
            member_limit=1,
            expire_date=expire,
        )
        return link.invite_link
    except Exception as exc:
        logger.error("Не создал invite-ссылку: {}", exc)
        return None
