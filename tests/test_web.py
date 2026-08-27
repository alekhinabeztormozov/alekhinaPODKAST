from __future__ import annotations

from fastapi.testclient import TestClient

import web.app as webapp
from config import Settings
from web.app import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vk_callback_disabled_returns_ok():
    response = TestClient(webapp.app).post("/vk/callback", json={"type": "confirmation"})
    assert response.status_code == 200
    assert response.text == "ok"


def test_vk_callback_confirmation(monkeypatch):
    monkeypatch.setattr(webapp.vk, "is_configured", lambda: True)
    monkeypatch.setattr(webapp, "get_settings", lambda: Settings(vk_confirmation_token="conf123"))
    response = TestClient(webapp.app).post("/vk/callback", json={"type": "confirmation"})
    assert response.text == "conf123"


def test_vk_callback_message_new_schedules_handler(monkeypatch):
    monkeypatch.setattr(webapp.vk, "is_configured", lambda: True)
    monkeypatch.setattr(webapp.vk, "check_secret", lambda secret: True)
    calls: list[tuple] = []

    async def fake_handle(text, peer_id, from_id, payload=""):
        calls.append((text, peer_id, from_id, payload))

    monkeypatch.setattr(webapp.vk_bot, "handle_incoming", fake_handle)
    body = {
        "type": "message_new",
        "object": {"message": {"text": "нутелла", "peer_id": 42, "from_id": 42, "payload": ""}},
    }
    response = TestClient(webapp.app).post("/vk/callback", json=body)
    assert response.status_code == 200
    assert response.text == "ok"
    assert calls == [("нутелла", 42, 42, "")]


def test_vk_callback_bad_secret_ignored(monkeypatch):
    monkeypatch.setattr(webapp.vk, "is_configured", lambda: True)
    monkeypatch.setattr(webapp.vk, "check_secret", lambda secret: False)
    called: list = []

    async def fake_handle(*a, **k):
        called.append(1)

    monkeypatch.setattr(webapp.vk_bot, "handle_incoming", fake_handle)
    body = {"type": "message_new", "secret": "wrong", "object": {"message": {"text": "x", "peer_id": 1}}}
    response = TestClient(webapp.app).post("/vk/callback", json=body)
    assert response.status_code == 200
    assert called == []
