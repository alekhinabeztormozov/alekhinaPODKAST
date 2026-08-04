from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from loguru import logger

from config import get_settings

READY_STATUS = "Контент готов"


class NotionNotConfigured(RuntimeError):
    pass


@lru_cache
def _client() -> Any:
    settings = get_settings()
    if not settings.notion_token:
        raise NotionNotConfigured("NOTION_TOKEN не задан")
    from notion_client import Client
    return Client(auth=settings.notion_token)


def _query_ready_sync() -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.notion_db_episodes:
        raise NotionNotConfigured("NOTION_DB_EPISODES не задан")
    response = _client().databases.query(
        database_id=settings.notion_db_episodes,
        filter={"property": "Статус", "select": {"equals": READY_STATUS}},
    )
    return response.get("results", [])


async def ready_episodes() -> list[dict[str, Any]]:
    try:
        return await asyncio.to_thread(_query_ready_sync)
    except NotionNotConfigured:
        logger.warning("Notion не настроен — возвращаю пусто")
        return []
    except Exception as exc:
        logger.error("Notion запрос упал: {}", exc)
        return []
