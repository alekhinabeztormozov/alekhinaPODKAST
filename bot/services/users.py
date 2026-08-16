from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from db.models import User
from db.session import session_scope


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _is_active(user: User) -> bool:
    if not user.is_subscribed:
        return False
    expires = _aware(user.subscription_expires)
    return expires is None or expires > _now()


async def get_or_create(tg_id: int, username: str = "") -> dict:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            user = User(tg_id=tg_id, username=username)
            session.add(user)
            await session.flush()
        elif username and user.username != username:
            user.username = username
        return _snapshot(user)


async def is_subscribed(tg_id: int) -> bool:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None or not user.is_subscribed:
            return False
        if not _is_active(user):
            user.is_subscribed = False
            return False
        return True


async def subscription_until(tg_id: int) -> datetime | None:
    """Дата окончания активной подписки (или None, если не активна)."""
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None or not _is_active(user):
            return None
        return _aware(user.subscription_expires)


async def can_trial(tg_id: int) -> bool:
    """Триал доступен, если ещё не брал и сейчас не подписан."""
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            return True
        return not user.trial_used and not _is_active(user)


async def grant_trial(tg_id: int, hours: int, username: str = "") -> datetime | None:
    """Выдать 24ч триал клуба. None, если триал уже брали или подписка активна."""
    expires = _now() + timedelta(hours=hours)
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            user = User(tg_id=tg_id, username=username)
            session.add(user)
        if user.trial_used or _is_active(user):
            return None
        user.is_subscribed = True
        user.subscription_expires = expires
        user.trial_used = True
    return expires


async def grant_subscription(tg_id: int, days: int, username: str = "") -> datetime:
    expires = _now() + timedelta(days=days)
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            user = User(tg_id=tg_id, username=username)
            session.add(user)
        user.is_subscribed = True
        user.subscription_expires = expires
    return expires


async def add_purchased_season(tg_id: int, season_id: str) -> None:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            user = User(tg_id=tg_id, purchased_seasons=[season_id])
            session.add(user)
            return
        owned = list(user.purchased_seasons or [])
        if season_id not in owned:
            owned.append(season_id)
            user.purchased_seasons = owned


async def has_season(tg_id: int, season_id: str) -> bool:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        owned = list(user.purchased_seasons or []) if user else []
        return season_id in owned or "all" in owned


async def all_user_ids() -> list[int]:
    async with session_scope() as session:
        result = await session.execute(select(User.tg_id))
        return [row[0] for row in result.all()]


async def subscriber_ids() -> list[int]:
    async with session_scope() as session:
        result = await session.execute(
            select(User.tg_id)
            .where(User.is_subscribed.is_(True))
            .where(User.subscription_expires > _now())
        )
        return [row[0] for row in result.all()]


async def take_voice_demo(tg_id: int) -> bool:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            user = User(tg_id=tg_id, got_voice_demo=True)
            session.add(user)
            return True
        if user.got_voice_demo:
            return False
        user.got_voice_demo = True
        return True


async def expired_subscribers(now: datetime | None = None) -> list[int]:
    moment = now or _now()
    async with session_scope() as session:
        result = await session.execute(
            select(User.tg_id)
            .where(User.is_subscribed.is_(True))
            .where(User.subscription_expires <= moment)
        )
        return [row[0] for row in result.all()]


async def drop_subscription(tg_id: int) -> None:
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is not None:
            user.is_subscribed = False


def _snapshot(user: User) -> dict:
    return {
        "tg_id": user.tg_id,
        "username": user.username,
        "is_subscribed": user.is_subscribed,
        "subscription_expires": user.subscription_expires,
        "purchased_seasons": list(user.purchased_seasons or []),
        "got_voice_demo": user.got_voice_demo,
        "trial_used": user.trial_used,
    }
