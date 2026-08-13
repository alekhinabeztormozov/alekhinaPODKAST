from __future__ import annotations

from dataclasses import dataclass, field

WELCOME = (
    "👋 <b>Алёхина без тормозов</b>\n\n"
    "Разборы стратегий известных брендов и рабочие инструменты для твоего дела.\n\n"
    "Что тут есть:\n"
    "📄 бесплатный гайд в подарок\n"
    "🧠 тест — твой бизнес-профиль\n"
    "🔒 закрытый клуб с детальными разборами\n"
    "🛒 магазин готовых гайдов\n\n"
    "С чего начнём? 👇"
)

MENU_HINT = "🏠 <b>Главное меню</b>\n\nВыбери раздел 👇"

QUIZ_INTRO = (
    "🧠 <b>Тест: твой бизнес-профиль</b>\n\n"
    "5 коротких вопросов. В конце — вывод и какие разборы тебе зайдут.\n\n"
    "Поехали?"
)

OWNER_PANEL = (
    "🎛 <b>Пульт владельца</b>\n\n"
    "Отсюда готовишь контент. Клиенты видят другое меню.\n\n"
    "🎧 <b>Эпизод</b> — пришли аудио, бот наложит фон и вернёт готовый выпуск.\n"
    "📄 <b>Гайд</b> — пришли текст (первая строка = заголовок), бот вернёт PDF.\n"
    "🎼 <b>Эмбиенты</b> — послушать фоны.\n"
    "📊 <b>Статистика</b> — контакты и продажи за неделю.\n\n"
    "Выбери кнопкой ниже 👇"
)

OWNER_AUDIO_HINT = (
    "🎧 <b>Обработка эпизода</b>\n\n"
    "Пришли аудио — файлом или голосовым. Дальше выберешь фон, и бот вернёт готовый mp3."
)
OWNER_GUIDE_HINT = (
    "📄 <b>Сборка гайда</b>\n\n"
    "Пришли текст одним сообщением. Первая строка станет заголовком, остальное — телом PDF."
)

PDF_ASK_EMAIL = (
    "📄 <b>Бесплатный гайд</b>\n\n"
    "Оставь email — пришлю гайд и новые разборы. Или пропусти, и дам ссылку сразу 👇"
)

PDF_DELIVERED = (
    "📄 <b>Готово!</b>\n\n"
    "Твой гайд: {link}\n\n"
    "Понравится — в закрытом клубе таких разборов десятки 🔒"
)

CLOSED_INTRO = (
    "🔒 <b>Закрытый клуб</b>\n\n"
    "Детальные разборы компаний, аудиобонусы и инструменты.\n"
    "Подписка <b>{price} ₽/мес</b>.\n\n"
    "🎁 Первый день — бесплатно, посмотреть изнутри."
)

SHOP_INTRO = (
    "🛒 <b>Магазин разборов</b>\n\n"
    "Выбери гайд — пришлю файл сразу после оплаты 👇"
)

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
        0: "🧩 Ты строишь на системе. Зайдут разборы про процессы и операционку — начни с закрытого клуба.",
        1: "🔥 Ты про бренд и эмоцию. Смотри разборы Nike и Starbucks — как продавать не товар, а чувство.",
        2: "🚀 Ты про масштаб. Тебе в закрытый клуб за стратегиями роста и выхода на новые рынки.",
    }
    return "🧠 <b>Твой результат</b>\n\n" + verdict[profile]


def find_item(item_id: str) -> GuideItem | None:
    return next((item for item in SHOP_ITEMS if item.id == item_id), None)
