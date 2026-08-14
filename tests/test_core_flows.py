from __future__ import annotations

from bot.services import catalog, users
from db.models import Bonus, Episode, Season
from db.session import session_scope


async def _seed() -> None:
    async with session_scope() as session:
        session.add(Season(
            season_id="sweet", title="Сладкая империя", price=299, price_subscriber=179,
            archive_link="https://drive/x", is_current=True,
        ))
        session.add(Bonus(
            bonus_id="b1", season_id="sweet", keyword="НУТЕЛЛА", title="Три ошибки в нейминге",
            pdf_link="https://p", audio_link="https://a", tags=["нейминг"],
        ))
        session.add(Episode(
            episode_id="e1", season_id="sweet", title="Nutella ложкой", audio_link="https://au",
            tags=["шоколад", "паста"],
        ))


async def test_keyword_bonus_cyrillic(db):
    await _seed()
    bonus = await catalog.bonus_by_keyword("нутелла")
    assert bonus is not None and bonus["title"] == "Три ошибки в нейминге"
    assert await catalog.bonus_by_keyword("нетакого") is None


async def test_search_by_tag_and_title(db):
    await _seed()
    by_tag = await catalog.search("шоколад")
    assert any(item["kind"] == "episode" for item in by_tag)
    by_title = await catalog.search("нейминг")
    assert any(item["kind"] == "bonus" for item in by_title)


async def test_subscription_lifecycle(db):
    await users.get_or_create(5, "u")
    assert await users.is_subscribed(5) is False
    await users.grant_subscription(5, 30)
    assert await users.is_subscribed(5) is True


async def test_season_purchase(db):
    await users.add_purchased_season(7, "sweet")
    assert await users.has_season(7, "sweet") is True
    assert await users.has_season(7, "cola") is False


async def test_voice_demo_once(db):
    assert await users.take_voice_demo(9) is True
    assert await users.take_voice_demo(9) is False
