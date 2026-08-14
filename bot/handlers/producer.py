from __future__ import annotations

import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, User
from loguru import logger

from bot.content import MENU_HINT, OWNER_AUDIO_HINT, OWNER_GUIDE_HINT, OWNER_PANEL
from bot.handlers.admin import week_stats_text
from bot.keyboards.common import (
    ambient_kb,
    ambient_preview_kb,
    back_to_owner,
    client_preview_kb,
    owner_menu,
)
from bot.services.audio import make_episode
from bot.services.pdf import build_guide
from bot.states.flows import Producer
from bot.ui import show
from config import Settings, get_settings
from media.ambient import find_ambient, get_ambients

router = Router(name="producer")

MAX_TG_DOWNLOAD = 20 * 1024 * 1024
MIN_GUIDE_LEN = 30
TMP_DIR = Path("media/tmp")
OUT_DIR = Path("media/out")


def _is_owner(user: User | None, settings: Settings) -> bool:
    return user is not None and user.id in settings.admin_ids


async def owner_only(message: Message) -> bool:
    return _is_owner(message.from_user, get_settings())


def split_guide(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return "Гайд", text.strip()
    title = non_empty[0].strip()[:80]
    index = lines.index(non_empty[0])
    body = "\n".join(lines[index + 1:]).strip()
    return title, body or non_empty[0].strip()


@router.message(Command("ambients"), owner_only)
async def list_ambients(message: Message) -> None:
    tracks = get_ambients()
    if not tracks:
        await message.answer("Эмбиентов пока нет. Загрузи файлы в media/assets/ambient/.")
        return
    lines = [
        f"• <b>{track.title}</b>" + (f" — {track.description}" if track.description else "")
        for track in tracks
    ]
    await message.answer(
        "Фоновые эмбиенты (нажми, чтобы послушать):\n\n" + "\n".join(lines),
        reply_markup=ambient_preview_kb(),
    )


@router.callback_query(F.data.startswith("ambprev:"))
async def preview_ambient(callback: CallbackQuery, bot: Bot) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    track = find_ambient(callback.data.split(":", 1)[1])
    if track is None or not track.path.exists():
        await callback.answer("Файл не найден.", show_alert=True)
        return
    await callback.answer("Отправляю…")
    await bot.send_audio(callback.from_user.id, FSInputFile(track.path), caption=track.title)


@router.callback_query(F.data.startswith("own:"))
async def owner_panel(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    action = callback.data.split(":", 1)[1]
    if action == "panel":
        await show(callback, OWNER_PANEL, owner_menu())
    elif action == "audio":
        await show(callback, OWNER_AUDIO_HINT, back_to_owner())
    elif action == "guide":
        await show(callback, OWNER_GUIDE_HINT, back_to_owner())
    elif action == "ambients":
        tracks = get_ambients()
        if not tracks:
            await show(callback, "Эмбиентов нет. Загрузи файлы в media/assets/ambient/.", back_to_owner())
            return
        lines = [
            f"• <b>{track.title}</b>" + (f" — {track.description}" if track.description else "")
            for track in tracks
        ]
        await show(callback, "Фоновые эмбиенты (нажми, чтобы послушать):\n\n" + "\n".join(lines), ambient_preview_kb())
    elif action == "stats":
        await show(callback, await week_stats_text(), back_to_owner())
    elif action == "client":
        await show(callback, MENU_HINT, client_preview_kb())
    else:
        await callback.answer()


@router.message(StateFilter(None), owner_only, F.text & ~F.text.startswith("/"))
async def receive_guide_text(message: Message) -> None:
    text = message.text or ""
    if len(text.strip()) < MIN_GUIDE_LEN:
        await message.answer("Пришли текст гайда (первая строка — заголовок) или аудио-эпизод для обработки.")
        return

    title, body = split_guide(text)
    await message.answer("Собираю PDF-гайд…")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"guide_{uuid.uuid4().hex[:12]}.pdf"
    try:
        await build_guide(title, body, out_path)
    except Exception as exc:
        logger.error("Сборка PDF упала: {}", exc)
        await message.answer("Не удалось собрать PDF-гайд.")
        return

    await message.answer_document(FSInputFile(out_path), caption=f"Гайд: {title}")
    out_path.unlink(missing_ok=True)
    await message.answer("Готово ✅ Пришли ещё текст или аудио, или вернись в пульт.", reply_markup=owner_menu())


@router.message(owner_only, F.audio | F.voice)
async def receive_audio(message: Message, state: FSMContext) -> None:
    media = message.audio or message.voice
    if media is None:
        return

    await state.set_state(Producer.choosing_ambient)
    await state.update_data(file_id=media.file_id)

    warning = ""
    if (media.file_size or 0) > MAX_TG_DOWNLOAD:
        warning = (
            "\n\n⚠ Файл больше 20 МБ. Telegram Bot API не отдаст его боту без "
            "локального Bot API server — см. docs/owner-guide.md."
        )
    await message.answer("Выбери фоновый эмбиент для эпизода:" + warning, reply_markup=ambient_kb())


@router.callback_query(F.data.startswith("amb:"), Producer.choosing_ambient)
async def choose_ambient(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]

    if action == "cancel":
        await state.clear()
        await show(callback, "Отменил обработку.")
        return

    data = await state.get_data()
    file_id = data.get("file_id")
    await state.clear()

    if not file_id:
        await callback.answer("Файл потерялся, пришли аудио заново.", show_alert=True)
        return

    music: Path | None = None
    if action != "none":
        track = find_ambient(action)
        if track is None or not track.path.exists():
            await callback.answer("Эмбиент не найден.", show_alert=True)
            return
        music = track.path

    await show(callback, "Обрабатываю аудио, подожди…")
    try:
        result = await _process(bot, file_id, music)
    except Exception as exc:
        logger.error("Обработка аудио упала: {}", exc)
        await bot.send_message(
            callback.from_user.id,
            "Не получилось обработать. Если файл больше 20 МБ — нужен локальный Bot API server.",
        )
        return

    await bot.send_audio(callback.from_user.id, FSInputFile(result), caption="Готовый эпизод")
    result.unlink(missing_ok=True)
    await bot.send_message(
        callback.from_user.id,
        "Готово ✅ Пришли ещё эпизод, или вернись в пульт.",
        reply_markup=owner_menu(),
    )


async def _process(bot: Bot, file_id: str, music: Path | None) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex[:12]
    source = TMP_DIR / f"src_{token}"
    out_path = OUT_DIR / f"ep_{token}.mp3"

    await bot.download(file_id, destination=str(source))
    try:
        await make_episode(voice=source, out_path=out_path, music=music)
    finally:
        source.unlink(missing_ok=True)
    return out_path
