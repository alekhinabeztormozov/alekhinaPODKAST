from __future__ import annotations

from sqlalchemy import select

from db.models import SeenKey
from db.session import session_scope


async def is_seen(kind: str, key: str) -> bool:
    async with session_scope() as session:
        result = await session.execute(
            select(SeenKey.id).where(SeenKey.kind == kind).where(SeenKey.key == key)
        )
        return result.first() is not None


async def mark_seen(kind: str, key: str) -> bool:
    if await is_seen(kind, key):
        return False
    async with session_scope() as session:
        session.add(SeenKey(kind=kind, key=key))
    return True
