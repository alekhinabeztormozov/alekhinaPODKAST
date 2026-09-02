from __future__ import annotations

import json

from bot.services import notion_sync, vk, vk_bot
from config import Settings
from db.models import Bonus
from db.session import session_scope


def test_not_configured_by_default(monkeypatch):
    monkeypatch.setattr(vk, "get_settings", lambda: Settings(vk_group_token=""))
    assert vk.is_configured() is False


def test_check_secret(monkeypatch):
    monkeypatch.setattr(vk, "get_settings", lambda: Settings(vk_secret="topsecret"))
    assert vk.check_secret("topsecret") is True
    assert vk.check_secret("wrong") is False
    assert vk.check_secret(None) is False


def test_check_secret_disabled(monkeypatch):
    monkeypatch.setattr(vk, "get_settings", lambda: Settings(vk_secret=""))
    assert vk.check_secret(None) is True


def test_main_keyboard_has_buttons_and_tg_link():
    kb = json.loads(vk_bot.main_keyboard())
    labels = [row[0]["action"].get("label") for row in kb["buttons"]]
    assert any("архиве" in label for label in labels)
    links = [row[0]["action"].get("link") for row in kb["buttons"] if row[0]["action"].get("link")]
    assert links and "t.me/" in links[0]


class _Sink:
    def __init__(self):
        self.sent: list[tuple[int, str, str | None]] = []

    async def send(self, peer_id, text, keyboard=None):
        self.sent.append((peer_id, text, keyboard))


async def _seed_bonus() -> None:
    async with session_scope() as session:
        session.add(Bonus(
            bonus_id="b1", season_id="sweet", keyword="НУТЕЛЛА", title="Три ошибки в нейминге",
            pdf_link="https://p/nutella.pdf", audio_link="https://a/nutella.mp3", tags=["нейминг"],
        ))


async def test_handle_incoming_bonus(db, monkeypatch):
    sink = _Sink()
    monkeypatch.setattr(vk, "send_message", sink.send)
    await _seed_bonus()
    await vk_bot.handle_incoming("нутелла", peer_id=111, from_id=111)

    assert len(sink.sent) == 1
    peer, text, keyboard = sink.sent[0]
    assert peer == 111
    assert "nutella.pdf" in text
    assert "t.me/" in text
    assert keyboard is not None


async def test_handle_incoming_none(db, monkeypatch):
    sink = _Sink()
    monkeypatch.setattr(vk, "send_message", sink.send)
    await vk_bot.handle_incoming("нетакогослова", peer_id=222, from_id=222)

    assert len(sink.sent) == 1
    assert "t.me/" in sink.sent[0][1]


async def test_handle_start_greeting(db, monkeypatch):
    sink = _Sink()
    monkeypatch.setattr(vk, "send_message", sink.send)
    await vk_bot.handle_incoming("Начать", peer_id=333, from_id=333)
    assert "Привет" in sink.sent[0][1]


async def test_handle_club_button(db, monkeypatch):
    sink = _Sink()
    monkeypatch.setattr(vk, "send_message", sink.send)
    await vk_bot.handle_incoming("", peer_id=444, from_id=444, payload=json.dumps({"cmd": "club"}))
    assert "Код Алёхиной" in sink.sent[0][1]


async def test_handle_search_button(db, monkeypatch):
    sink = _Sink()
    monkeypatch.setattr(vk, "send_message", sink.send)
    await vk_bot.handle_incoming("", peer_id=555, from_id=555, payload=json.dumps({"cmd": "search"}))
    assert "поищу" in sink.sent[0][1].lower()


async def test_publish_vk_posts_gate_when_unconfigured(db):
    assert await notion_sync.publish_vk_posts() == 0
