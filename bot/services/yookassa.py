from __future__ import annotations

import base64
import uuid
from typing import Any

import httpx
from loguru import logger

from config import get_settings

API_URL = "https://api.yookassa.ru/v3/payments"


class YooKassaNotConfigured(RuntimeError):
    pass


def _auth_header() -> str:
    settings = get_settings()
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        raise YooKassaNotConfigured("YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY не заданы")
    raw = f"{settings.yookassa_shop_id}:{settings.yookassa_secret_key}".encode()
    return "Basic " + base64.b64encode(raw).decode("ascii")


async def create_payment(
    amount_rub: int,
    description: str,
    metadata: dict[str, Any],
    return_url: str,
) -> dict[str, Any]:
    headers = {
        "Authorization": _auth_header(),
        "Idempotence-Key": uuid.uuid4().hex,
        "Content-Type": "application/json",
    }
    body = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
        "metadata": metadata,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(API_URL, headers=headers, json=body)
        if response.status_code >= 400:
            logger.error("YooKassa {}: {}", response.status_code, response.text)
        response.raise_for_status()
        return response.json()


async def get_payment(payment_id: str) -> dict[str, Any]:
    headers = {"Authorization": _auth_header()}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{API_URL}/{payment_id}", headers=headers)
        response.raise_for_status()
        return response.json()


def confirmation_url(payment: dict[str, Any]) -> str:
    return payment.get("confirmation", {}).get("confirmation_url", "")
