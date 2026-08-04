from __future__ import annotations

import asyncio

from bot.main import build_bot
from config import get_settings


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан — заполни .env")

    bot = build_bot(settings)
    try:
        me = await bot.get_me()
        print(f"bot: @{me.username} id={me.id}")

        updates = await bot.get_updates(timeout=1)
        if not updates:
            print("Апдейтов нет. Отправь пост в закрытый канал (или /start боту) и запусти снова.")
            return

        chats: dict[int, str] = {}
        users: dict[int, str] = {}
        for update in updates:
            for obj in (update.my_chat_member, update.channel_post, update.message):
                if obj is None:
                    continue
                chat = getattr(obj, "chat", None)
                if chat is not None:
                    chats[chat.id] = f"type={chat.type} title={chat.title or ''} @{chat.username or ''}"
                author = getattr(obj, "from_user", None)
                if author is not None:
                    users[author.id] = f"@{author.username or ''} {author.full_name}"

        for chat_id, info in chats.items():
            print(f"chat: id={chat_id} {info}")
        for user_id, info in users.items():
            print(f"user: id={user_id} {info}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
