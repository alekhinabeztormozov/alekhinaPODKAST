from __future__ import annotations

from types import SimpleNamespace

from bot.handlers.club import club_bonuses
from bot.services import users
from db.models import Season
from db.session import session_scope


class FakeMessage:
    def __init__(self) -> None:
        self.text = ""
        self.markup = None

    async def edit_text(self, text, reply_markup=None):
        self.text = text
        self.markup = reply_markup

    async def answer(self, text, reply_markup=None):
        self.text = text
        self.markup = reply_markup


class FakeCallback:
    def __init__(self, tg_id: int) -> None:
        self.from_user = SimpleNamespace(id=tg_id)
        self.message = FakeMessage()
        self.answered = False

    async def answer(self, text=None, show_alert=False):
        self.answered = True


async def test_club_bonuses_offers_subscription_to_guest(db):
    """Не подписчик жмёт «Бонусы клуба» — должен увидеть оффер, а не упасть."""
    callback = FakeCallback(101)
    await club_bonuses(callback)
    assert "790" in callback.message.text
    assert callback.message.markup is not None


async def test_club_bonuses_subscriber_without_bonuses(db):
    async with session_scope() as session:
        session.add(Season(season_id="sweet", title="Сладкая империя", is_current=True))
    await users.grant_subscription(102, 30)
    callback = FakeCallback(102)
    await club_bonuses(callback)
    assert "скоро" in callback.message.text.lower()
