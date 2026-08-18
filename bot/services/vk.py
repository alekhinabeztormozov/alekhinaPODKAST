from __future__ import annotations

import hmac
import random
from typing import Any

import httpx
from loguru import logger

from config import get_settings

API_URL = "https://api.vk.com/method/"


class VkNotConfigured(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(get_settings().vk_group_token)


def check_secret(secret: str | None) -> bool:
    expected = get_settings().vk_secret
    if not expected:
        return True
    return hmac.compare_digest(secret or "", expected)


async def _call(method: str, params: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.vk_group_token:
        raise VkNotConfigured("VK_GROUP_TOKEN не задан")
    payload = {
        **params,
        "access_token": settings.vk_group_token,
        "v": settings.vk_api_version,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(API_URL + method, data=payload)
        response.raise_for_status()
        data = response.json()
    if "error" in data:
        message = data["error"].get("error_msg", "unknown")
        logger.error("VK {} error: {}", method, message)
        raise RuntimeError(f"VK {method}: {message}")
    return data.get("response", {})


async def send_message(peer_id: int, text: str) -> None:
    await _call(
        "messages.send",
        {"peer_id": peer_id, "message": text, "random_id": random.randint(1, 2_000_000_000)},
    )


async def post_to_wall(text: str) -> None:
    settings = get_settings()
    if not settings.vk_group_id:
        raise VkNotConfigured("VK_GROUP_ID не задан")
    await _call(
        "wall.post",
        {"owner_id": -settings.vk_group_id, "from_group": 1, "message": text},
    )
