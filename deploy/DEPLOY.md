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
- `YOOKASSA_SHOP_ID` + `YOOKASSA_SECRET_KEY` — данные магазина ЮKassa (docs/payments-setup.md). Именно они, а не `PAYMENT_PROVIDER_TOKEN` — оплаты идут внешним чекаутом ЮKassa + вебхук.
- `USE_REDIS=true` — на проде FSM в Redis (переживает рестарт).
- `POSTGRES_PASSWORD`, `SITE_ADDRESS` (домен для Caddy/HTTPS — обязателен для вебхука ЮKassa).
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
- Sheets: создать service-account JSON в Google Cloud (на единую почту), положить файл в `/opt/alehina-bot/secrets/` (каталог монтируется в контейнеры только на чтение и в образ не попадает), путь к нему в `GOOGLE_SA_JSON`, id таблицы в `GOOGLE_SHEETS_ID`, расшарить таблицу на email сервис-аккаунта, затем `/setup_sheets`.

## 5.05. Webhook ЮKassa (обязательно для оплат)

После поднятия домена зарегистрировать URL уведомлений в ЛК ЮKassa
(Настройки → Уведомления / HTTP-уведомления): `https://<домен>/payments/yookassa`.
Событие — `payment.succeeded`. Без этого бот не узнает об оплате и не выдаст доступ.
Наполнение контентом — командами `/add_season` и т.д. (docs/owner-guide.md).

## 5.1. Шрифты PDF (только без Docker)

В Docker шрифты ставятся автоматически (Dockerfile). Для systemd/bare-запуска:

```bash
sudo mkdir -p /usr/share/fonts/truetype/brand
sudo cp pdf/fonts/*.ttf /usr/share/fonts/truetype/brand/ && sudo fc-cache -f
```

Иначе гайды рендерятся системным шрифтом вместо фирменного Oswald/Roboto.

## 6. Проверка цепочки

- Написать боту `/start` — меню.
- Владельцем: прислать текст → PDF; прислать аудио → выбрать эмбиент → готовый выпуск; `/ambients`, `/admin`.
- Залить эпизод в Podster → через ~10 мин анонс в открытом канале.
- Тестовая оплата (ЮKassa test token) → выдача invite/файла.
