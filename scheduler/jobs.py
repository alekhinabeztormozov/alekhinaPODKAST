from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import feedparser
from aiogram import Bot
from loguru import logger
from sqlalchemy import select

from bot.services import notion, seen, subscriptions
from config import Settings
from db.models import ScheduledPost
from db.session import session_scope


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


async def poll_rss(bot: Bot, settings: Settings) -> int:
    if not settings.podster_rss_url or not settings.open_channel_id:
        return 0

    feed = feedparser.parse(settings.podster_rss_url)
    published = 0
    for entry in reversed(feed.entries):
        guid = entry.get("id") or entry.get("link", "")
        if not guid or await seen.is_seen("rss", guid):
            continue
        try:
            await bot.send_message(settings.open_channel_id, announce_text(entry))
            await seen.mark_seen("rss", guid)
            published += 1
        except Exception as exc:
            logger.error("Не отправил анонс {}: {}", guid, exc)
    return published


async def publish_due(bot: Bot) -> int:
    now = datetime.now(UTC)
    published = 0
    async with session_scope() as session:
        result = await session.execute(
            select(ScheduledPost)
            .where(ScheduledPost.status == "pending")
            .where(ScheduledPost.publish_at <= now)
        )
        for post in result.scalars():
            try:
                await bot.send_message(post.target, post.text)
                post.status = "published"
                published += 1
            except Exception as exc:
                post.status = "failed"
                logger.error("Не опубликовал пост {}: {}", post.id, exc)
    return published


async def notify_ready(bot: Bot, settings: Settings) -> int:
    notified = 0
    for episode in await notion.ready_episodes():
        page_id = notion.episode_id(episode)
        if not page_id or await seen.is_seen("notion_ready", page_id):
            continue
        title = notion.episode_title(episode)
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, f"Эпизод «{title}» готов к публикации.")
            except Exception as exc:
                logger.error("Не уведомил админа {}: {}", admin_id, exc)
        await seen.mark_seen("notion_ready", page_id)
        notified += 1
    return notified


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
