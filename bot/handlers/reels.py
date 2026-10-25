from __future__ import annotations

import re
import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.handlers.producer import MAX_TG_DOWNLOAD, TMP_DIR, _is_owner, owner_only
from bot.services import notion
from bot.states.flows import ReelFlow
from bot.ui import show
from config import get_settings
from reels import announces, scenarios, store
from reels.transcribe import load_transcript, transcribe_episode, transcript_text

router = Router(name="reels")

TRACKS_DIR = Path("media/reels/tracks")
REF_MAX = 48

PANEL_HINT = (
    "🎬 <b>Рилсы</b>\n\n"
    "Пришлите выпуск аудиофайлом, в подписи - название. Бот расшифрует его и напишет сценарии роликов. "
    "Вы смотрите логику, утверждаете или пишете правки. Дальше бот сам соберет ролики и выложит по расписанию.\n\n"
    "{counts}"
)
EPISODE_HINT = "Пришлите выпуск аудиофайлом, в подписи к нему - название выпуска."
ANNOUNCE_LABELS = {
    "open_channel": "📢 Открытый канал",
    "closed_channel": "🔒 Закрытый канал",
    "vk": "🟦 ВКонтакте",
}
TRACK_HINT ="Пришлите трек для этого ролика (mp3 файлом), из него возьму самый яркий кусок."


def episode_ref(title: str) -> str:
    slug = re.sub(r"[^\w]+", "-", title.lower()).strip("-")[:REF_MAX]
    return slug or f"ep-{uuid.uuid4().hex[:8]}"


def panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Сценарии из выпуска", callback_data="reel:new")
    builder.button(text="📝 На проверке", callback_data="reel:drafts")
    builder.button(text="🎵 Ждут трек", callback_data="reel:tracks")
    builder.button(text="◀️ В пульт", callback_data="own:panel")
    builder.adjust(1)
    return builder.as_markup()


