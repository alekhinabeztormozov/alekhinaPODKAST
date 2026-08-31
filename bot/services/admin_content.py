from __future__ import annotations

from sqlalchemy import func, select, update

from db.models import Bonus, Episode, MainProduct, Season
from db.session import session_scope


def _tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


async def _upsert(model, key_field: str, key: str, values: dict) -> str:
    async with session_scope() as session:
        row = await session.scalar(select(model).where(getattr(model, key_field) == key))
        if row is None:
            session.add(model(**{key_field: key}, **values))
            return "добавлено"
        for field, value in values.items():
            setattr(row, field, value)
        return "обновлено"


async def add_season(parts: list[str]) -> str:
    season_id, title, price, price_sub, archive, is_current = parts
    current = is_current.strip() in {"1", "да", "true"}
    result = await _upsert(Season, "season_id", season_id, dict(
        title=title, price=int(price), price_subscriber=int(price_sub),
        archive_link=archive, is_current=current,
    ))
    if current:
        await _make_only_current(season_id)
    return result


async def _make_only_current(season_id: str) -> None:
    """Текущий сезон ровно один: current_season() берёт первую попавшуюся строку с флагом."""
    async with session_scope() as session:
        await session.execute(
            update(Season)
            .where(Season.season_id != season_id)
            .where(Season.is_current.is_(True))
            .values(is_current=False)
        )


async def add_bonus(parts: list[str]) -> str:
    bonus_id, season_id, keyword, title, pdf, audio = parts
    return await _upsert(Bonus, "bonus_id", bonus_id, dict(
        season_id=season_id, keyword=keyword, title=title, pdf_link=pdf, audio_link=audio,
    ))


async def add_episode(parts: list[str]) -> str:
    episode_id, season_id, title, audio, tags = parts
    return await _upsert(Episode, "episode_id", episode_id, dict(
        season_id=season_id, title=title, audio_link=audio, tags=_tags(tags),
    ))


async def add_product(parts: list[str]) -> str:
    product_id, season_id, title, price, price_sub, link, is_active = parts
    return await _upsert(MainProduct, "product_id", product_id, dict(
        season_id=season_id, title=title, price=int(price), price_subscriber=int(price_sub),
        payment_link=link, is_active=is_active.strip() in {"1", "да", "true"},
    ))


async def set_workbook(parts: list[str]) -> str:
    season_id, link = parts
    async with session_scope() as session:
        row = await session.scalar(select(Season).where(Season.season_id == season_id))
        if row is None:
            raise ValueError(f"Сезон «{season_id}» не найден — сперва /add_season")
        row.workbook_link = link
    return f"тетрадь для «{season_id}» сохранена"


async def counts() -> dict[str, int]:
    async with session_scope() as session:
        seasons = await session.scalar(select(func.count()).select_from(Season))
        episodes = await session.scalar(select(func.count()).select_from(Episode))
        bonuses = await session.scalar(select(func.count()).select_from(Bonus))
        products = await session.scalar(select(func.count()).select_from(MainProduct))
    return {"seasons": seasons or 0, "episodes": episodes or 0,
            "bonuses": bonuses or 0, "products": products or 0}
