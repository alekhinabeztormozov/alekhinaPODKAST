from __future__ import annotations

from pathlib import Path

import httpx
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
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


async def to_vk(video: Path, scenario: dict) -> None:
    settings = get_settings()
    if not settings.vk_user_token or not settings.vk_group_id:
        raise RuntimeError("VK_USER_TOKEN или VK_GROUP_ID не заданы")
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
        saved = await _vk_method(client, "video.save", {
            "group_id": settings.vk_group_id,
            "name": scenario.get("title", "Новый ролик")[:120],
            "description": f"{post_text(scenario)}\n\n{bot_link()}",
            "wallpost": 1,
        })
        upload_url = saved["upload_url"]
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


ALBUM_LIMIT = 10


def slide_paths(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.png"))[:ALBUM_LIMIT]


def album(slides: list[Path], caption: str = "") -> list[InputMediaPhoto]:
    return [
        InputMediaPhoto(media=FSInputFile(path), caption=caption[:TG_CAPTION_LIMIT] if index == 0 and caption else None)
        for index, path in enumerate(slides)
    ]


async def album_to_telegram(bot: Bot, folder: Path, scenario: dict) -> None:
    channel = get_settings().open_channel_id
    if not channel:
        raise RuntimeError("OPEN_CHANNEL_ID не задан")
    await bot.send_media_group(channel, album(slide_paths(folder), f"{post_text(scenario)}\n\n{bot_link()}"))


async def _vk_method(client: httpx.AsyncClient, method: str, params: dict) -> dict:
    settings = get_settings()
    response = await client.post(API_URL + method, data={
        **params, "access_token": settings.vk_user_token, "v": settings.vk_api_version,
    })
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"VK {method}: {data['error'].get('error_msg')}")
    return data["response"]


async def _vk_upload_photo(client: httpx.AsyncClient, path: Path) -> str:
    group_id = get_settings().vk_group_id
    server = await _vk_method(client, "photos.getWallUploadServer", {"group_id": group_id})
    with path.open("rb") as handle:
        uploaded = (await client.post(server["upload_url"], files={"photo": (path.name, handle, "image/png")})).json()
    saved = await _vk_method(client, "photos.saveWallPhoto", {
        "group_id": group_id, "photo": uploaded["photo"], "server": uploaded["server"], "hash": uploaded["hash"],
    })
    return f"photo{saved[0]['owner_id']}_{saved[0]['id']}"


async def album_to_vk(folder: Path, scenario: dict) -> None:
    settings = get_settings()
    if not settings.vk_user_token or not settings.vk_group_id:
        raise RuntimeError("VK_USER_TOKEN или VK_GROUP_ID не заданы")
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
        attachments = [await _vk_upload_photo(client, path) for path in slide_paths(folder)]
        await _vk_method(client, "wall.post", {
            "owner_id": -settings.vk_group_id, "from_group": 1,
            "message": f"{post_text(scenario)}\n\n{bot_link()}", "attachments": ",".join(attachments),
        })


async def album_to_instagram_owner(bot: Bot, folder: Path, scenario: dict, reel_id: int) -> None:
    for admin_id in get_settings().admin_ids:
        caption = f"Карусель для Instagram: {scenario.get('title', '')}"
        await bot.send_media_group(admin_id, album(slide_paths(folder), caption))
        await bot.send_message(admin_id, post_text(scenario), parse_mode=None, reply_markup=instagram_kb(reel_id))
