from __future__ import annotations

import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, User
from loguru import logger

from bot.keyboards.common import ambient_kb
from bot.services.audio import make_episode
from bot.states.flows import Producer
from bot.ui import show
from config import Settings, get_settings
from media.ambient import find_ambient

router = Router(name="producer")

MAX_TG_DOWNLOAD = 20 * 1024 * 1024
TMP_DIR = Path("media/tmp")
OUT_DIR = Path("media/out")


def _is_owner(user: User | None, settings: Settings) -> bool:
    return user is not None and user.id in settings.admin_ids


@router.message(F.audio | F.voice)
async def receive_audio(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    if not _is_owner(message.from_user, settings):
        return

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
