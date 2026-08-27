from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import Bot
from loguru import logger
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from bot.services import catalog, sales, sheets, users
from config import Settings, get_settings
from db.models import ProcessedPayment
from db.session import DatabaseNotConfigured, session_scope

KINDS = {"sub", "season", "workbook", "all"}


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


async def _release(payment_id: str) -> None:
    """Снять резерв идемпотентности, чтобы вебхук ЮKassa повторил выдачу."""
    try:
        async with session_scope() as session:
            await session.execute(
                delete(ProcessedPayment).where(ProcessedPayment.provider_payment_id == payment_id)
            )
    except Exception as exc:
        logger.error("Не снял резерв платежа {}: {}", payment_id, exc)


async def _notify(bot: Bot, tg_id: int, text: str) -> None:
    """Сообщение о выдаче — best-effort: доступ уже выдан, сбой отправки не критичен."""
    try:
        await bot.send_message(tg_id, text)
    except Exception as exc:
        logger.error("Не отправил сообщение о выдаче {}: {}", tg_id, exc)


async def _invite_link(bot: Bot, settings: Settings, days: int) -> str:
    if not settings.closed_channel_id:
        return ""
    try:
        expire = datetime.now(UTC) + timedelta(days=days)
        link = await bot.create_chat_invite_link(
            chat_id=settings.closed_channel_id, member_limit=1, expire_date=expire,
        )
        return link.invite_link
    except Exception as exc:
        logger.error("Не создал invite: {}", exc)
        return ""


async def _record_sale(tg_id: int, item: str, amount: int, currency: str) -> None:
    try:
        await sales.record(tg_id, item, amount, currency)
        await sheets.add_sale(tg_id, item, amount)
    except Exception as exc:
        logger.error("Не записал продажу {} {}: {}", tg_id, item, exc)


async def fulfill(bot: Bot, payment_id: str, metadata: dict[str, Any], amount: int, currency: str) -> bool:
    kind = metadata.get("kind", "")
    try:
        tg_id = int(metadata.get("tg_id", 0))
    except (TypeError, ValueError):
        tg_id = 0
    if not tg_id or kind not in KINDS:
        logger.warning("Платёж {} без корректных metadata: {}", payment_id, metadata)
        return False

    if await _already_done(payment_id, tg_id, kind, amount, currency):
        logger.info("Платёж {} уже обработан", payment_id)
        return False

    settings = get_settings()
    try:
        if kind == "sub":
            return await _fulfill_sub(bot, tg_id, metadata, amount, currency, settings)
        if kind == "workbook":
            return await _fulfill_workbook(bot, tg_id, metadata, amount, currency)
        if kind == "all":
            return await _fulfill_all(bot, tg_id, amount, currency, settings)
        return await _fulfill_season(bot, tg_id, metadata, amount, currency)
    except Exception:
        await _release(payment_id)
        raise


async def _fulfill_sub(
    bot: Bot, tg_id: int, metadata: dict[str, Any], amount: int, currency: str, settings: Settings
) -> bool:
    try:
        days = int(metadata.get("days", settings.subscription_days))
    except (TypeError, ValueError):
        days = settings.subscription_days
    expires = await users.grant_subscription(tg_id, days)
    invite = await _invite_link(bot, settings, days)
    tail = f"\nСсылка на клуб: {invite}" if invite else ""
    await _notify(
        bot, tg_id,
        f"✅ Ты в клубе «Код Алёхиной»!\nДоступ активен до {expires:%d.%m.%Y}.{tail}\n\n"
        "Напиши слово из любого эпизода — выдам бонус, или загляни в бонусы сезона.",
    )
    item = "subscription_3m" if days >= settings.subscription_days_3m else "subscription"
    await _record_sale(tg_id, item, amount, currency)
    return True


async def _fulfill_season(
    bot: Bot, tg_id: int, metadata: dict[str, Any], amount: int, currency: str
) -> bool:
    season_id = metadata.get("season_id", "")
    await users.add_purchased_season(tg_id, season_id)
    season = await catalog.get_season(season_id)
    link = season["archive_link"] if season else ""
    title = season["title"] if season else season_id
    text = (
        f"✅ Оплата прошла! Доступ к сезону «{title}» открыт навсегда.\n"
        f"Архив: {link}\nСохрани ссылку — она не потеряется."
    )
    current = await catalog.current_season()
    if current and current["season_id"] not in (season_id, "all"):
        text += (
            f"\n\n🔥 А прямо сейчас идёт новый сезон «{current['title']}». "
            "Оформи подписку на клуб — получай свежие бонусы и скидку 40% на архивы."
        )
    await _notify(bot, tg_id, text)
    await _record_sale(tg_id, f"season:{season_id}", amount, currency)
    return True


async def _fulfill_workbook(
    bot: Bot, tg_id: int, metadata: dict[str, Any], amount: int, currency: str
) -> bool:
    season_id = metadata.get("season_id", "")
    season = await catalog.get_season(season_id)
    link = season["workbook_link"] if season else ""
    title = season["title"] if season else season_id
    await _notify(
        bot, tg_id,
        f"✅ Оплата прошла! Рабочая тетрадь сезона «{title}» твоя.\n"
        f"Скачать: {link or '—'}\nПриятного внедрения!",
    )
    await _record_sale(tg_id, f"workbook:{season_id}", amount, currency)
    return True


async def _fulfill_all(bot: Bot, tg_id: int, amount: int, currency: str, settings: Settings) -> bool:
    await users.add_purchased_season(tg_id, settings.all_seasons_season_id)
    pack = await catalog.get_season(settings.all_seasons_season_id)
    link = pack["archive_link"] if pack else ""
    await _notify(
        bot, tg_id,
        "✅ Оплата прошла! Доступ ко ВСЕМ сезонам открыт навсегда.\n"
        f"Общий архив: {link or '—'}\nСохрани ссылку — она не потеряется.",
    )
    await _record_sale(tg_id, "all_seasons", amount, currency)
    return True
