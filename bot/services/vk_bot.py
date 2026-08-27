from __future__ import annotations

import json

from loguru import logger

from bot.services import catalog, contacts, vk
from config import get_settings


def _tg_link() -> str:
    return f"https://t.me/{get_settings().bot_username}"


def main_keyboard() -> str:
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [{"action": {"type": "text", "label": "🔍 Найти в архиве",
                         "payload": json.dumps({"cmd": "search"})}}],
            [{"action": {"type": "text", "label": "🚀 Клуб и подписка",
                         "payload": json.dumps({"cmd": "club"})}}],
            [{"action": {"type": "open_link", "link": _tg_link(), "label": "Перейти в Телеграм"}}],
        ],
    }
    return json.dumps(keyboard, ensure_ascii=False)


def _welcome_text() -> str:
    return (
        "👋 Привет! Это вселенная нейромаркетинга «Алёхина без тормозов».\n\n"
        "Напиши ключевое слово из эпизода — пришлю бонус (PDF + голосовой разбор). "
        "Или нажми «Найти в архиве» и введи слово: кофе, кола, упаковка…\n\n"
        f"Бонусы к каждому выпуску, голосовые разборы и клуб с подпиской — в Телеграме: {_tg_link()}"
    )


def _club_text() -> str:
    return (
        "🚀 Клуб «Код Алёхиной» — бонусы к каждому эпизоду, голосовые разборы, эксклюзив "
        "и скидки на архивы сезонов.\n\n"
        f"Оформить подписку и забрать бонусы: {_tg_link()}"
    )


def _search_prompt() -> str:
    return "🔍 Напиши слово — поищу в архиве эпизоды и бонусы. Например: кофе, шоколад, кола, упаковка."


def _bonus_text(bonus: dict) -> str:
    return (
        "🎁 Держи бонус к этому эпизоду!\n"
        f"PDF-расшифровка: {bonus['pdf_link'] or '—'}\n"
        f"Голосовой разбор: {bonus['audio_link'] or '—'}\n\n"
        "Хочешь такие бонусы к каждому выпуску, голосовые разборы и клуб с подпиской — "
        f"всё в Телеграме: {_tg_link()}"
    )


def _results_text(query: str, results: list[dict]) -> str:
    lines = [f"🔍 Нашёл по запросу «{query}»:", ""]
    for index, item in enumerate(results, 1):
        kind = "эпизод" if item["kind"] == "episode" else "бонус"
        lines.append(f"{index}. {item['title']} — {kind}")
    lines.append("")
    lines.append(f"Забрать бонусы и оформить подписку — в Телеграме: {_tg_link()}")
    return "\n".join(lines)


def _none_text() -> str:
    return (
        "Ничего не нашёл по запросу. Попробуй другие слова: кофе, шоколад, кола, упаковка…\n\n"
        f"А все бонусы и подписка — в Телеграме: {_tg_link()}"
    )


def _command(payload: str, text: str) -> str:
    if payload:
        try:
            data = json.loads(payload)
            cmd = data.get("cmd") or data.get("command") or ""
            if cmd == "start":
                return "start"
            if cmd:
                return cmd
        except (ValueError, TypeError, AttributeError):
            pass
    low = text.strip().lower()
    if low in {"начать", "start", "старт", "привет", "меню"}:
        return "start"
    if low in {"найти в архиве", "поиск", "найти"}:
        return "search"
    if "клуб" in low or "подписк" in low:
        return "club"
    return ""


async def handle_incoming(
    text: str, peer_id: int, from_id: int, payload: str = "", name: str = ""
) -> None:
    query = (text or "").strip()
    command = _command(payload, query)
    kb = main_keyboard()
    try:
        if command == "start":
            await vk.send_message(peer_id, _welcome_text(), kb)
            return
        if command == "club":
            await vk.send_message(peer_id, _club_text(), kb)
            return
        if command == "search":
            await vk.send_message(peer_id, _search_prompt(), kb)
            return
        if not query:
            await vk.send_message(peer_id, _welcome_text(), kb)
            return

        await contacts.record(from_id, name=name, source="vk")
        bonus = await catalog.bonus_by_keyword(query)
        if bonus is not None:
            await vk.send_message(peer_id, _bonus_text(bonus), kb)
            return
        results = await catalog.search(query)
        message = _results_text(query, results) if results else _none_text()
        await vk.send_message(peer_id, message, kb)
    except vk.VkNotConfigured:
        logger.warning("VK не настроен — входящее сообщение пропущено")
    except Exception as exc:
        logger.error("VK обработка входящего упала: {}", exc)
