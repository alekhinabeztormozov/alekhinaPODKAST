from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from db.models import User
from db.session import session_scope


def _now() -> datetime:
    return datetime.now(UTC)


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
        expires = user.subscription_expires
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires is not None and expires <= _now():
            user.is_subscribed = False
            return False
        return True


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
        return bool(user and season_id in (user.purchased_seasons or []))


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
    }
