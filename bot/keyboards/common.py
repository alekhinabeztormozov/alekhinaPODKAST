from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from media.ambient import get_ambients


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 О подписке", callback_data="club")
    builder.button(text="🔍 Найти в архиве", callback_data="search")
    builder.button(text="🏪 Магазин сезонов", callback_data="shop")
    builder.button(text="🎯 Интенсив", callback_data="intensive")
    builder.adjust(1)
    return builder.as_markup()


def intensive_kb(payment_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if payment_link:
        builder.button(text="✍️ Записаться на интенсив", url=payment_link)
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="menu")
    return builder.as_markup()


def club_offer_kb(price: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Вступить в клуб за {price} ₽", callback_data="club:buy")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def club_active_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Бонусы сезона", callback_data="club:bonuses")
    builder.button(text="🏪 Магазин сезонов", callback_data="shop")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def after_bonus_kb(price: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"🚀 Вступить в клуб за {price} ₽", callback_data="club:buy")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def shop_kb(seasons: list[dict[str, Any]], subscribed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for season in seasons:
        price = season["price_subscriber"] if subscribed else season["price"]
        builder.button(text=f"{season['title']} · {price} ₽", callback_data=f"season:buy:{season['season_id']}")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def season_buy_kb(season_id: str, price: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Купить за {price} ₽", callback_data=f"season:buy:{season_id}")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def search_results_kb(results: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in results:
        if item["kind"] == "episode" and item.get("audio_link"):
            builder.button(text=f"▶ {item['title'][:40]}", url=item["audio_link"])
        elif item["kind"] == "bonus":
            builder.button(text=f"🎁 {item['title'][:40]}", callback_data=f"bonus:{item['bonus_id']}")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def bonuses_list_kb(bonuses: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for bonus in bonuses:
        builder.button(text=f"🎁 {bonus['title'][:45]}", callback_data=f"bonus:{bonus['bonus_id']}")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def owner_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎧 Загрузить эпизод", callback_data="own:audio")
    builder.button(text="📄 Собрать гайд", callback_data="own:guide")
    builder.button(text="🎼 Эмбиенты", callback_data="own:ambients")
    builder.button(text="📊 Статистика", callback_data="own:stats")
    builder.button(text="👀 Клиентский вид", callback_data="own:client")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def back_to_owner() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В пульт", callback_data="own:panel")
    return builder.as_markup()


def ambient_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for track in get_ambients():
        builder.button(text=track.title, callback_data=f"amb:{track.id}")
    builder.button(text="Без фона", callback_data="amb:none")
    builder.button(text="Отмена", callback_data="amb:cancel")
    builder.adjust(1)
    return builder.as_markup()


def ambient_preview_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for track in get_ambients():
        builder.button(text=f"▶ {track.title}", callback_data=f"ambprev:{track.id}")
    builder.button(text="◀️ В пульт", callback_data="own:panel")
    builder.adjust(1)
    return builder.as_markup()
