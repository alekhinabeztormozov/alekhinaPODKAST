from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from bot.services import admin_content, catalog, users
from config import Settings
from db.models import MainProduct, Season, User
from db.session import session_scope
from scheduler import jobs


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))

    async def ban_chat_member(self, *a, **k):
        pass

    async def unban_chat_member(self, *a, **k):
        pass


async def test_all_seasons_access(db):
    await users.add_purchased_season(1, "all")
    assert await users.has_season(1, "sweet") is True
    assert await users.has_season(1, "cola") is True


async def test_active_intensive(db):
    async with session_scope() as session:
        session.add(MainProduct(product_id="p1", season_id="sweet", title="Битва",
                                description="3ч", price=3900, price_subscriber=2730,
                                payment_link="https://pay", is_active=True))
    product = await catalog.active_main_product()
    assert product is not None and product["title"] == "Битва"


async def test_admin_content_upsert(db):
    res = await admin_content.add_season(["sweet", "Сладкая империя", "299", "179", "https://x", "1"])
    assert res == "добавлено"
    season = await catalog.get_season("sweet")
    assert season and season["price"] == 299 and season["is_current"] is True
    res2 = await admin_content.add_season(["sweet", "Сладкая империя 2", "349", "199", "https://x", "0"])
    assert res2 == "обновлено"
    counts = await admin_content.counts()
    assert counts["seasons"] == 1


async def test_revoke_expired(db):
    async with session_scope() as session:
        session.add(User(tg_id=42, is_subscribed=True,
                         subscription_expires=datetime.now(UTC) - timedelta(days=1)))
    bot = FakeBot()
    revoked = await jobs.revoke_expired(bot, Settings())
    assert revoked == 1
    assert any(chat == 42 for chat, _ in bot.sent)
    assert await users.is_subscribed(42) is False


async def test_finale_broadcast(db):
    async with session_scope() as session:
        session.add(Season(season_id="sweet", title="Сладкая империя", end_date=date.today()))
        session.add(MainProduct(product_id="p1", season_id="sweet", title="Битва",
                                description="практика", price=3900, price_subscriber=2730,
                                payment_link="https://pay", is_active=True))
        session.add(User(tg_id=101, username="u"))
    bot = FakeBot()
    notified = await jobs.notify_finale(bot, Settings())
    assert notified == 1
    assert any(chat == 101 for chat, _ in bot.sent)
