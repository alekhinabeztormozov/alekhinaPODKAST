from __future__ import annotations

import asyncio

from sqlalchemy import select

from db.models import Bonus, Episode, MainProduct, Season
from db.session import init_models, session_scope

SEASONS = [
    dict(season_id="sweet", title="Сладкая империя", description="Разбор брендов сладостей.",
         price=299, price_subscriber=179, archive_link="https://drive.google.com/drive/folders/xxxx",
         is_current=True),
]
EPISODES = [
    dict(episode_id="sweet_nutella", season_id="sweet",
         title="Nutella: почему ты ешь её ложкой из банки",
         audio_link="https://example.com/nutella.mp3",
         tags=["nutella", "шоколад", "паста", "детство", "якорь любви"]),
]
BONUSES = [
    dict(bonus_id="bonus_nutella", season_id="sweet", keyword="НУТЕЛЛА",
         title="Три ошибки в нейминге сладостей",
         pdf_link="https://drive.google.com/nutella_bonus.pdf",
         audio_link="https://example.com/nutella_bonus.mp3",
         tags=["нейминг", "сладости", "ошибки"]),
]
PRODUCTS = [
    dict(product_id="intensive_sweet", season_id="sweet",
         title="Шоколадная битва: создай свой ритуал", description="3-часовой интенсив.",
         price=3900, price_subscriber=2730, payment_link="https://example.com/payment", is_active=True),
]


async def _upsert(session, model, key_field, rows):
    added = 0
    for row in rows:
        exists = await session.scalar(select(model).where(getattr(model, key_field) == row[key_field]))
        if exists is None:
            session.add(model(**row))
            added += 1
    return added


async def main() -> None:
    await init_models()
    async with session_scope() as session:
        n = 0
        n += await _upsert(session, Season, "season_id", SEASONS)
        n += await _upsert(session, Episode, "episode_id", EPISODES)
        n += await _upsert(session, Bonus, "bonus_id", BONUSES)
        n += await _upsert(session, MainProduct, "product_id", PRODUCTS)
    print(f"seed: добавлено {n} записей")


if __name__ == "__main__":
    asyncio.run(main())
