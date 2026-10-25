from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from db.models import Reel
from db.session import session_scope

MSK = ZoneInfo("Europe/Moscow")
DAYS_AHEAD = 60

DRAFT = "draft"
NEED_TRACK = "need_track"
APPROVED = "approved"
RENDERING = "rendering"
READY = "ready"
PUBLISHED = "published"
REJECTED = "rejected"
FAILED = "failed"

STATUS_TITLES = {
    DRAFT: "на проверке",
    NEED_TRACK: "ждут трек",
    APPROVED: "в очереди на сборку",
    RENDERING: "собираются",
    READY: "готовы, ждут слот",
    PUBLISHED: "вышли",
    FAILED: "ошибка сборки",
}


async def add_drafts(episode_ref: str, episode_title: str, scenarios: list[dict]) -> list[int]:
    async with session_scope() as session:
        reels = [
            Reel(episode_ref=episode_ref, episode_title=episode_title, kind=item["kind"], scenario=item, published=[])
            for item in scenarios
        ]
        session.add_all(reels)
        await session.flush()
        return [reel.id for reel in reels]


async def get(reel_id: int) -> Reel | None:
    async with session_scope() as session:
        return await session.get(Reel, reel_id)


async def update(reel_id: int, **fields) -> Reel | None:
    async with session_scope() as session:
        reel = await session.get(Reel, reel_id)
        if reel is None:
            return None
        for name, value in fields.items():
            setattr(reel, name, value)
        return reel


async def approve(reel_id: int) -> Reel | None:
    reel = await get(reel_id)
    if reel is None:
        return None
    needs_track = reel.kind == "trigger_song" and not reel.track_path
    return await update(reel_id, status=NEED_TRACK if needs_track else APPROVED, error="")


async def with_status(*statuses: str) -> list[Reel]:
    async with session_scope() as session:
        result = await session.execute(select(Reel).where(Reel.status.in_(statuses)).order_by(Reel.id))
        return list(result.scalars().all())


async def counts() -> dict[str, int]:
    totals: dict[str, int] = {}
    for reel in await with_status(*STATUS_TITLES):
        totals[reel.status] = totals.get(reel.status, 0) + 1
    return totals


async def episode_refs() -> list[str]:
    async with session_scope() as session:
        result = await session.execute(select(Reel.episode_ref).distinct())
        return [row for row in result.scalars().all()]


async def due(now: datetime) -> list[Reel]:
    async with session_scope() as session:
        result = await session.execute(
            select(Reel).where(Reel.status == READY).where(Reel.publish_at <= now).order_by(Reel.publish_at)
        )
        return list(result.scalars().all())


async def published_since(moment: datetime) -> list[Reel]:
    async with session_scope() as session:
        result = await session.execute(
            select(Reel).where(Reel.status == PUBLISHED).where(Reel.updated_at >= moment).order_by(Reel.publish_at)
        )
        return list(result.scalars().all())


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def slot_candidates(after: datetime, slots: list[tuple[int, int]]):
    local = after.astimezone(MSK)
    for day in range(DAYS_AHEAD):
        date = (local + timedelta(days=day)).date()
        for hours, minutes in slots:
            moment = datetime(date.year, date.month, date.day, hours, minutes, tzinfo=MSK)
            if moment > local:
                yield moment.astimezone(UTC)


def next_free_slot(after: datetime, slots: list[tuple[int, int]], taken: set[datetime]) -> datetime:
    taken_utc = {_as_utc(moment) for moment in taken}
    for candidate in slot_candidates(after, slots):
        if candidate not in taken_utc:
            return candidate
    raise RuntimeError("нет свободных слотов на 60 дней вперед")


async def schedule(reel_id: int, slots: list[tuple[int, int]], now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    taken = {reel.publish_at for reel in await with_status(READY) if reel.publish_at}
    slot = next_free_slot(now, slots, taken)
    await update(reel_id, status=READY, publish_at=slot)
    return slot
