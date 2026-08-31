from __future__ import annotations

from bot.services import admin_content, catalog


async def test_new_current_season_replaces_previous(db):
    await admin_content.add_season(["sweet", "Сладкая империя", "299", "179", "https://a", "1"])
    assert (await catalog.current_season())["season_id"] == "sweet"

    await admin_content.add_season(["cola", "Газировка", "299", "179", "https://b", "1"])
    current = await catalog.current_season()
    assert current["season_id"] == "cola"

    old = await catalog.get_season("sweet")
    assert old["is_current"] is False


async def test_season_added_as_not_current_keeps_previous(db):
    await admin_content.add_season(["sweet", "Сладкая империя", "299", "179", "https://a", "1"])
    await admin_content.add_season(["cola", "Газировка", "299", "179", "https://b", "0"])
    assert (await catalog.current_season())["season_id"] == "sweet"
