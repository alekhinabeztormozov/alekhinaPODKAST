from __future__ import annotations

from typing import Any

from bot.services import catalog, notion, notion_sync
from config import Settings


def _page(pid: str, status: str = "Опубликован", keyword: str = "НУТЕЛЛА", tg: str = "Новый выпуск!") -> dict[str, Any]:
    return {
        "id": pid,
        "properties": {
            "Название": {"title": [{"plain_text": "Nutella ложкой"}]},
            "Статус": {"select": {"name": status}},
            "Сезон": {"select": {"name": "sweet"}},
            "Ссылка на аудио": {"url": "https://au/nutella.mp3"},
            "Теги": {"rich_text": [{"plain_text": "шоколад, паста"}]},
            "Ключевое слово": {"rich_text": [{"plain_text": keyword}]},
            "Название бонуса": {"rich_text": [{"plain_text": "Три ошибки в нейминге"}]},
            "PDF-бонус": {"url": "https://p/nutella.pdf"},
            "Аудио-бонус": {"url": "https://a/nutella_bonus.mp3"},
            "Пост для Telegram": {"rich_text": [{"plain_text": tg}]},
        },
    }


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[Any, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


def test_extract_catalog_maps_fields():
    data = notion.extract_catalog(_page("abc-123"))
    assert data["episode_id"] == "abc-123"
    assert data["season_id"] == "sweet"
    assert data["audio_link"] == "https://au/nutella.mp3"
    assert data["tags"] == ["шоколад", "паста"]
    assert data["keyword"] == "НУТЕЛЛА"
    assert data["bonus_id"] == "nb_abc123"
    assert data["bonus_title"] == "Три ошибки в нейминге"
    assert data["pdf_link"] == "https://p/nutella.pdf"
    assert data["bonus_audio"] == "https://a/nutella_bonus.mp3"


async def test_sync_creates_episode_and_bonus(db, monkeypatch):
    async def fake_pages():
        return [_page("p-1")]

    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    result = await notion_sync.sync_catalog()
    assert result == {"episodes": 1, "bonuses": 1, "skipped": 0}

    bonus = await catalog.bonus_by_keyword("нутелла")
    assert bonus is not None and bonus["title"] == "Три ошибки в нейминге"
    found = await catalog.search("шоколад")
    assert any(item["kind"] == "episode" for item in found)


async def test_sync_idempotent(db, monkeypatch):
    async def fake_pages():
        return [_page("p-1")]

    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    await notion_sync.sync_catalog()
    await notion_sync.sync_catalog()
    seasons_bonuses = await catalog.season_bonuses("sweet")
    assert len(seasons_bonuses) == 1


async def test_publish_posts_once(db, monkeypatch):
    async def fake_published():
        return [_page("p-9", tg="Вышел эпизод про Nutella")]

    monkeypatch.setattr(notion, "published_pages", fake_published)
    bot = FakeBot()
    settings = Settings(open_channel_id="-100500")
    first = await notion_sync.publish_ready_posts(bot, settings)
    assert first == 1
    assert bot.sent == [("-100500", "Вышел эпизод про Nutella")]
    second = await notion_sync.publish_ready_posts(bot, settings)
    assert second == 0
