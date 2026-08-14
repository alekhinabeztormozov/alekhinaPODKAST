from __future__ import annotations

from typing import Any

from sqlalchemy import select

from db.models import Bonus, Episode, MainProduct, Season
from db.session import session_scope


def _bonus(b: Bonus) -> dict[str, Any]:
    return {
        "bonus_id": b.bonus_id,
        "season_id": b.season_id,
        "keyword": b.keyword,
        "title": b.title,
        "pdf_link": b.pdf_link,
        "audio_link": b.audio_link,
        "tags": list(b.tags or []),
    }


def _season(s: Season) -> dict[str, Any]:
    return {
        "season_id": s.season_id,
        "title": s.title,
        "description": s.description,
        "price": s.price,
        "price_subscriber": s.price_subscriber,
        "archive_link": s.archive_link,
        "is_current": s.is_current,
    }


def _episode(e: Episode) -> dict[str, Any]:
    return {
        "episode_id": e.episode_id,
        "season_id": e.season_id,
        "title": e.title,
        "audio_link": e.audio_link,
        "tags": list(e.tags or []),
    }


async def bonus_by_keyword(keyword: str) -> dict[str, Any] | None:
    key = keyword.strip().lower()
    async with session_scope() as session:
        rows = (await session.execute(select(Bonus))).scalars().all()
    for row in rows:
        if row.keyword.strip().lower() == key:
            return _bonus(row)
    return None


def _product(p: MainProduct) -> dict[str, Any]:
    return {
        "product_id": p.product_id,
        "season_id": p.season_id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "price_subscriber": p.price_subscriber,
        "payment_link": p.payment_link,
    }


async def active_main_product(season_id: str | None = None) -> dict[str, Any] | None:
    async with session_scope() as session:
        query = select(MainProduct).where(MainProduct.is_active.is_(True))
        if season_id:
            query = query.where(MainProduct.season_id == season_id)
        row = await session.scalar(query)
        return _product(row) if row else None


async def bonus_by_id(bonus_id: str) -> dict[str, Any] | None:
    async with session_scope() as session:
        row = await session.scalar(select(Bonus).where(Bonus.bonus_id == bonus_id))
        return _bonus(row) if row else None


async def current_season() -> dict[str, Any] | None:
    async with session_scope() as session:
        row = await session.scalar(select(Season).where(Season.is_current.is_(True)))
        return _season(row) if row else None


async def get_season(season_id: str) -> dict[str, Any] | None:
    async with session_scope() as session:
        row = await session.scalar(select(Season).where(Season.season_id == season_id))
        return _season(row) if row else None


async def all_seasons() -> list[dict[str, Any]]:
    async with session_scope() as session:
        rows = (await session.execute(select(Season))).scalars().all()
        return [_season(s) for s in rows]


async def season_bonuses(season_id: str) -> list[dict[str, Any]]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(Bonus).where(Bonus.season_id == season_id))
        ).scalars().all()
        return [_bonus(b) for b in rows]


def _matches(query: str, title: str, tags: list[str]) -> bool:
    q = query.strip().lower()
    if q in title.lower():
        return True
    return any(q in str(t).lower() for t in tags)


async def search(query: str, limit: int = 3) -> list[dict[str, Any]]:
    async with session_scope() as session:
        episodes = (await session.execute(select(Episode))).scalars().all()
        bonuses = (await session.execute(select(Bonus))).scalars().all()

    results: list[dict[str, Any]] = []
    for e in episodes:
        if _matches(query, e.title, list(e.tags or [])):
            item = _episode(e)
            item["kind"] = "episode"
            results.append(item)
    for b in bonuses:
        if _matches(query, b.title, list(b.tags or [])):
            item = _bonus(b)
            item["kind"] = "bonus"
            results.append(item)
    return results[:limit]
