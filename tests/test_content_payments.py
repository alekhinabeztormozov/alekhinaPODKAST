from __future__ import annotations

from bot.content import DEFAULT_QUIZ, SHOP_ITEMS, find_item, quiz_result
from bot.services.payments import item_prices, subscription_prices
from config import Settings


def test_quiz_result_stable_verdict():
    result = quiz_result([0, 1, 2, 0, 1])
    assert result.startswith("Результат теста")


def test_quiz_has_five_questions():
    assert len(DEFAULT_QUIZ.questions) == 5


def test_find_item_known_and_unknown():
    assert find_item(SHOP_ITEMS[0].id) is SHOP_ITEMS[0]
    assert find_item("nope") is None


def test_stars_amount_is_value():
    settings = Settings(payment_currency="XTR", subscription_price=200)
    prices = subscription_prices(settings)
    assert prices[0].amount == 200


def test_fiat_amount_in_kopecks():
    settings = Settings(payment_currency="RUB", subscription_price=200)
    prices = subscription_prices(settings)
    assert prices[0].amount == 20000


def test_item_price_currency_aware():
    settings = Settings(payment_currency="RUB")
    price = item_prices(SHOP_ITEMS[0], settings)[0].amount
    assert price == SHOP_ITEMS[0].price * 100
