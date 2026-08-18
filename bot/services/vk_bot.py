from __future__ import annotations

from loguru import logger

from bot.services import catalog, contacts, vk
from config import get_settings


def _tg_link() -> str:
    return f"https://t.me/{get_settings().bot_username}"


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


async def handle_incoming(text: str, peer_id: int, from_id: int, name: str = "") -> None:
    query = (text or "").strip()
    if not query:
        return
    try:
        await contacts.record(from_id, name=name, source="vk")
        bonus = await catalog.bonus_by_keyword(query)
        if bonus is not None:
            await vk.send_message(peer_id, _bonus_text(bonus))
            return
        results = await catalog.search(query)
        await vk.send_message(peer_id, _results_text(query, results) if results else _none_text())
    except vk.VkNotConfigured:
        logger.warning("VK не настроен — входящее сообщение пропущено")
    except Exception as exc:
        logger.error("VK обработка входящего упала: {}", exc)
