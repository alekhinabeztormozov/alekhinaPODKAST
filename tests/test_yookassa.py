from __future__ import annotations

from bot.services.yookassa import confirmation_url


def test_confirmation_url_extracted():
    payment = {"confirmation": {"type": "redirect", "confirmation_url": "https://pay/x"}}
    assert confirmation_url(payment) == "https://pay/x"


def test_confirmation_url_missing():
    assert confirmation_url({}) == ""
    assert confirmation_url({"confirmation": {}}) == ""
