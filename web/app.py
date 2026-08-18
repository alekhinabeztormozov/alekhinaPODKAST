from __future__ import annotations

from aiogram import Bot
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from loguru import logger

from bot.main import build_bot
from bot.services import fulfillment, vk, vk_bot, yookassa
from config import get_settings

app = FastAPI(title="alekhina-bot", version="0.2.0")

_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = build_bot(get_settings())
    return _bot


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/payments/yookassa")
async def yookassa_webhook(request: Request) -> dict[str, str]:
    try:
        data = await request.json()
    except Exception:
        return {"status": "bad_request"}

    payment_id = data.get("object", {}).get("id")
    if not payment_id:
        return {"status": "ignored"}

    try:
        payment = await yookassa.get_payment(payment_id)
    except Exception as exc:
        logger.error("YooKassa get_payment {} упал: {}", payment_id, exc)
        return {"status": "error"}

    if payment.get("status") != "succeeded" or not payment.get("paid"):
        return {"status": "pending"}

    metadata = payment.get("metadata", {})
    amount = int(float(payment.get("amount", {}).get("value", "0")))
    currency = payment.get("amount", {}).get("currency", "RUB")
    try:
        await fulfillment.fulfill(_get_bot(), payment_id, metadata, amount, currency)
    except Exception as exc:
        logger.error("Выдача по платежу {} упала: {}", payment_id, exc)
    return {"status": "ok"}


@app.post("/vk/callback")
async def vk_callback(request: Request) -> PlainTextResponse:
    if not vk.is_configured():
        return PlainTextResponse("ok")
    try:
        data = await request.json()
    except Exception:
        return PlainTextResponse("ok")

    if data.get("type") == "confirmation":
        return PlainTextResponse(get_settings().vk_confirmation_token or "ok")

    if not vk.check_secret(data.get("secret")):
        logger.warning("VK callback: неверный secret")
        return PlainTextResponse("ok")

    if data.get("type") == "message_new":
        obj = data.get("object", {})
        message = obj.get("message", obj)
        text = message.get("text", "")
        payload = message.get("payload", "")
        peer_id = message.get("peer_id") or message.get("from_id")
        from_id = message.get("from_id", 0)
        if peer_id:
            try:
                await vk_bot.handle_incoming(text, int(peer_id), int(from_id), payload=payload)
            except Exception as exc:
                logger.error("VK message_new обработка упала: {}", exc)

    return PlainTextResponse("ok")
