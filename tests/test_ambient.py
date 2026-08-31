from __future__ import annotations

import types

import pytest

from bot.handlers.producer import _is_owner, split_guide
from bot.keyboards.common import ambient_kb, ambient_preview_kb
from config import Settings
from media.ambient import AMBIENT_DIR, find_ambient, get_ambients


def test_ambients_present_and_unique():
    tracks = get_ambients()
    assert tracks
    ids = [track.id for track in tracks]
    assert len(ids) == len(set(ids))


def test_find_ambient_known_and_unknown():
    first = get_ambients()[0]
    found = find_ambient(first.id)
    assert found is not None and found.id == first.id
    assert find_ambient("nope") is None


def test_ambient_files_exist():
    for track in get_ambients():
        assert track.path.exists()


def test_ambient_kb_has_all_plus_controls():
    keyboard = ambient_kb()
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    assert len(buttons) == len(get_ambients()) + 2


def test_is_owner():
    settings = Settings(admin_tg_ids="1,2")
    assert _is_owner(types.SimpleNamespace(id=1), settings) is True
    assert _is_owner(types.SimpleNamespace(id=9), settings) is False
    assert _is_owner(None, settings) is False


def test_split_guide_multiline():
    title, body = split_guide("Разбор Nike\n\nПервый абзац.\n\nВторой абзац.")
    assert title == "Разбор Nike"
    assert "Первый абзац." in body
    assert "Второй абзац." in body


def test_split_guide_single_line_keeps_body():
    text = "Длинный одностр+очный текст гайда без переносов, который должен остаться телом"
    title, body = split_guide(text)
    assert body == text
    assert title == text[:80]


def test_split_guide_empty():
    title, body = split_guide("   ")
    assert title == "Гайд"
    assert body == ""


@pytest.fixture
def cyrillic_track():
    """Владелец кладёт файл с длинным русским именем — так бывает."""
    path = AMBIENT_DIR / "Спокойный тягучий фон для интро и финала.mp3"
    path.write_bytes(b"")
    yield path
    path.unlink(missing_ok=True)


def test_callback_codes_fit_telegram_limit(cyrillic_track):
    for track in get_ambients():
        code = track.code
        assert code.isascii()
        assert len(f"ambprev:{code}".encode()) <= 64


def test_ambient_keyboards_build_with_cyrillic_filename(cyrillic_track):
    """Раньше длинное юникод-имя ломало сборку клавиатуры и весь приём аудио."""
    assert ambient_kb().inline_keyboard
    assert ambient_preview_kb().inline_keyboard


def test_find_ambient_by_code(cyrillic_track):
    track = next(t for t in get_ambients() if t.path == cyrillic_track)
    assert track.code != track.id
    assert find_ambient(track.code) == track
    assert find_ambient(track.id) == track
