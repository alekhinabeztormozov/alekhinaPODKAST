from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import Bot
from loguru import logger
from sqlalchemy.exc import IntegrityError

from bot.services import catalog, sales, users
from config import Settings, get_settings
from db.models import ProcessedPayment
from db.session import DatabaseNotConfigured, session_scope


async def _already_done(payment_id: str, tg_id: int, kind: str, amount: int, currency: str) -> bool:
    try:
        async with session_scope() as session:
            session.add(
                ProcessedPayment(
                    provider_payment_id=payment_id, tg_id=tg_id, kind=kind,
                    amount=amount, currency=currency,
                )
            )
        return False
    except IntegrityError:
        return True
    except DatabaseNotConfigured:
        return False


async def _invite_link(bot: Bot, settings: Settings) -> str:
    if not settings.closed_channel_id:
        return ""
    try:
        expire = datetime.now(UTC) + timedelta(days=settings.subscription_days)
        link = await bot.create_chat_invite_link(
            chat_id=settings.closed_channel_id, member_limit=1, expire_date=expire,
        )
        return link.invite_link
    except Exception as exc:
        logger.error("Не создал invite: {}", exc)
        return ""


async def fulfill(bot: Bot, payment_id: str, metadata: dict[str, Any], amount: int, currency: str) -> bool:
    kind = metadata.get("kind", "")
    try:
        tg_id = int(metadata.get("tg_id", 0))
    except (TypeError, ValueError):
        tg_id = 0
    if not tg_id or kind not in {"sub", "season"}:
        logger.warning("Платёж {} без корректных metadata: {}", payment_id, metadata)
        return False

    if await _already_done(payment_id, tg_id, kind, amount, currency):
        logger.info("Платёж {} уже обработан", payment_id)
        return False

    settings = get_settings()
    if kind == "sub":
        expires = await users.grant_subscription(tg_id, settings.subscription_days)
        invite = await _invite_link(bot, settings)
        tail = f"\nСсылка на клуб: {invite}" if invite else ""
        await bot.send_message(
            tg_id,
            f"✅ Ты в клубе «Код Алёхиной»!\nДоступ активен до {expires:%d.%m.%Y}.{tail}",
        )
        await sales.record(tg_id, "subscription", amount, currency)
        return True

    season_id = metadata.get("season_id", "")
    await users.add_purchased_season(tg_id, season_id)
    season = await catalog.get_season(season_id)
    link = season["archive_link"] if season else ""
    title = season["title"] if season else season_id
    await bot.send_message(
        tg_id,
        f"✅ Оплата прошла! Доступ к сезону «{title}» открыт навсегда.\nАрхив: {link}",
    )
    await sales.record(tg_id, f"season:{season_id}", amount, currency)
    return True
