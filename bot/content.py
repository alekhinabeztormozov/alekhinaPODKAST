from __future__ import annotations

from dataclasses import dataclass, field

WELCOME = (
    "<b>Алёхина без тормозов</b>\n\n"
    "Бизнес-разборы, стратегии и инструменты без воды.\n"
    "Выбирай, с чего начать:"
)

MENU_HINT = "Выбери раздел:"

OWNER_PANEL = (
    "<b>Панель владельца</b>\n\n"
    "Здесь ты готовишь контент. Клиенты видят другое меню — кнопка «Клиентский вид».\n\n"
    "• <b>Эпизод</b>: пришли сюда аудио (файл или голосовое) — бот наложит фон и вернёт готовый выпуск для Podster.\n"
    "• <b>Гайд</b>: пришли текст (первая строка — заголовок) — бот вернёт стилизованный PDF.\n"
    "• <b>Эмбиенты</b>: послушать фоновые подложки.\n"
    "• <code>/admin</code> — статистика, <code>/setup_notion</code>, <code>/setup_sheets</code> — разовая настройка."
)

OWNER_AUDIO_HINT = "Пришли аудио эпизода — файлом или голосовым. Дальше выберешь фон, и бот вернёт готовый mp3."
OWNER_GUIDE_HINT = "Пришли текст гайда одним сообщением. Первая строка станет заголовком, остальное — телом PDF."

PDF_ASK_EMAIL = (
    "Пришли свой email, чтобы получить бонус и не потерять доступ.\n"
    "Можно пропустить кнопкой ниже."
)

PDF_DELIVERED = (
    "Готово! Твой PDF-бонус: {link}\n\n"
    "Хочешь глубже? В закрытом канале — детальные разборы компаний и аудиобонусы."
)

CLOSED_INTRO = (
    "<b>Закрытый канал</b>\n\n"
    "Детальные разборы, аудиобонусы, инструменты. "
    "Подписка {price} ₽/мес.\n"
    "Первый день — бесплатно, чтобы посмотреть изнутри."
)

SHOP_INTRO = "<b>Магазин гайдов</b>\n\nВыбирай разбор — файл придёт сразу после оплаты."

ADMIN_DENIED = "Недостаточно прав."


@dataclass(frozen=True)
class GuideItem:
    id: str
    title: str
    price: int
    payload_file: str = ""


@dataclass(frozen=True)
class QuizQuestion:
    text: str
    options: list[str]


@dataclass(frozen=True)
class QuizSet:
    brand: str
    questions: list[QuizQuestion] = field(default_factory=list)


SHOP_ITEMS: list[GuideItem] = [
    GuideItem(id="starbucks", title="Starbucks: разбор стратегии", price=30),
    GuideItem(id="nike", title="Nike: как продают эмоцию", price=30),
    GuideItem(id="ikea", title="IKEA: экономика потока", price=30),
]

DEFAULT_QUIZ = QuizSet(
    brand="default",
    questions=[
        QuizQuestion("Что для тебя важнее в бизнесе?", ["Прибыль", "Бренд", "Команда"]),
        QuizQuestion("Как принимаешь решения?", ["По данным", "По интуиции", "Смешанно"]),
        QuizQuestion("Твой рынок?", ["Локальный", "Федеральный", "Международный"]),
        QuizQuestion("Главный ресурс сейчас?", ["Деньги", "Время", "Люди"]),
        QuizQuestion("Что мешает расти?", ["Процессы", "Маркетинг", "Фокус"]),
    ],
)


def quiz_result(answers: list[int]) -> str:
    profile = sum(answers) % 3
    verdict = {
        0: "Ты строишь на системе — тебе зайдут разборы про процессы.",
        1: "Ты про бренд и эмоцию — смотри разборы Nike и Starbucks.",
        2: "Ты про масштаб — тебе в закрытый канал за стратегиями роста.",
    }
    return "Результат теста\n\n" + verdict[profile]


def find_item(item_id: str) -> GuideItem | None:
    return next((item for item in SHOP_ITEMS if item.id == item_id), None)