def card_kb(reel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Утвердить", callback_data=f"reel:ok:{reel_id}")
    builder.button(text="✏️ Поправить", callback_data=f"reel:edit:{reel_id}")
    builder.button(text="🗑 Не надо", callback_data=f"reel:no:{reel_id}")
    builder.adjust(1, 2)
    return builder.as_markup()


def counts_text(totals: dict[str, int]) -> str:
    lines = [f"{title}: {totals[status]}" for status, title in store.STATUS_TITLES.items() if totals.get(status)]
    return "\n".join(lines) or "Пока роликов нет."


async def send_cards(bot: Bot, chat_id: int, reel_ids: list[int]) -> None:
    for reel_id in reel_ids:
        reel = await store.get(reel_id)
        if reel is None:
            continue
        await bot.send_message(chat_id, scenarios.card_text(reel.scenario), reply_markup=card_kb(reel_id))


@router.message(Command("reels"), owner_only)
async def reels_command(message: Message) -> None:
    await message.answer(PANEL_HINT.format(counts=counts_text(await store.counts())), reply_markup=panel_kb())


@router.callback_query(F.data == "reel:panel")
async def reels_panel(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    await show(callback, PANEL_HINT.format(counts=counts_text(await store.counts())), panel_kb())


@router.callback_query(F.data == "reel:new")
async def ask_episode(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    await state.set_state(ReelFlow.waiting_episode)
    await show(callback, EPISODE_HINT)


@router.message(ReelFlow.waiting_episode, owner_only, F.audio | F.voice | F.document)
async def receive_episode(message: Message, bot: Bot, state: FSMContext) -> None:
    media = message.audio or message.voice or message.document
    await state.clear()
    if (media.file_size or 0) > MAX_TG_DOWNLOAD:
        await message.answer("Файл больше 20 МБ, Telegram не отдаст его боту. Пришлите ссылку на Google Диск Льву.")
        return
    title = (message.caption or getattr(media, "title", None) or getattr(media, "file_name", None) or "Выпуск").strip()
    await message.answer("Расшифровываю выпуск и пишу сценарии, это займет несколько минут…")
    try:
        reel_ids = await make_scenarios(bot, media.file_id, title)
    except Exception as exc:
        logger.error("Сценарии не собрались: {}", exc)
        await message.answer("Не получилось собрать сценарии. Лев уже видит ошибку и поправит.")
        return
    await message.answer(f"Готово, сценариев: {len(reel_ids)}. Посмотрите логику каждого 👇")
    await send_cards(bot, message.chat.id, reel_ids)
    await send_announces(message, title)


async def send_announces(message: Message, title: str) -> None:
    transcript = transcript_text(load_transcript(episode_ref(title)))
    try:
        posts = await announces.generate(title, transcript)
    except Exception as exc:
        logger.error("Анонсы не собрались: {}", exc)
        return
    where = await save_announces(title, posts)
    await message.answer(f"Анонсы к выпуску ({where}):", parse_mode=None)
    for kind, label in ANNOUNCE_LABELS.items():
        await message.answer(f"{label}\n\n{posts[kind]}", parse_mode=None)


async def save_announces(title: str, posts: dict[str, str]) -> str:
    try:
        page = await notion.find_page(title)
        if page is None:
            return "в Notion выпуска с таким названием нет, скопируйте вручную"
        await notion.write_posts(notion.episode_id(page), posts)
        return "уже записал в Notion, выйдут вместе с выпуском"
    except Exception as exc:
        logger.error("Анонсы не записались в Notion: {}", exc)
        return "в Notion записать не вышло, скопируйте вручную"


async def make_scenarios(bot: Bot, file_id: str, title: str) -> list[int]:
    ref = episode_ref(title)
    segments = load_transcript(ref)
    if not segments:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        source = TMP_DIR / f"reel_src_{uuid.uuid4().hex[:8]}"
        await bot.download(file_id, destination=str(source))
        try:
            segments = await transcribe_episode(ref, source)
        finally:
            source.unlink(missing_ok=True)
    return await scenarios_for(ref, title, transcript_text(segments))


async def scenarios_for(ref: str, title: str, transcript: str) -> list[int]:
    items = await scenarios.generate(title, transcript, get_settings().reels_per_episode)
    return await store.add_drafts(ref, title, [item.model_dump() for item in items])


@router.callback_query(F.data.in_({"reel:drafts", "reel:tracks"}))
async def list_reels(callback: CallbackQuery, bot: Bot) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    status = store.DRAFT if callback.data == "reel:drafts" else store.NEED_TRACK
    reels = await store.with_status(status)
    await callback.answer()
    if not reels:
        await bot.send_message(callback.from_user.id, "Тут пусто 👌")
        return
    if status == store.DRAFT:
        await send_cards(bot, callback.from_user.id, [reel.id for reel in reels])
        return
    for reel in reels:
        await bot.send_message(
            callback.from_user.id,
            f"🎵 {reel.scenario.get('title', '')}\nНажмите и пришлите трек",
            reply_markup=track_kb(reel.id),
        )


def track_kb(reel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎵 Прислать трек", callback_data=f"reel:track:{reel_id}")
    return builder.as_markup()


def _reel_id(callback: CallbackQuery) -> int:
    return int(callback.data.rsplit(":", 1)[1])


@router.callback_query(F.data.startswith("reel:ok:"))
async def approve_reel(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    reel = await store.approve(_reel_id(callback))
    if reel is None:
        await callback.answer("Ролик не найден", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    if reel.status == store.NEED_TRACK:
        await state.set_state(ReelFlow.waiting_track)
        await state.update_data(reel_id=reel.id)
        await callback.message.answer(TRACK_HINT)
    else:
        await callback.message.answer("Утверждено ✅ Соберу ролик и поставлю в расписание.")
    await callback.answer()


@router.callback_query(F.data.startswith("reel:no:"))
async def reject_reel(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    await store.update(_reel_id(callback), status=store.REJECTED)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Убрал")


@router.callback_query(F.data.startswith("reel:drop:"))
async def drop_reel(callback: CallbackQuery) -> None:
    if callback.from_user.id not in get_settings().report_ids + get_settings().admin_ids:
        await callback.answer()
        return
    await store.update(_reel_id(callback), status=store.REJECTED, publish_at=None)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Снял с публикации")


@router.callback_query(F.data.startswith("reel:ig:"))
async def instagram_done(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Отметил, спасибо)")


@router.callback_query(F.data.startswith("reel:edit:"))
async def ask_feedback(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    await state.set_state(ReelFlow.waiting_feedback)
    await state.update_data(reel_id=_reel_id(callback))
    await callback.message.answer("Напишите, что поменять - текстом или голосовым словами.")
    await callback.answer()


@router.message(ReelFlow.waiting_feedback, owner_only, F.text)
async def receive_feedback(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    reel = await store.get(int(data.get("reel_id", 0)))
    if reel is None:
        await message.answer("Ролик потерялся, откройте рилсы заново.")
        return
    await message.answer("Переписываю…")
    try:
        transcript = transcript_text(load_transcript(reel.episode_ref))
        updated = await scenarios.rewrite(reel.episode_title, transcript, reel.scenario, message.text)
    except Exception as exc:
        logger.error("Правка сценария {} упала: {}", reel.id, exc)
        await message.answer("Не получилось переписать, попробуйте еще раз чуть позже.")
        return
    feedback = "\n".join(part for part in (reel.feedback, message.text) if part)
    await store.update(reel.id, scenario=updated.model_dump(), feedback=feedback, status=store.DRAFT)
    await message.answer(scenarios.card_text(updated.model_dump()), reply_markup=card_kb(reel.id))


@router.callback_query(F.data.startswith("reel:track:"))
async def ask_track(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user, get_settings()):
        await callback.answer()
        return
    await state.set_state(ReelFlow.waiting_track)
    await state.update_data(reel_id=_reel_id(callback))
    await callback.message.answer(TRACK_HINT)
    await callback.answer()


@router.message(ReelFlow.waiting_track, owner_only, F.audio | F.document)
async def receive_track(message: Message, bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    reel_id = int(data.get("reel_id", 0))
    media = message.audio or message.document
    if (media.file_size or 0) > MAX_TG_DOWNLOAD:
        await message.answer("Трек больше 20 МБ, сожмите до mp3 и пришлите еще раз.")
        return
    TRACKS_DIR.mkdir(parents=True, exist_ok=True)
    target = TRACKS_DIR / f"reel_{reel_id}.mp3"
    await bot.download(media.file_id, destination=str(target))
    await store.update(reel_id, track_path=str(target), status=store.APPROVED)
    await message.answer("Трек получил 🎵 Соберу ролик и поставлю в расписание.")
