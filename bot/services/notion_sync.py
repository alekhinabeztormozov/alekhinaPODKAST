from __future__ import annotations

from typing import Any

from aiogram import Bot
from loguru import logger
from sqlalchemy import select

from bot.services import notion, seen
from config import Settings
from db.models import Bonus, Episode
from db.session import DatabaseNotConfigured, session_scope


async def _upsert_episode(session: Any, data: dict[str, Any]) -> None:
    row = await session.scalar(select(Episode).where(Episode.episode_id == data["episode_id"]))
    values = dict(
        season_id=data["season_id"],
        title=data["title"],
        audio_link=data["audio_link"],
        tags=data["tags"],
    )
    if row is None:
        session.add(Episode(episode_id=data["episode_id"], **values))
        return
    for field, value in values.items():
        setattr(row, field, value)


async def _upsert_bonus(session: Any, data: dict[str, Any]) -> None:
    row = await session.scalar(select(Bonus).where(Bonus.bonus_id == data["bonus_id"]))
    values = dict(
        season_id=data["season_id"],
        keyword=data["keyword"],
        title=data["bonus_title"],
        pdf_link=data["pdf_link"],
        audio_link=data["bonus_audio"],
        tags=data["tags"],
    )
    if row is None:
        session.add(Bonus(bonus_id=data["bonus_id"], **values))
        return
    for field, value in values.items():
        setattr(row, field, value)


async def sync_catalog() -> dict[str, int]:
    pages = await notion.catalog_pages()
    episodes = bonuses = skipped = 0
    if not pages:
        return {"episodes": 0, "bonuses": 0, "skipped": 0}
    try:
        async with session_scope() as session:
            for page in pages:
                data = notion.extract_catalog(page)
                touched = False
                if data["audio_link"] or data["tags"]:
                    await _upsert_episode(session, data)
                    episodes += 1
                    touched = True
                if data["keyword"] and (data["pdf_link"] or data["bonus_audio"]):
                    await _upsert_bonus(session, data)
                    bonuses += 1
                    touched = True
                if not touched:
                    skipped += 1
    except DatabaseNotConfigured:
        logger.warning("БД не настроена — синк Notion пропущен")
        return {"episodes": 0, "bonuses": 0, "skipped": len(pages)}
    logger.info("Notion синк: эпизоды={} бонусы={} пропущено={}", episodes, bonuses, skipped)
    return {"episodes": episodes, "bonuses": bonuses, "skipped": skipped}


async def publish_ready_posts(bot: Bot, settings: Settings) -> int:
    if not settings.open_channel_id:
        return 0
    published = 0
    for page in await notion.published_pages():
        page_id = notion.episode_id(page)
        text = notion.telegram_post(page)
        if not page_id or not text or await seen.is_seen("notion_post", page_id):
            continue
        try:
            await bot.send_message(settings.open_channel_id, text)
            await seen.mark_seen("notion_post", page_id)
            published += 1
        except Exception as exc:
            logger.error("Не опубликовал пост Notion {}: {}", page_id, exc)
    return published
