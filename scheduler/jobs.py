from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import feedparser
from aiogram import Bot
from loguru import logger
from sqlalchemy import select

from bot.content import FINALE_ANNOUNCE, SEASON_ENDING, SUB_EXPIRED
from bot.services import catalog, notion, notion_sync, seen, users
from config import Settings
from db.models import ScheduledPost, Season
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
    parts.append("Напиши ключевое слово из эпизода в бота — заберёшь бонус.")
    return "\n\n".join(parts)


async def _broadcast(bot: Bot, ids: list[int], text: str) -> int:
    sent = 0
    for tg_id in ids:
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except Exception as exc:
            logger.error("Рассылка {} не дошла: {}", tg_id, exc)
    return sent


async def pull_notion(bot: Bot, settings: Settings) -> int:
    await notion_sync.sync_catalog()
    published = await notion_sync.publish_ready_posts(bot, settings)
    published += await notion_sync.publish_vk_posts()
    return published


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
    for tg_id in await users.expired_subscribers():
        try:
            await users.drop_subscription(tg_id)
            if settings.closed_channel_id:
                await bot.ban_chat_member(settings.closed_channel_id, tg_id)
                await bot.unban_chat_member(settings.closed_channel_id, tg_id)
            await bot.send_message(tg_id, SUB_EXPIRED)
            revoked += 1
        except Exception as exc:
            logger.error("Не отозвал доступ у {}: {}", tg_id, exc)
    return revoked


async def _seasons_ending(target: date) -> list[Season]:
    async with session_scope() as session:
        result = await session.execute(
            select(Season).where(Season.is_current.is_(True)).where(Season.end_date == target)
        )
        return list(result.scalars().all())


async def notify_season_ending(bot: Bot, settings: Settings) -> int:
    target = date.today() + timedelta(days=3)
    seasons = await _seasons_ending(target)
    notified = 0
    for season in seasons:
        if await seen.is_seen("season_ending", season.season_id):
            continue
        await _broadcast(bot, await users.subscriber_ids(), SEASON_ENDING.format(title=season.title))
        await seen.mark_seen("season_ending", season.season_id)
        notified += 1
    return notified


async def notify_finale(bot: Bot, settings: Settings) -> int:
    today = date.today()
    async with session_scope() as session:
        result = await session.execute(select(Season).where(Season.end_date == today))
        seasons = list(result.scalars().all())
    notified = 0
    for season in seasons:
        if await seen.is_seen("finale", season.season_id):
            continue
        product = await catalog.active_main_product(season.season_id)
        if product is None:
            continue
        text = FINALE_ANNOUNCE.format(title=product["title"], description=product["description"])
        await _broadcast(bot, await users.all_user_ids(), text)
        await seen.mark_seen("finale", season.season_id)
        notified += 1
    return notified
