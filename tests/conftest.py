from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./.pytest_cache/test.db")
os.environ.setdefault("PAYMENT_CURRENCY", "XTR")

import pytest_asyncio

Path(".pytest_cache").mkdir(exist_ok=True)


@pytest_asyncio.fixture
async def db():
    from db.models import Base
    from db.session import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
