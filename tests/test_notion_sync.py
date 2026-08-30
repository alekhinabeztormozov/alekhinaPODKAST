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


async def _async(value: Any) -> Any:
    return value


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
    assert (result["episodes"], result["bonuses"], result["skipped"]) == (1, 1, 0)

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


async def _add_season(season_id: str, title: str, is_current: bool = False) -> None:
    from db.models import Season
    from db.session import session_scope

    async with session_scope() as session:
        session.add(Season(season_id=season_id, title=title, is_current=is_current))


async def test_season_resolved_by_human_title(db, monkeypatch):
    """В Notion пишут «Сладкая империя», а в базе сезон лежит под слагом sweet."""
    await _add_season("sweet", "Сладкая империя")
    page = _page("p-2")
    page["properties"]["Сезон"] = {"select": {"name": "  сладкая ИМПЕРИЯ "}}

    async def fake_pages():
        return [page]

    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    result = await notion_sync.sync_catalog()
    assert result["problems"] == []
    assert len(await catalog.season_bonuses("sweet")) == 1


async def test_empty_season_falls_back_to_current(db, monkeypatch):
    await _add_season("sweet", "Сладкая империя", is_current=True)
    page = _page("p-3")
    page["properties"]["Сезон"] = {"select": None}

    async def fake_pages():
        return [page]

    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    await notion_sync.sync_catalog()
    assert len(await catalog.season_bonuses("sweet")) == 1


async def test_skip_reason_reported(db, monkeypatch):
    page = _page("p-4", keyword="")
    page["properties"]["Ссылка на аудио"] = {"url": None}
    page["properties"]["Теги"] = {"rich_text": []}

    async def fake_pages():
        return [page]

    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    result = await notion_sync.sync_catalog()
    assert result["skipped"] == 1
    assert any("пропущен" in p for p in result["problems"])


UUID_A = "3c9f5b3d-18c8-80a6-8bdc-d454a94419e5"
UUID_B = "3c9f5b3d-18c8-80d9-882f-f48e74be9cb6"


async def test_missing_page_is_pruned(db, monkeypatch):
    """Строку убрали из Notion — эпизод и бонус уходят из базы бота."""
    pages = [_page(UUID_A)]
    monkeypatch.setattr(notion, "catalog_pages", lambda: _async(pages))
    await notion_sync.sync_catalog()
    assert await catalog.bonus_by_keyword("нутелла") is not None

    pages.clear()
    pages.append(_page(UUID_B, keyword="ДРУГОЕ"))
    result = await notion_sync.sync_catalog()
    assert await catalog.bonus_by_keyword("нутелла") is None
    assert any("больше нет в Notion" in p for p in result["problems"])


async def test_manual_rows_survive_prune(db, monkeypatch):
    """Заведённое руками через /add_* не имеет id-uuid и удаляться не должно."""
    from db.models import Bonus, Episode
    from db.session import session_scope

    async with session_scope() as session:
        session.add(Episode(episode_id="sweet_nutella", season_id="sweet", title="Ручной"))
        session.add(Bonus(bonus_id="bonus_nutella", season_id="sweet", keyword="РУЧНОЕ",
                          title="Ручной бонус"))

    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([_page(UUID_A)]))
    await notion_sync.sync_catalog()
    assert await catalog.bonus_by_keyword("ручное") is not None


async def test_duplicate_keyword_reported_not_overwritten(db, monkeypatch):
    first, second = _page(UUID_A), _page(UUID_B)
    second["properties"]["Название бонуса"] = {"rich_text": [{"plain_text": "Второй бонус"}]}
    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([first, second]))
    result = await notion_sync.sync_catalog()

    assert result["bonuses"] == 1
    assert any("уже занято" in p for p in result["problems"])
    bonus = await catalog.bonus_by_keyword("нутелла")
    assert bonus["title"] == "Три ошибки в нейминге"


async def test_page_without_title_skipped(db, monkeypatch):
    page = _page(UUID_A)
    page["properties"]["Название"] = {"title": []}
    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([page]))
    result = await notion_sync.sync_catalog()

    assert result["skipped"] == 1
    assert any("«Название»" in p for p in result["problems"])
    assert await catalog.bonus_by_keyword("нутелла") is None


async def test_notion_unavailable_deletes_nothing(db, monkeypatch):
    """Notion отвалился — catalog_pages отдаёт None, база остаётся как была."""
    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([_page(UUID_A)]))
    await notion_sync.sync_catalog()

    monkeypatch.setattr(notion, "catalog_pages", lambda: _async(None))
    result = await notion_sync.sync_catalog()
    assert await catalog.bonus_by_keyword("нутелла") is not None
    assert result["problems"] == ["Notion не ответил — ничего не менял, жду следующего прогона"]


async def test_empty_notion_prunes_everything(db, monkeypatch):
    """Notion ответил, что готовых строк нет — значит их правда убрали."""
    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([_page(UUID_A)]))
    await notion_sync.sync_catalog()

    monkeypatch.setattr(notion, "catalog_pages", lambda: _async([]))
    result = await notion_sync.sync_catalog()
    assert await catalog.bonus_by_keyword("нутелла") is None
    assert any("больше нет в Notion" in p for p in result["problems"])


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
