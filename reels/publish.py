from __future__ import annotations

from pathlib import Path

import httpx
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.vk import API_URL
from config import get_settings

UPLOAD_TIMEOUT = 600
TG_CAPTION_LIMIT = 1024


def hashtag_line(scenario: dict) -> str:
    return " ".join(f"#{tag.lstrip('#').replace(' ', '_')}" for tag in scenario.get("hashtags", []))


def post_text(scenario: dict) -> str:
    return "\n\n".join(part for part in (scenario.get("caption", "").strip(), hashtag_line(scenario)) if part)


def bot_link() -> str:
    return f"https://t.me/{get_settings().bot_username}"


async def to_telegram(bot: Bot, video: Path, scenario: dict) -> None:
    channel = get_settings().open_channel_id
    if not channel:
        raise RuntimeError("OPEN_CHANNEL_ID не задан")
    caption = f"{post_text(scenario)}\n\n{bot_link()}"[:TG_CAPTION_LIMIT]
    await bot.send_video(channel, FSInputFile(video), caption=caption, width=1080, height=1920, supports_streaming=True)


async def _vk_save(client: httpx.AsyncClient, scenario: dict) -> str:
    settings = get_settings()
    response = await client.post(API_URL + "video.save", data={
        "access_token": settings.vk_user_token,
        "v": settings.vk_api_version,
        "group_id": settings.vk_group_id,
        "name": scenario.get("title", "Новый ролик")[:120],
        "description": f"{post_text(scenario)}\n\n{bot_link()}",
        "wallpost": 1,
    })
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"VK video.save: {data['error'].get('error_msg')}")
    return data["response"]["upload_url"]


async def to_vk(video: Path, scenario: dict) -> None:
    settings = get_settings()
    if not settings.vk_user_token or not settings.vk_group_id:
        raise RuntimeError("VK_USER_TOKEN или VK_GROUP_ID не заданы")
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
        upload_url = await _vk_save(client, scenario)
        with video.open("rb") as handle:
            response = await client.post(upload_url, files={"video_file": (video.name, handle, "video/mp4")})
    if response.status_code != 200 or "error" in response.text[:200]:
        raise RuntimeError(f"VK загрузка видео {response.status_code}: {response.text[:200]}")


def instagram_kb(reel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Выложила в Instagram", callback_data=f"reel:ig:{reel_id}")
    return builder.as_markup()


async def to_instagram_owner(bot: Bot, video: Path, scenario: dict, reel_id: int) -> None:
    for admin_id in get_settings().admin_ids:
        await bot.send_video(
            admin_id, FSInputFile(video), width=1080, height=1920,
            caption=f"Ролик для Instagram: {scenario.get('title', '')}\nПодпись ниже, скопируйте целиком",
        )
        await bot.send_message(admin_id, post_text(scenario), parse_mode=None, reply_markup=instagram_kb(reel_id))
