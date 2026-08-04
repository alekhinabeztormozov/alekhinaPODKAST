from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from db.models import Subscription
from db.session import session_scope


def _now() -> datetime:
    return datetime.now(UTC)


async def grant(tg_id: int, days: int, status: str = "active") -> datetime:
    expires_at = _now() + timedelta(days=days)
    async with session_scope() as session:
        session.add(Subscription(tg_id=tg_id, status=status, expires_at=expires_at))
    return expires_at


async def is_active(tg_id: int) -> bool:
    async with session_scope() as session:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.tg_id == tg_id)
            .where(Subscription.status.in_(("active", "trial")))
            .where(Subscription.expires_at > _now())
        )
        return result.first() is not None


async def has_used_trial(tg_id: int) -> bool:
    async with session_scope() as session:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.tg_id == tg_id)
            .where(Subscription.status == "trial")
        )
        return result.first() is not None


async def expired(now: datetime | None = None) -> list[int]:
    moment = now or _now()
    async with session_scope() as session:
        result = await session.execute(
            select(Subscription.tg_id)
            .where(Subscription.status.in_(("active", "trial")))
            .where(Subscription.expires_at <= moment)
        )
        return [row[0] for row in result.all()]


async def mark_expired(tg_id: int) -> None:
    async with session_scope() as session:
        await session.execute(
            update(Subscription)
            .where(Subscription.tg_id == tg_id)
            .where(Subscription.status.in_(("active", "trial")))
            .values(status="expired")
        )
