from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from loguru import logger

from config import get_settings

STATUSES = ["Идея", "Сценарий", "Запись", "Монтаж", "Контент готов", "Опубликован"]
READY_STATUS = "Контент готов"
PUBLISHED_STATUS = "Опубликован"
CATALOG_STATUSES = (READY_STATUS, PUBLISHED_STATUS)

EPISODES_SCHEMA: dict[str, dict[str, Any]] = {
    "Название": {"title": {}},
    "Статус": {"select": {"options": [{"name": name} for name in STATUSES]}},
    "Сезон": {"select": {}},
    "Бренд": {"select": {}},
    "Дата выхода": {"date": {}},
    "Ссылка на аудио": {"url": {}},
    "Ссылка на расшифровку": {"url": {}},
    "Ключевое слово": {"rich_text": {}},
    "Теги": {"rich_text": {}},
    "Название бонуса": {"rich_text": {}},
    "PDF-бонус": {"url": {}},
    "Аудио-бонус": {"url": {}},
    "Пост для Telegram": {"rich_text": {}},
    "Пост для VK": {"rich_text": {}},
    "Текст для Дзен": {"rich_text": {}},
    "Темы для клипов": {"rich_text": {}},
}


class NotionNotConfigured(RuntimeError):
    pass


@lru_cache
def _client() -> Any:
    settings = get_settings()
    if not settings.notion_token:
        raise NotionNotConfigured("NOTION_TOKEN не задан")
    from notion_client import Client

    return Client(auth=settings.notion_token)


def _create_episodes_db_sync(parent_page_id: str) -> str:
    response = _client().databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Эпизоды"}}],
        properties=EPISODES_SCHEMA,
    )
    return response["id"]


def _query_status_sync(statuses: tuple[str, ...]) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.notion_db_episodes:
        raise NotionNotConfigured("NOTION_DB_EPISODES не задан")
    client = _client()
    conditions = [{"property": "Статус", "select": {"equals": status}} for status in statuses]
    filter_ = conditions[0] if len(conditions) == 1 else {"or": conditions}
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {"database_id": settings.notion_db_episodes, "filter": filter_}
        if cursor:
            payload["start_cursor"] = cursor
        response = client.databases.query(**payload)
        results.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return results


def _query_ready_sync() -> list[dict[str, Any]]:
    return _query_status_sync((READY_STATUS,))


def _prop(page: dict[str, Any], name: str) -> dict[str, Any]:
    return page.get("properties", {}).get(name, {})


def _rich(page: dict[str, Any], name: str) -> str:
    prop = _prop(page, name)
    parts = prop.get("rich_text") or prop.get("title") or []
    return "".join(part.get("plain_text", "") for part in parts).strip()


def _url(page: dict[str, Any], name: str) -> str:
    return (_prop(page, name).get("url") or "").strip()


def _select(page: dict[str, Any], name: str) -> str:
    select = _prop(page, name).get("select")
    return select.get("name", "").strip() if select else ""


def episode_id(page: dict[str, Any]) -> str:
    return page.get("id", "")


def episode_title(page: dict[str, Any]) -> str:
    return _rich(page, "Название") or "Без названия"


def episode_status(page: dict[str, Any]) -> str:
    return _select(page, "Статус")


def telegram_post(page: dict[str, Any]) -> str:
    return _rich(page, "Пост для Telegram")


def extract_catalog(page: dict[str, Any]) -> dict[str, Any]:
    page_id = page.get("id", "")
    slug = page_id.replace("-", "")
    tags = [t.strip() for t in _rich(page, "Теги").split(",") if t.strip()]
    title = episode_title(page)
    return {
        "episode_id": page_id,
        "season_id": _select(page, "Сезон"),
        "title": title,
        "audio_link": _url(page, "Ссылка на аудио"),
        "tags": tags,
        "keyword": _rich(page, "Ключевое слово"),
        "bonus_id": f"nb_{slug}"[:64],
        "bonus_title": _rich(page, "Название бонуса") or title,
        "pdf_link": _url(page, "PDF-бонус"),
        "bonus_audio": _url(page, "Аудио-бонус"),
    }


async def create_episodes_db(parent_page_id: str) -> str | None:
    try:
        return await asyncio.to_thread(_create_episodes_db_sync, parent_page_id)
    except NotionNotConfigured:
        logger.warning("Notion не настроен — базу не создаю")
        return None
    except Exception as exc:
        logger.error("Notion создание базы упало: {}", exc)
        return None


async def ready_episodes() -> list[dict[str, Any]]:
    try:
        return await asyncio.to_thread(_query_ready_sync)
    except NotionNotConfigured:
        logger.warning("Notion не настроен — возвращаю пусто")
        return []
    except Exception as exc:
        logger.error("Notion запрос упал: {}", exc)
        return []


async def _query_status(statuses: tuple[str, ...]) -> list[dict[str, Any]]:
    try:
        return await asyncio.to_thread(_query_status_sync, statuses)
    except NotionNotConfigured:
        logger.warning("Notion не настроен — возвращаю пусто")
        return []
    except Exception as exc:
        logger.error("Notion запрос упал: {}", exc)
        return []


async def catalog_pages() -> list[dict[str, Any]]:
    return await _query_status(CATALOG_STATUSES)


async def published_pages() -> list[dict[str, Any]]:
    return await _query_status((PUBLISHED_STATUS,))
