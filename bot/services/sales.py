from __future__ import annotations

from loguru import logger

from db.models import Sale
from db.session import DatabaseNotConfigured, session_scope


async def record(tg_id: int, item: str, amount: int, currency: str = "XTR", status: str = "paid") -> bool:
    try:
        async with session_scope() as session:
            session.add(Sale(tg_id=tg_id, item=item, amount=amount, currency=currency, status=status))
        return True
    except DatabaseNotConfigured:
        logger.warning("БД не настроена — продажа не записана")
        return False
    except Exception as exc:
        logger.error("Запись продажи упала: {}", exc)
        return False
