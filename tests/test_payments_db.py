from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from bot.services import sales
from db.models import ProcessedPayment, Sale
from db.session import session_scope


async def test_payment_idempotency(db):
    """Уникальность provider_payment_id — на ней держится защита от повторной выдачи."""
    async with session_scope() as session:
        session.add(ProcessedPayment(provider_payment_id="charge_x", tg_id=1, kind="sub"))
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            session.add(ProcessedPayment(provider_payment_id="charge_x", tg_id=1, kind="sub"))


async def test_sale_recorded_in_db(db):
    assert await sales.record(7, "starbucks", 30, "RUB") is True
    async with session_scope() as session:
        count = await session.scalar(select(func.count()).select_from(Sale))
    assert count == 1
