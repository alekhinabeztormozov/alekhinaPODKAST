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
