from __future__ import annotations

from aiogram import Bot
from aiogram.types import LabeledPrice

from bot.content import GuideItem
from config import Settings


def _amount(value: int, currency: str) -> int:
    return value if currency == "XTR" else value * 100


def subscription_prices(settings: Settings) -> list[LabeledPrice]:
    amount = _amount(settings.subscription_price, settings.payment_currency)
    return [LabeledPrice(label="Подписка на месяц", amount=amount)]


def item_prices(item: GuideItem, settings: Settings) -> list[LabeledPrice]:
    return [LabeledPrice(label=item.title, amount=_amount(item.price, settings.payment_currency))]


async def send_subscription_invoice(bot: Bot, chat_id: int, settings: Settings) -> None:
    await bot.send_invoice(
        chat_id=chat_id,
        title="Подписка на закрытый канал",
        description="Детальные разборы, аудиобонусы и инструменты на месяц.",
        payload="sub",
        provider_token=settings.payment_provider_token,
        currency=settings.payment_currency,
        prices=subscription_prices(settings),
    )


async def send_item_invoice(bot: Bot, chat_id: int, item: GuideItem, settings: Settings) -> None:
    await bot.send_invoice(
        chat_id=chat_id,
        title=item.title,
        description=f"PDF-гайд: {item.title}",
        payload=f"item:{item.id}",
        provider_token=settings.payment_provider_token,
        currency=settings.payment_currency,
        prices=item_prices(item, settings),
    )
