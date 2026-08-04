from __future__ import annotations

import types

from bot.handlers.producer import _is_owner, split_guide
from bot.keyboards.common import ambient_kb
from config import Settings
from media.ambient import find_ambient, get_ambients


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
