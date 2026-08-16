from __future__ import annotations

from bot.services import notion
from bot.services.sheets import CONTACTS_SHEET, SHEET_HEADERS


def test_sheet_headers_cover_four_tabs():
    assert len(SHEET_HEADERS) == 4
    assert SHEET_HEADERS[CONTACTS_SHEET][0] == "Telegram ID"


def test_episodes_schema_has_all_properties():
    assert len(notion.EPISODES_SCHEMA) == 16
    assert "title" in notion.EPISODES_SCHEMA["Название"]
    for field in ("Ключевое слово", "Теги", "Аудио-бонус", "PDF-бонус"):
        assert field in notion.EPISODES_SCHEMA
    options = notion.EPISODES_SCHEMA["Статус"]["select"]["options"]
    assert [o["name"] for o in options] == notion.STATUSES


def test_ready_status_in_statuses():
    assert notion.READY_STATUS in notion.STATUSES


def test_episode_extractors():
    page = {
        "id": "abc",
        "properties": {
            "Название": {"title": [{"plain_text": "Starbucks"}]},
            "Статус": {"select": {"name": "Контент готов"}},
        },
    }
    assert notion.episode_id(page) == "abc"
    assert notion.episode_title(page) == "Starbucks"
    assert notion.episode_status(page) == "Контент готов"


def test_episode_extractors_empty_defaults():
    assert notion.episode_title({}) == "Без названия"
    assert notion.episode_status({}) == ""
