from __future__ import annotations

import re
from typing import Any

from aiogram import Bot
from loguru import logger
from sqlalchemy import select

from bot.services import notion, seen, vk
from config import Settings
from db.models import Bonus, Episode, Season
from db.session import DatabaseNotConfigured, session_scope

# Строки, заведённые из Notion: id страницы — uuid, id бонуса — nb_ + тот же uuid без дефисов.
# Всё остальное (sweet_nutella, bonus_nutella) заведено руками через /add_* и не трогается.
_NOTION_EPISODE_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_NOTION_BONUS_ID = re.compile(r"^nb_[0-9a-f]{32}$")



async def _season_index(session: Any) -> tuple[dict[str, str], str]:
    """Сезоны по слагу и по названию (регистр не важен) + текущий сезон как запасной."""
    rows = (await session.execute(select(Season))).scalars().all()
    index: dict[str, str] = {}
    fallback = ""
    for row in rows:
        index[row.season_id.strip().casefold()] = row.season_id
        if row.title:
            index[row.title.strip().casefold()] = row.season_id
        if row.is_current:
            fallback = row.season_id
    return index, fallback


def _resolve_season(raw: str, index: dict[str, str], fallback: str, title: str,
                    problems: list[str]) -> str:
    """Notion отдаёт имя опции «Сезон» — приводим его к season_id из базы."""
    key = raw.strip().casefold()
    if not key:
        if fallback:
            return fallback
        problems.append(f"«{title}»: сезон не указан, текущего сезона в базе нет")
        return ""
    if key in index:
        return index[key]
    known = ", ".join(sorted({v for v in index.values()})) or "нет ни одного"
    problems.append(f"«{title}»: сезон «{raw}» не найден в базе (есть: {known})")
    return raw.strip()


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


async def _prune_missing(session: Any, live_episodes: set[str], live_bonuses: set[str]) -> list[str]:
    """Убирает из базы то, что раньше пришло из Notion, а теперь там пропало.

    Вызывается только когда Notion реально отдал страницы: catalog_pages() при любой
    ошибке возвращает пустой список, и на пустом ответе синк выходит раньше.
    """
    removed: list[str] = []
    for row in (await session.execute(select(Episode))).scalars().all():
        if _NOTION_EPISODE_ID.match(row.episode_id) and row.episode_id not in live_episodes:
            removed.append(f"эпизод «{row.title}» убран: его больше нет в Notion")
            await session.delete(row)
    for row in (await session.execute(select(Bonus))).scalars().all():
        if _NOTION_BONUS_ID.match(row.bonus_id) and row.bonus_id not in live_bonuses:
            removed.append(f"бонус «{row.title}» убран: его больше нет в Notion")
            await session.delete(row)
    return removed


async def _keyword_owners(session: Any) -> dict[str, str]:
    """Ключевое слово (регистр не важен) → bonus_id, который его уже занял."""
    rows = (await session.execute(select(Bonus))).scalars().all()
    return {row.keyword.strip().casefold(): row.bonus_id for row in rows if row.keyword.strip()}


def _skip_reason(data: dict[str, Any]) -> str:
    """Почему страница не попала ни в эпизоды, ни в бонусы."""
    missing = []
    if not data["audio_link"] and not data["tags"]:
        missing.append("нет «Ссылки на аудио» и «Тегов»")
    if not data["keyword"]:
        missing.append("нет «Ключевого слова» для бонуса")
    elif not data["pdf_link"] and not data["bonus_audio"]:
        missing.append("нет «PDF-бонуса» и «Аудио-бонуса»")
    return f"«{data['title']}» пропущен: " + "; ".join(missing)


async def sync_catalog() -> dict[str, Any]:
    pages = await notion.catalog_pages()
    episodes = bonuses = skipped = 0
    problems: list[str] = []
    if pages is None:
        logger.warning("Notion не ответил — синк пропущен, базу не трогаю")
        return {
            "episodes": 0,
            "bonuses": 0,
            "skipped": 0,
            "problems": ["Notion не ответил — ничего не менял, жду следующего прогона"],
        }
    if not pages:
        logger.info("Notion синк: строк со статусом {} нет", notion.CATALOG_STATUSES)
    try:
        async with session_scope() as session:
            index, fallback = await _season_index(session)
            records = [notion.extract_catalog(page) for page in pages]
            # Страница есть в Notion — что бы с ней дальше ни случилось, её строки не удаляем.
            problems.extend(await _prune_missing(
                session,
                {d["episode_id"] for d in records},
                {d["bonus_id"] for d in records},
            ))
            keyword_owner = await _keyword_owners(session)
            for data in records:
                title = data["title"]
                if not data["has_title"]:
                    skipped += 1
                    problems.append(
                        f"строка {data['episode_id'][:8]}… пропущена: не заполнено «Название»"
                    )
                    continue
                data["season_id"] = _resolve_season(
                    data["season_id"], index, fallback, title, problems
                )
                touched = False
                if data["audio_link"] or data["tags"]:
                    await _upsert_episode(session, data)
                    episodes += 1
                    touched = True
                key = data["keyword"].strip().casefold()
                if key and (data["pdf_link"] or data["bonus_audio"]):
                    owner = keyword_owner.get(key)
                    if owner and owner != data["bonus_id"]:
                        problems.append(
                            f"«{title}»: ключевое слово «{data['keyword']}» уже занято другим "
                            f"бонусом, этот бонус не завёл — слово должно быть уникальным"
                        )
                    else:
                        await _upsert_bonus(session, data)
                        keyword_owner[key] = data["bonus_id"]
                        bonuses += 1
                        touched = True
                if not touched:
                    skipped += 1
                    problems.append(_skip_reason(data))
    except DatabaseNotConfigured:
        logger.warning("БД не настроена — синк Notion пропущен")
        return {"episodes": 0, "bonuses": 0, "skipped": len(pages), "problems": ["БД не настроена"]}
    logger.info("Notion синк: эпизоды={} бонусы={} пропущено={}", episodes, bonuses, skipped)
    for problem in problems:
        logger.warning("Notion синк: {}", problem)
    return {
        "episodes": episodes,
        "bonuses": bonuses,
        "skipped": skipped,
        "problems": problems,
    }


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


async def publish_vk_posts() -> int:
    if not vk.is_configured():
        return 0
    published = 0
    for page in await notion.published_pages():
        page_id = notion.episode_id(page)
        text = notion.vk_post(page)
        if not page_id or not text or await seen.is_seen("vk_post", page_id):
            continue
        try:
            await vk.post_to_wall(text)
            await seen.mark_seen("vk_post", page_id)
            published += 1
        except Exception as exc:
            logger.error("Не опубликовал пост VK {}: {}", page_id, exc)
    return published
