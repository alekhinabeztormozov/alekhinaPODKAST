from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from bot.services import seen
from config import Settings
from db.models import ScheduledPost
from db.session import session_scope
from scheduler import jobs


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


async def test_seen_dedup(db):
    assert await seen.mark_seen("rss", "g1") is True
    assert await seen.mark_seen("rss", "g1") is False
    assert await seen.is_seen("rss", "g1") is True
    assert await seen.is_seen("rss", "g2") is False


async def test_publish_due_only_past(db):
    past = datetime.now(UTC) - timedelta(minutes=5)
    future = datetime.now(UTC) + timedelta(hours=1)
    async with session_scope() as session:
        session.add(ScheduledPost(target="@c", text="hi", publish_at=past))
        session.add(ScheduledPost(target="@c", text="later", publish_at=future))

    bot = FakeBot()
    published = await jobs.publish_due(bot)

    assert published == 1
    assert bot.sent == [("@c", "hi")]
    async with session_scope() as session:
        rows = (await session.execute(select(ScheduledPost))).scalars().all()
        statuses = {row.text: row.status for row in rows}
    assert statuses == {"hi": "published", "later": "pending"}


async def test_notify_ready_dedups(db, monkeypatch):
    episodes = [
        {
            "id": "p1",
            "properties": {
                "Название": {"title": [{"plain_text": "Эп1"}]},
                "Статус": {"select": {"name": "Контент готов"}},
            },
        }
    ]

    async def fake_ready():
        return episodes

    monkeypatch.setattr(jobs.notion, "ready_episodes", fake_ready)

    bot = FakeBot()
    settings = Settings(admin_tg_ids="1")
    first = await jobs.notify_ready(bot, settings)
    second = await jobs.notify_ready(bot, settings)

    assert first == 1
    assert second == 0
    assert bot.sent[0][0] == 1


class FakeFeed:
    def __init__(self, entries):
        self.entries = entries


async def test_rss_uses_notion_post_and_blocks_repeat(db, monkeypatch):
    from bot.services import notion, notion_sync

    entries = [
        {"id": "g2", "title": "Мак  Э2", "link": "https://podster.fm/2", "summary": "s"},
        {"id": "g1", "title": "Старый", "link": "https://podster.fm/1"},
    ]
    page = {
        "id": "p-2",
        "properties": {
            "Название": {"title": [{"plain_text": "мак э2"}]},
            "Пост для Telegram": {"rich_text": [{"plain_text": "Почему мы берем фри сытыми"}]},
        },
    }

    async def fake_pages():
        return [page]

    monkeypatch.setattr(jobs.feedparser, "parse", lambda url: FakeFeed(entries))
    monkeypatch.setattr(notion, "catalog_pages", fake_pages)
    monkeypatch.setattr(notion, "published_pages", fake_pages)
    await seen.mark_seen("rss", "g1")
    settings = Settings(podster_rss_url="https://rss", open_channel_id="@open")
    bot = FakeBot()

    assert await jobs.poll_rss(bot, settings) == 1
    assert bot.sent == [("@open", "Почему мы берем фри сытыми\n\nСлушать: https://podster.fm/2")]
    assert await notion_sync.publish_ready_posts(bot, settings) == 0
    assert await jobs.poll_rss(bot, settings) == 0


async def test_rss_falls_back_to_template(db, monkeypatch):
    from bot.services import notion

    async def no_pages():
        return None

    monkeypatch.setattr(jobs.feedparser, "parse", lambda url: FakeFeed([{"id": "g3", "title": "Э3", "link": "L"}]))
    monkeypatch.setattr(notion, "catalog_pages", no_pages)
    await seen.mark_seen("rss", "seed")
    bot = FakeBot()

    assert await jobs.poll_rss(bot, Settings(podster_rss_url="u", open_channel_id="@open")) == 1
    assert bot.sent[0][1].startswith("<b>Э3</b>")
