from __future__ import annotations

from typing import Any

import feedparser
from aiogram import Bot
from loguru import logger

from bot.services import subscriptions
from config import Settings


def announce_text(entry: dict[str, Any]) -> str:
    title = entry.get("title", "Новый эпизод")
    summary = entry.get("summary", "").strip()
    link = entry.get("link", "")
    parts = [f"<b>{title}</b>"]
    if summary:
        parts.append(summary[:400])
    if link:
        parts.append(f"Слушать: {link}")
    parts.append("Забери PDF-бонус и разборы в боте.")
    return "\n\n".join(parts)


async def poll_rss(bot: Bot, settings: Settings, seen: set[str]) -> int:
    if not settings.podster_rss_url or not settings.open_channel_id:
        return 0

    feed = feedparser.parse(settings.podster_rss_url)
    published = 0
    for entry in reversed(feed.entries):
        guid = entry.get("id") or entry.get("link", "")
        if not guid or guid in seen:
            continue
        try:
            await bot.send_message(settings.open_channel_id, announce_text(entry))
            seen.add(guid)
            published += 1
        except Exception as exc:
            logger.error("Не отправил анонс {}: {}", guid, exc)
    return published


async def revoke_expired(bot: Bot, settings: Settings) -> int:
    revoked = 0
    for tg_id in await subscriptions.expired():
        try:
            if settings.closed_channel_id:
                await bot.ban_chat_member(settings.closed_channel_id, tg_id)
                await bot.unban_chat_member(settings.closed_channel_id, tg_id)
            await subscriptions.mark_expired(tg_id)
            revoked += 1
        except Exception as exc:
            logger.error("Не отозвал доступ у {}: {}", tg_id, exc)
    return revoked
