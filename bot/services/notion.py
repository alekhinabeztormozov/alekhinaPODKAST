from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from loguru import logger

from config import get_settings

STATUSES = ["Идея", "Сценарий", "Запись", "Монтаж", "Контент готов", "Опубликован"]
READY_STATUS = "Контент готов"

EPISODES_SCHEMA: dict[str, dict[str, Any]] = {
    "Название": {"title": {}},
    "Статус": {"select": {"options": [{"name": name} for name in STATUSES]}},
    "Сезон": {"select": {}},
    "Бренд": {"select": {}},
    "Дата выхода": {"date": {}},
    "Ссылка на аудио": {"url": {}},
    "Ссылка на расшифровку": {"url": {}},
    "Пост для Telegram": {"rich_text": {}},
    "Пост для VK": {"rich_text": {}},
    "Текст для Дзен": {"rich_text": {}},
    "PDF-бонус": {"url": {}},
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


def _query_ready_sync() -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.notion_db_episodes:
        raise NotionNotConfigured("NOTION_DB_EPISODES не задан")
    response = _client().databases.query(
        database_id=settings.notion_db_episodes,
        filter={"property": "Статус", "select": {"equals": READY_STATUS}},
    )
    return response.get("results", [])


def episode_id(page: dict[str, Any]) -> str:
    return page.get("id", "")


def episode_title(page: dict[str, Any]) -> str:
    parts = page.get("properties", {}).get("Название", {}).get("title", [])
    return "".join(part.get("plain_text", "") for part in parts) or "Без названия"


def episode_status(page: dict[str, Any]) -> str:
    select = page.get("properties", {}).get("Статус", {}).get("select")
    return select.get("name", "") if select else ""


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
