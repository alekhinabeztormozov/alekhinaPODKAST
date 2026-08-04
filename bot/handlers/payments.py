from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.types import Message, PreCheckoutQuery
from loguru import logger
from sqlalchemy.exc import IntegrityError

from bot.content import find_item
from bot.keyboards.common import main_menu
from bot.services import sheets, subscriptions
from config import Settings, get_settings
from db.models import ProcessedPayment
from db.session import DatabaseNotConfigured, session_scope

router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_success(message: Message, bot: Bot) -> None:
    payment = message.successful_payment
    if payment is None or message.from_user is None:
        return

    user_id = message.from_user.id
    payload = payment.invoice_payload
    kind = "sub" if payload == "sub" else "item"

    if not await _register_payment(payment.telegram_payment_charge_id, user_id, kind, payload, payment):
        return

    settings = get_settings()
    if payload == "sub":
        await _fulfill_subscription(message, bot, user_id, settings, payment.total_amount)
    elif payload.startswith("item:"):
        await _fulfill_item(message, user_id, payload.split(":", 1)[1], payment.total_amount)


async def _register_payment(
    charge_id: str,
    user_id: int,
    kind: str,
    payload: str,
    payment: object,
) -> bool:
    try:
        async with session_scope() as session:
            session.add(
                ProcessedPayment(
                    provider_payment_id=charge_id,
                    tg_id=user_id,
                    kind=kind,
                    payload=payload,
                    amount=getattr(payment, "total_amount", 0),
                    currency=getattr(payment, "currency", ""),
                )
            )
        return True
    except IntegrityError:
        logger.info("Повторный платёж {} — пропускаю", charge_id)
        return False
    except DatabaseNotConfigured:
        logger.warning("БД не настроена — выдаю без дедупликации")
        return True
    except Exception as exc:
        logger.error("Регистрация платежа упала: {}", exc)
        return True


async def _fulfill_subscription(
    message: Message,
    bot: Bot,
    user_id: int,
    settings: Settings,
    amount: int,
) -> None:
    try:
        await subscriptions.grant(user_id, days=settings.subscription_days, status="active")
    except DatabaseNotConfigured:
        logger.warning("БД не настроена — подписка не сохранена")
    except Exception as exc:
        logger.error("Не выдал подписку: {}", exc)

    link = await _invite_link(bot, settings)
    tail = f"\nСсылка на канал: {link}" if link else ""
    await message.answer("Подписка активна. Спасибо!" + tail, reply_markup=main_menu())
    await sheets.add_sale(user_id, "subscription", amount)


async def _fulfill_item(message: Message, user_id: int, item_id: str, amount: int) -> None:
    item = find_item(item_id)
    title = item.title if item else item_id
    await message.answer(f"Спасибо! Твой гайд «{title}» уже в пути.", reply_markup=main_menu())
    await sheets.add_sale(user_id, item_id, amount)


async def _invite_link(bot: Bot, settings: Settings) -> str | None:
    if not settings.closed_channel_id:
        return None
    try:
        expire = datetime.now(UTC) + timedelta(days=settings.subscription_days)
        link = await bot.create_chat_invite_link(
            chat_id=settings.closed_channel_id,
            member_limit=1,
            expire_date=expire,
        )
        return link.invite_link
    except Exception as exc:
        logger.error("Не создал invite-ссылку: {}", exc)
        return None
