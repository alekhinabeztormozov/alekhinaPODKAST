from __future__ import annotations

from bot.handlers.reels import episode_ref
from bot.services import notion, notion_sync
from config import Settings
from reels import announces


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


def _page(page_id: str, closed: str) -> dict:
    return {
        "id": page_id,
        "properties": {"Пост для закрытого канала": {"rich_text": [{"plain_text": closed}]}},
    }


def test_clean_replaces_forbidden_marks():
    assert announces.clean(" «Фри» — это триггер ") == "\"Фри\" - это триггер"


def test_build_request_mentions_keyword_and_bot():
    prompt = announces.build_request("Мак Э2", "текст", "картошка", "https://podster.fm/x")
    assert "Ключевое слово для бота: картошка" in prompt
    assert "Ссылка на выпуск: https://podster.fm/x" in prompt
    assert "@AlekhinaU_bot" in prompt


def test_rich_text_value_splits_long_text():
    value = notion._rich_text_value("а" * 4500)
    assert [len(part["text"]["content"]) for part in value["rich_text"]] == [2000, 2000, 500]


def test_episode_ref_is_stable_slug():
    assert episode_ref("МАК Э2: Грудь и бренды!") == "мак-э2-грудь-и-бренды"
    assert episode_ref("!!!").startswith("ep-")


async def test_closed_posts_published_once(db, monkeypatch):
    async def fake_published():
        return [_page("p-1", "Для своих: главный вывод"), _page("p-2", "")]

    monkeypatch.setattr(notion, "published_pages", fake_published)
    bot = FakeBot()
    settings = Settings(closed_channel_id="-100777")
    assert await notion_sync.publish_closed_posts(bot, settings) == 1
    assert bot.sent == [("-100777", "Для своих: главный вывод")]
    assert await notion_sync.publish_closed_posts(bot, settings) == 0


async def test_closed_posts_skip_without_channel(db):
    assert await notion_sync.publish_closed_posts(FakeBot(), Settings(closed_channel_id="")) == 0
