from __future__ import annotations

from sqlalchemy import func, select

from bot.services import catalog, contacts, fulfillment, users
from db.models import Contact, ProcessedPayment, Sale, Season
from db.session import session_scope


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))

    async def create_chat_invite_link(self, *a, **k):
        class _L:
            invite_link = "https://t.me/+invite"
        return _L()


async def _seed_seasons() -> None:
    async with session_scope() as session:
        session.add(Season(
            season_id="sweet", title="Сладкая империя", price=299, price_subscriber=179,
            archive_link="https://drive/sweet", workbook_link="https://drive/sweet_wb", is_current=True,
        ))
        session.add(Season(
            season_id="all", title="Все сезоны", price=999, price_subscriber=599,
            archive_link="https://drive/all", is_current=False,
        ))


async def test_trial_once(db):
    assert await users.can_trial(50) is True
    until = await users.grant_trial(50, 24)
    assert until is not None
    assert await users.is_subscribed(50) is True
    assert await users.can_trial(50) is False
    assert await users.grant_trial(50, 24) is None


async def test_subscription_until(db):
    await users.grant_subscription(60, 30)
    until = await users.subscription_until(60)
    assert until is not None
    assert await users.subscription_until(61) is None


async def test_subscription_renewal_stacks(db):
    first = await users.grant_subscription(65, 30)
    second = await users.grant_subscription(65, 30)
    assert (second - first).days >= 29


async def test_catalog_excludes_all_pack(db):
    await _seed_seasons()
    ids = [s["season_id"] for s in await catalog.all_seasons()]
    assert "sweet" in ids and "all" not in ids
    pack = await catalog.all_seasons_pack()
    assert pack is not None and pack["season_id"] == "all"
    wbs = [s["season_id"] for s in await catalog.sellable_workbooks()]
    assert wbs == ["sweet"]


async def test_fulfill_sub_3m(db):
    await _seed_seasons()
    bot = FakeBot()
    ok = await fulfillment.fulfill(bot, "pay-sub3", {"kind": "sub", "tg_id": 70, "days": 90}, 1890, "RUB")
    assert ok is True
    assert await users.is_subscribed(70) is True
    async with session_scope() as session:
        item = await session.scalar(select(Sale.item).where(Sale.tg_id == 70))
    assert item == "subscription_3m"


async def test_fulfill_season_and_idempotent(db):
    await _seed_seasons()
    bot = FakeBot()
    ok = await fulfillment.fulfill(bot, "pay-season", {"kind": "season", "season_id": "sweet", "tg_id": 71}, 299, "RUB")
    assert ok is True
    assert await users.has_season(71, "sweet") is True
    # повторный вебхук с тем же payment_id не выдаёт повторно
    meta = {"kind": "season", "season_id": "sweet", "tg_id": 71}
    again = await fulfillment.fulfill(bot, "pay-season", meta, 299, "RUB")
    assert again is False


async def test_fulfill_workbook(db):
    await _seed_seasons()
    bot = FakeBot()
    ok = await fulfillment.fulfill(bot, "pay-wb", {"kind": "workbook", "season_id": "sweet", "tg_id": 72}, 599, "RUB")
    assert ok is True
    assert any("тетрад" in text.lower() for _, text in bot.sent)


async def test_fulfill_all_grants_everything(db):
    await _seed_seasons()
    bot = FakeBot()
    ok = await fulfillment.fulfill(bot, "pay-all", {"kind": "all", "tg_id": 73}, 999, "RUB")
    assert ok is True
    assert await users.has_season(73, "sweet") is True
    assert await users.has_season(73, "cola") is True


async def test_contacts_dedupe(db):
    await contacts.record(80, name="Лев", source="start")
    await contacts.record(80, name="Лев", source="keyword")
    async with session_scope() as session:
        count = await session.scalar(select(func.count()).select_from(Contact).where(Contact.tg_id == 80))
    assert count == 1


async def _reserved(payment_id: str) -> bool:
    async with session_scope() as session:
        row = await session.scalar(
            select(ProcessedPayment).where(ProcessedPayment.provider_payment_id == payment_id)
        )
    return row is not None


async def test_fulfill_releases_reservation_on_grant_failure(db, monkeypatch):
    await _seed_seasons()
    bot = FakeBot()

    async def boom(*a, **k):
        raise RuntimeError("БД недоступна")

    monkeypatch.setattr(users, "grant_subscription", boom)
    meta = {"kind": "sub", "tg_id": 90, "days": 30}
    try:
        await fulfillment.fulfill(bot, "pay-fail", meta, 790, "RUB")
        raised = False
    except RuntimeError:
        raised = True
    assert raised is True
    assert await _reserved("pay-fail") is False

    monkeypatch.undo()
    ok = await fulfillment.fulfill(bot, "pay-fail", meta, 790, "RUB")
    assert ok is True
    assert await users.is_subscribed(90) is True


async def test_fulfill_send_failure_still_grants(db):
    await _seed_seasons()

    class RaisingBot(FakeBot):
        async def send_message(self, chat_id, text, **kwargs):
            raise RuntimeError("user blocked bot")

    bot = RaisingBot()
    meta = {"kind": "season", "season_id": "sweet", "tg_id": 91}
    ok = await fulfillment.fulfill(bot, "pay-send", meta, 299, "RUB")
    assert ok is True
    assert await users.has_season(91, "sweet") is True
    assert await _reserved("pay-send") is True
    again = await fulfillment.fulfill(bot, "pay-send", meta, 299, "RUB")
    assert again is False
