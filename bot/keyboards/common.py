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


def client_preview_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 О подписке", callback_data="club")
    builder.button(text="🔍 Найти в архиве", callback_data="search")
    builder.button(text="🏪 Магазин сезонов", callback_data="shop")
    builder.button(text="🎯 Интенсив", callback_data="intensive")
    builder.button(text="◀️ В пульт", callback_data="own:panel")
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


def club_offer_kb(price: int, price3: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Месяц — {price} ₽", callback_data="club:buy:1")
    builder.button(text=f"💎 3 месяца — {price3} ₽", callback_data="club:buy:3")
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
    builder.button(text=f"🚀 Вступить в клуб за {price} ₽", callback_data="club")
    builder.button(text="🎁 Все бонусы этого сезона", callback_data="club:bonuses")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def voice_demo_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Забрать 24 часа бесплатно", callback_data="club:trial")
    builder.button(text="🚀 О подписке", callback_data="club")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def shop_kb(all_seasons_price: int, subscribed: bool, has_workbooks: bool, has_pack: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Купить сезон", callback_data="shop:seasons")
    if has_workbooks:
        builder.button(text="📓 Рабочая тетрадь", callback_data="shop:workbooks")
    if has_pack:
        builder.button(text=f"🎁 Все сезоны · {all_seasons_price} ₽", callback_data="shop:all")
    if not subscribed:
        builder.button(text="🚀 Вступить в клуб (−40%)", callback_data="club")
    builder.button(text="◀️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def seasons_list_kb(seasons: list[dict[str, Any]], subscribed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for season in seasons:
        price = season["price_subscriber"] if subscribed else season["price"]
        builder.button(text=f"{season['title']} · {price} ₽", callback_data=f"season:show:{season['season_id']}")
    builder.button(text="◀️ В магазин", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def workbooks_list_kb(seasons: list[dict[str, Any]], subscribed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    price = _wb_price(subscribed)
    for season in seasons:
        builder.button(text=f"{season['title']} · {price} ₽", callback_data=f"wb:show:{season['season_id']}")
    builder.button(text="◀️ В магазин", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def _wb_price(subscribed: bool) -> int:
    from config import get_settings

    settings = get_settings()
    return settings.workbook_price_subscriber if subscribed else settings.workbook_price


def season_offer_kb(season_id: str, price: int, subscribed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Купить за {price} ₽", callback_data=f"season:buy:{season_id}")
    if not subscribed:
        builder.button(text="🚀 Вступить в клуб (−40%)", callback_data="club")
    builder.button(text="◀️ В магазин", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def workbook_offer_kb(season_id: str, price: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Купить за {price} ₽", callback_data=f"wb:buy:{season_id}")
    builder.button(text="◀️ В магазин", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def all_seasons_kb(price: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Купить за {price} ₽", callback_data="all:buy")
    builder.button(text="◀️ В магазин", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def back_to_shop() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В магазин", callback_data="shop")
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
        builder.button(text=track.title, callback_data=f"amb:{track.code}")
    builder.button(text="Без фона", callback_data="amb:none")
    builder.button(text="Отмена", callback_data="amb:cancel")
    builder.adjust(1)
    return builder.as_markup()


def ambient_preview_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for track in get_ambients():
        builder.button(text=f"▶ {track.title}", callback_data=f"ambprev:{track.code}")
    builder.button(text="◀️ В пульт", callback_data="own:panel")
    builder.adjust(1)
    return builder.as_markup()
