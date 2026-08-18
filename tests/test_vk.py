from __future__ import annotations

from bot.services import notion_sync, vk, vk_bot
from config import Settings
from db.models import Bonus
from db.session import session_scope


def test_not_configured_by_default():
    assert vk.is_configured() is False


def test_check_secret(monkeypatch):
    monkeypatch.setattr(vk, "get_settings", lambda: Settings(vk_secret="topsecret"))
    assert vk.check_secret("topsecret") is True
    assert vk.check_secret("wrong") is False
    assert vk.check_secret(None) is False


def test_check_secret_disabled(monkeypatch):
    monkeypatch.setattr(vk, "get_settings", lambda: Settings(vk_secret=""))
    assert vk.check_secret(None) is True


async def _seed_bonus() -> None:
    async with session_scope() as session:
        session.add(Bonus(
            bonus_id="b1", season_id="sweet", keyword="НУТЕЛЛА", title="Три ошибки в нейминге",
            pdf_link="https://p/nutella.pdf", audio_link="https://a/nutella.mp3", tags=["нейминг"],
        ))


async def test_handle_incoming_bonus(db, monkeypatch):
    sent: list[tuple[int, str]] = []

    async def fake_send(peer_id, text):
        sent.append((peer_id, text))

    monkeypatch.setattr(vk, "send_message", fake_send)
    await _seed_bonus()
    await vk_bot.handle_incoming("нутелла", peer_id=111, from_id=111)

    assert len(sent) == 1
    peer, text = sent[0]
    assert peer == 111
    assert "nutella.pdf" in text
    assert "t.me/" in text


async def test_handle_incoming_none(db, monkeypatch):
    sent: list[str] = []

    async def fake_send(peer_id, text):
        sent.append(text)

    monkeypatch.setattr(vk, "send_message", fake_send)
    await vk_bot.handle_incoming("нетакогослова", peer_id=222, from_id=222)

    assert len(sent) == 1
    assert "t.me/" in sent[0]


async def test_publish_vk_posts_gate_when_unconfigured(db):
    assert await notion_sync.publish_vk_posts() == 0
