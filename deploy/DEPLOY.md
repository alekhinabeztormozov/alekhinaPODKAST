# Деплой на VPS (runbook)

VPS за пределами РФ (Telegram API из РФ режется по DPI). Ubuntu 22.04+, 1-2 ГБ RAM.

## 1. Подготовка сервера

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER   # перелогиниться
git clone <repo> /opt/alehina-bot && cd /opt/alehina-bot
```

## 2. .env

```bash
cp .env.example .env
nano .env
```

Заполнить:
- `BOT_TOKEN` — от BotFather.
- `ADMIN_TG_IDS` — числовой Telegram ID владельца/разработчика (через @userinfobot).
- `OPEN_CHANNEL_ID` — `@alekhinabeztormozov`.
- `CLOSED_CHANNEL_ID` — числовой id закрытого канала (см. п.4).
- `NOTION_TOKEN`, `PODSTER_RSS_URL` — уже есть.
- `PAYMENT_CURRENCY=RUB`, `PAYMENT_PROVIDER_TOKEN` — токен ЮKassa (docs/payments-setup.md).
- `POSTGRES_PASSWORD`, `SITE_ADDRESS` (домен для Caddy/HTTPS, если нужен web).
- `DATABASE_URL`/`REDIS_URL` в compose проставляются автоматически — в `.env` можно не трогать.

`TELEGRAM_PROXY` на VPS оставить пустым.

## 3. Запуск

```bash
docker compose up -d --build
docker compose logs -f bot
```

`migrate` накатит схему, поднимутся bot, web, scheduler, caddy.

## 4. Числовой id закрытого канала

Бот уже админ канала. После старта:

```bash
docker compose exec bot python -m scripts.chat_id
```

(или отправить любой пост в закрытый канал и посмотреть `docker compose logs scheduler`). Вписать id в `.env` (`CLOSED_CHANNEL_ID=-100...`), затем `docker compose up -d bot`.

## 5. Notion и Sheets

- Notion: расшарить страницу интеграции (Notion → страница → ... → Connections → bot-access), затем в боте `/setup_notion <page_id>` — создаст базу «Эпизоды», вернёт её id → в `.env` `NOTION_DB_EPISODES`, `docker compose up -d bot scheduler`.
- Sheets: создать service-account JSON в Google Cloud (на единую почту), положить путь в `GOOGLE_SA_JSON`, id таблицы в `GOOGLE_SHEETS_ID`, расшарить таблицу на email сервис-аккаунта, затем `/setup_sheets`.

## 6. Проверка цепочки

- Написать боту `/start` — меню.
- Владельцем: прислать текст → PDF; прислать аудио → выбрать эмбиент → готовый выпуск; `/ambients`, `/admin`.
- Залить эпизод в Podster → через ~10 мин анонс в открытом канале.
- Тестовая оплата (ЮKassa test token) → выдача invite/файла.
