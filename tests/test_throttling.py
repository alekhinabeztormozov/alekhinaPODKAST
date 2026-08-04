from __future__ import annotations

import types

from bot.middlewares.throttling import ThrottlingMiddleware


async def test_second_call_suppressed():
    middleware = ThrottlingMiddleware(interval=10)
    calls: list[int] = []

    async def handler(event, data):
        calls.append(1)
        return "ok"

    user = types.SimpleNamespace(id=42)
    data = {"event_from_user": user}

    first = await middleware(handler, object(), data)
    second = await middleware(handler, object(), data)

    assert first == "ok"
    assert second is None
    assert len(calls) == 1


async def test_missing_user_passes_through():
    middleware = ThrottlingMiddleware(interval=10)
    calls: list[int] = []

    async def handler(event, data):
        calls.append(1)
        return "ok"

    result = await middleware(handler, object(), {})
    assert result == "ok"
    assert len(calls) == 1
