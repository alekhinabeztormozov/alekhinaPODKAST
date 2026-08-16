from __future__ import annotations

from loguru import logger
from sqlalchemy import select

from bot.services import sheets
from db.models import Contact
from db.session import DatabaseNotConfigured, session_scope


async def record(tg_id: int, name: str = "", source: str = "", email: str = "", quiz_result: str = "") -> None:
    """Записать контакт в БД + Google Sheets. Один пользователь = одна строка (дедуп по tg_id).

    В Sheets пишем только при первой фиксации, чтобы не плодить дубли (спека 4.6/5.5).
    """
    inserted = False
    try:
        async with session_scope() as session:
            exists = await session.scalar(select(Contact).where(Contact.tg_id == tg_id))
            if exists is None:
                session.add(
                    Contact(tg_id=tg_id, name=name, source=source, email=email, quiz_result=quiz_result)
                )
                inserted = True
    except DatabaseNotConfigured:
        return
    except Exception as exc:
        logger.error("Запись контакта {} упала: {}", tg_id, exc)
        return
    if inserted:
        await sheets.add_contact(tg_id, name, email, source, quiz_result)
