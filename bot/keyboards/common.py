from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.content import GuideItem, QuizQuestion
from media.ambient import AMBIENTS


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 PDF-бонус", callback_data="pdf")
    builder.button(text="🧠 Тест", callback_data="quiz")
    builder.button(text="🔒 Закрытый канал", callback_data="closed")
    builder.button(text="🛒 Магазин", callback_data="shop")
    builder.adjust(2, 2)
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀ В меню", callback_data="menu")
    return builder.as_markup()


def pdf_skip() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить", callback_data="pdf:skip")
    builder.button(text="◀ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def offer_closed() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒 Закрытый канал", callback_data="closed")
    builder.button(text="◀ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def closed_channel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 День бесплатно", callback_data="closed:trial")
    builder.button(text="💳 Оформить подписку", callback_data="closed:buy")
    builder.button(text="◀ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def shop_kb(items: list[GuideItem]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"{item.title} — {item.price} ₽",
            callback_data=f"shop:buy:{item.id}",
        )
    builder.button(text="◀ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def quiz_kb(question: QuizQuestion, index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option_index, option in enumerate(question.options):
        builder.button(text=option, callback_data=f"quiz:ans:{index}:{option_index}")
    builder.adjust(1)
    return builder.as_markup()


def ambient_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for track in AMBIENTS:
        builder.button(text=track.title, callback_data=f"amb:{track.id}")
    builder.button(text="Без фона", callback_data="amb:none")
    builder.button(text="Отмена", callback_data="amb:cancel")
    builder.adjust(1)
    return builder.as_markup()
