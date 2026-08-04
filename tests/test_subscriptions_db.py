from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from bot.services import subscriptions
from db.models import ProcessedPayment, Subscription
from db.session import session_scope


async def test_grant_and_active(db):
    await subscriptions.grant(1, days=30, status="active")
    assert await subscriptions.is_active(1) is True
    assert await subscriptions.is_active(2) is False


async def test_trial_tracking(db):
    assert await subscriptions.has_used_trial(3) is False
    await subscriptions.grant(3, days=1, status="trial")
    assert await subscriptions.has_used_trial(3) is True


async def test_expiry_and_revoke(db):
    past = datetime.now(UTC) - timedelta(days=1)
    async with session_scope() as session:
        session.add(Subscription(tg_id=9, status="active", expires_at=past))
    assert 9 in await subscriptions.expired()
    await subscriptions.mark_expired(9)
    assert 9 not in await subscriptions.expired()


async def test_payment_idempotency(db):
    async with session_scope() as session:
        session.add(ProcessedPayment(provider_payment_id="charge_x", tg_id=1, kind="sub"))
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            session.add(ProcessedPayment(provider_payment_id="charge_x", tg_id=1, kind="sub"))


async def test_sale_recorded_in_db(db):
    from sqlalchemy import func, select

    from bot.services import sales
    from db.models import Sale

    assert await sales.record(7, "starbucks", 30, "RUB") is True
    async with session_scope() as session:
        count = await session.scalar(select(func.count()).select_from(Sale))
    assert count == 1
