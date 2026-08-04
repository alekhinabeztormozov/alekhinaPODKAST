# Алёхина без тормозов — бот и автоматизация подкаста

Полное техническое описание проекта — в [PROJECT.md](PROJECT.md).

Автоматизация подкаста: обработка аудио (ffmpeg), генерация PDF-гайдов (WeasyPrint),
Telegram-бот (aiogram 3.x) с воронкой продаж, оплаты Telegram-нативно, интеграции
Google Sheets / Notion / RSS.

## Требования

- Python 3.12+
- ffmpeg и ffprobe в `PATH` (аудио-пайплайн)
- Для PDF на Windows — GTK-библиотеки (см. ниже). На Linux ставятся пакетами
  `libpango`, `libcairo`, `libgdk-pixbuf`.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Заполнить `.env` по мере поступления доступов (переменные описаны в PROJECT.md р.10.1).

### GTK для WeasyPrint на Windows

WeasyPrint использует нативные библиотеки Pango/Cairo. Через MSYS2:

```bash
winget install MSYS2.MSYS2
C:\msys64\usr\bin\pacman -S --noconfirm mingw-w64-x86_64-pango
```

Код сам добавляет `C:\msys64\mingw64\bin` в поиск библиотек при рендере. Другой путь
задаётся переменной окружения `GTK_BIN_DIR`.

## Запуск

```bash
python -m bot.main
python -m scheduler.runner
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## Аудио-пайплайн

```bash
python -m media.pipeline --voice raw.mp3 --intro media/assets/intro.mp3 \
    --music media/assets/music.mp3 --outro media/assets/outro.mp3 -o media/out/ep01.mp3
```

Подробности — [media/README.md](media/README.md).

## Структура

```
bot/         бот aiogram: handlers, keyboards, states, middlewares, services
web/         FastAPI (health, вебхуки)
scheduler/   APScheduler: RSS-опрос, ревокация подписок
media/       ffmpeg-пайплайн
pdf/         WeasyPrint-шаблоны и рендер
db/          модели SQLAlchemy, сессии
config.py    pydantic-settings
```
