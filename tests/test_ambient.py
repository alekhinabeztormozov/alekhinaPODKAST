from __future__ import annotations

import types

from bot.handlers.producer import _is_owner, split_guide
from bot.keyboards.common import ambient_kb
from config import Settings
from media.ambient import AMBIENTS, find_ambient


def test_ambient_ids_unique():
    ids = [track.id for track in AMBIENTS]
    assert len(ids) == len(set(ids))


def test_find_ambient_known_and_unknown():
    assert find_ambient(AMBIENTS[0].id) is AMBIENTS[0]
    assert find_ambient("nope") is None


def test_ambient_path_matches_id():
    track = AMBIENTS[0]
    assert track.path.name == f"{track.id}.mp3"


def test_ambient_kb_has_all_plus_controls():
    keyboard = ambient_kb()
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    assert len(buttons) == len(AMBIENTS) + 2


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
