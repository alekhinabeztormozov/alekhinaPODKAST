from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from config import Settings
from db.models import Reel
from reels import heygen, publish, render, store
from reels.scenarios import voiceover_text
from reels.subtitles import Word, build_ass
from reels.transcribe import TranscribeError, words_of

REELS_DIR = Path("media/reels")
SONG_VISUALS_DIR = Path("media/assets/reels")
SONG_SECONDS = 25
HEYGEN_DONE = "completed"


def reel_file(reel_id: int, suffix: str) -> Path:
    REELS_DIR.mkdir(parents=True, exist_ok=True)
    return REELS_DIR / f"reel_{reel_id}{suffix}"


def screen_hook(scenario: dict) -> str:
    scenes = scenario.get("scenes") or []
    if scenes and scenes[0].get("on_screen"):
        return scenes[0]["on_screen"]
    return scenario.get("title", "")


def song_visual() -> Path | None:
    if not SONG_VISUALS_DIR.exists():
        return None
    candidates = sorted(path for path in SONG_VISUALS_DIR.iterdir() if path.suffix.lower() in {
        *render.IMAGE_SUFFIXES, ".mp4", ".mov",
    })
    return candidates[0] if candidates else None


async def _safe_words(media: Path) -> list[Word]:
    try:
        return await words_of(media)
    except TranscribeError as exc:
        logger.warning("Субтитры пропущены, нет расшифровки: {}", exc)
        return []


def preview_kb(reel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛑 Снять с публикации", callback_data=f"reel:drop:{reel_id}")
    return builder.as_markup()


async def _announce_ready(bot: Bot, settings: Settings, reel: Reel, video: Path) -> None:
    slot = reel.publish_at.astimezone(store.MSK).strftime("%d.%m %H:%M") if reel.publish_at else "-"
    caption = f"Готов ролик: {reel.scenario.get('title', '')}\nВыйдет {slot} по мск"
    for chat_id in settings.report_ids:
        try:
            await bot.send_video(chat_id, FSInputFile(video), caption=caption, reply_markup=preview_kb(reel.id))
        except Exception as exc:
            logger.error("Не показал превью {}: {}", chat_id, exc)


async def _finish(bot: Bot, settings: Settings, reel_id: int, video: Path) -> None:
    await store.update(reel_id, video_path=str(video))
    await store.schedule(reel_id, settings.reel_slots)
    reel = await store.get(reel_id)
    if reel is not None:
        await _announce_ready(bot, settings, reel, video)


async def _fail(bot: Bot, settings: Settings, reel_id: int, exc: Exception) -> None:
    logger.error("Ролик {} не собрался: {}", reel_id, exc)
    await store.update(reel_id, status=store.FAILED, error=str(exc)[:1000])
    await _report_errors(bot, settings, f"Ролик {reel_id} не собрался: {exc}")


async def render_song(bot: Bot, settings: Settings, reel: Reel) -> None:
    visual = song_visual()
    if visual is None:
        raise render.RenderError("нет картинки для нейротрека в media/assets/reels/")
    track = Path(reel.track_path)
    levels = await asyncio.to_thread(render.loudness_per_second, track)
    start = render.loudest_start(levels, SONG_SECONDS)
    clip = await asyncio.to_thread(render.cut_audio, track, start, SONG_SECONDS, reel_file(reel.id, "_clip.mp3"))
    words = await _safe_words(clip)
    clip.unlink(missing_ok=True)
    out = reel_file(reel.id, ".mp4")
    ass = build_ass(words, screen_hook(reel.scenario))
    await asyncio.to_thread(render.compose_song_reel, track, visual, ass, out, start, SONG_SECONDS)
    await _finish(bot, settings, reel.id, out)


async def start_renders(bot: Bot, settings: Settings) -> int:
    started = 0
    for reel in await store.with_status(store.APPROVED):
        try:
            if reel.kind == "trigger_song":
                await store.update(reel.id, status=store.RENDERING)
                await render_song(bot, settings, reel)
            else:
                job = await heygen.start_video(voiceover_text(reel.scenario))
                await store.update(reel.id, status=store.RENDERING, render_job=job)
            started += 1
        except Exception as exc:
            await _fail(bot, settings, reel.id, exc)
    return started


async def finish_avatar(bot: Bot, settings: Settings, reel: Reel, video_url: str) -> None:
    raw = await heygen.download(video_url, reel_file(reel.id, "_raw.mp4"))
    words = await _safe_words(raw)
    out = reel_file(reel.id, ".mp4")
    await asyncio.to_thread(render.compose_avatar_reel, raw, build_ass(words, screen_hook(reel.scenario)), out)
    raw.unlink(missing_ok=True)
    await _finish(bot, settings, reel.id, out)


async def poll_renders(bot: Bot, settings: Settings) -> int:
    finished = 0
    for reel in await store.with_status(store.RENDERING):
        if not reel.render_job:
            continue
        try:
            status, video_url = await heygen.video_status(reel.render_job)
            if status != HEYGEN_DONE or not video_url:
                continue
            await finish_avatar(bot, settings, reel, video_url)
            finished += 1
        except Exception as exc:
            await _fail(bot, settings, reel.id, exc)
    return finished


async def _publish_target(bot: Bot, target: str, reel: Reel, video: Path) -> None:
    if target == "tg":
        await publish.to_telegram(bot, video, reel.scenario)
    elif target == "vk":
        await publish.to_vk(video, reel.scenario)
    elif target == "ig":
        await publish.to_instagram_owner(bot, video, reel.scenario, reel.id)


async def publish_reel(bot: Bot, settings: Settings, reel: Reel) -> list[str]:
    video = Path(reel.video_path)
    done = list(reel.published or [])
    errors = []
    for target in settings.reel_targets:
        if target in done:
            continue
        try:
            await _publish_target(bot, target, reel, video)
            done.append(target)
        except Exception as exc:
            logger.error("Ролик {} не ушел в {}: {}", reel.id, target, exc)
            errors.append(f"{target}: {exc}")
    await store.update(reel.id, status=store.PUBLISHED, published=done, error="; ".join(errors)[:1000])
    return errors


async def _report_errors(bot: Bot, settings: Settings, text: str) -> None:
    for chat_id in settings.report_ids:
        try:
            await bot.send_message(chat_id, text, parse_mode=None)
        except Exception as exc:
            logger.error("Не сообщил об ошибке публикации: {}", exc)


async def publish_due_reels(bot: Bot, settings: Settings, now: datetime | None = None) -> int:
    published = 0
    for reel in await store.due(now or datetime.now(UTC)):
        errors = await publish_reel(bot, settings, reel)
        published += 1
        if errors:
            await _report_errors(bot, settings, f"Ролик {reel.id} вышел не везде:\n" + "\n".join(errors))
    return published
