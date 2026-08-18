# Чеклист go-live (VPS)

Порядок для запуска сегодня. Подробности — [deploy/DEPLOY.md](../deploy/DEPLOY.md), оплаты — [payments-setup.md](payments-setup.md).

## 0. Перед стартом собрать доступы
- [ ] `BOT_TOKEN` (BotFather).
- [ ] Числовой `ADMIN_TG_IDS` владельца (+ разработчика) — через @userinfobot.
- [ ] Открытый канал: `OPEN_CHANNEL_ID` (@username), бот — админ.
- [ ] Закрытый канал создан, бот — админ с правом приглашать/банить (id получим на шаге 3).
- [ ] ЮKassa: `YOOKASSA_SHOP_ID` + `YOOKASSA_SECRET_KEY` (сначала можно `test_`).
- [ ] Домен для HTTPS (`SITE_ADDRESS`) — нужен для вебхука ЮKassa.
- [ ] (опц.) Notion `NOTION_TOKEN`, Podster `PODSTER_RSS_URL`, Google `GOOGLE_SA_JSON`+`GOOGLE_SHEETS_ID`.

## 1. Сервер и .env
- [ ] VPS вне РФ (Telegram режется DPI), Ubuntu 22.04+, docker + compose-plugin.
- [ ] `git clone` в `/opt/alehina-bot`, `cp .env.example .env`.
- [ ] Заполнить `.env`: токен, admin, каналы, ЮKassa, `POSTGRES_PASSWORD`, `SITE_ADDRESS`.
- [ ] **`USE_REDIS=true`** (прод — FSM в Redis).
- [ ] `TELEGRAM_PROXY` пустой.

## 2. Запуск
- [ ] `docker compose up -d --build` — поднимутся db, redis, migrate (alembic upgrade head), bot, web, scheduler, caddy.
- [ ] `docker compose logs -f bot` — «Бот запускается», без трейсбеков.
- [ ] `docker compose ps` — все healthy; `curl https://<домен>/health` → `{"status":"ok"}`.

## 3. Закрытый канал
- [ ] `docker compose exec bot python -m scripts.chat_id` (или пост в канал + логи) → взять `-100…`.
- [ ] Вписать `CLOSED_CHANNEL_ID` в `.env` → `docker compose up -d bot web scheduler`.

## 4. Оплаты
- [ ] В ЛК ЮKassa зарегистрировать HTTP-уведомление `https://<домен>/payments/yookassa`, событие `payment.succeeded`.
- [ ] Тестовым ключом провести оплату подписки: ссылка → оплата → вебхук → бот прислал invite. Проверить `docker compose logs -f web`.
- [ ] Переключить на боевой `YOOKASSA_SECRET_KEY` → `docker compose up -d web`.

## 5. Интеграции (опц., но по спеке нужны)
- [ ] Notion: расшарить страницу интеграции → `/setup_notion <page_id>` → id в `.env` (`NOTION_DB_EPISODES`). База «Эпизоды» создастся со всеми полями (Ключевое слово, Теги, PDF-бонус, Аудио-бонус, Пост для Telegram, Пост для VK). Синк Notion→БД идёт каждые 5 мин + `/sync_notion` вручную.
- [ ] Sheets: положить SA-JSON, расшарить таблицу на email сервис-аккаунта → `/setup_sheets` (создаст 4 листа). После — контакты/продажи пишутся туда автоматически.
- [ ] ВКонтакте (опц., верх воронки): создать сообщество → Управление → Работа с API → ключ доступа сообщества (`VK_GROUP_TOKEN`), id группы (`VK_GROUP_ID`). В Callback API указать адрес `https://<домен>/vk/callback`, версию `VK_API_VERSION`, вписать строку подтверждения в `VK_CONFIRMATION_TOKEN` и (опц.) секрет в `VK_SECRET`; включить событие «Входящее сообщение». Включить сообщения сообщества. Пусто = ВК выключен, деплой не ломается. Бот в ВК выдаёт бонус по ключевому слову и уводит в Телеграм; «Пост для VK» из Notion публикуется на стену.

## 6. Наполнение контентом
Сезоны/пакеты/интенсив — командами (разово, их мало); эпизоды и бонусы — в Notion (Юлия), бот синхронизирует.
- [ ] `/add_season sweet | Сладкая империя | 299 | 179 | <архив> | 1` (текущий сезон; код `sweet` = поле «Сезон» в Notion).
- [ ] `/set_workbook sweet | <ссылка>` — рабочая тетрадь (иначе раздел скрыт).
- [ ] `/add_season all | Все сезоны | 999 | 599 | <общая_папка> | 0` — пакет «все сезоны».
- [ ] `/add_product intensive_sweet | sweet | … | 3900 | 2730 | <ссылка> | 0` — интенсив (активировать в финале `is_active=1`).
- [ ] Эпизоды+бонусы: Юлия заполняет карточки в Notion (см. docs/owner-guide.md), ставит статус «Контент готов»/«Опубликован» → `/sync_notion` (или ждать авто-синк).
- [ ] `/content` — проверить счётчики. (Быстрый демо-каталог: `docker compose exec bot python -m scripts.seed_demo`.)

## 7. Дымовой прогон end-to-end
- [ ] `/start` клиентом → меню (О подписке / Найти в архиве / Магазин / Интенсив).
- [ ] Ключевое слово → PDF + голосовой; демо-голос один раз → кнопка «Забрать 24 часа» → доступ + invite.
- [ ] Поиск словом → топ-3 с кнопками.
- [ ] Магазин → сезон/тетрадь/все сезоны, цены с −40% у подписчика.
- [ ] Подписка 790 и 1890 → оплата → invite; по истечении — авто-кик + напоминание (scheduler).
- [ ] Владельцем: текст → PDF; аудио → эмбиент → готовый mp3; `/admin` статистика.
- [ ] Эпизод в Podster → через ~10 мин анонс в открытом канале.

## 8. После сдачи
- [ ] Клиент меняет пароль единой почты (доступ бота — не по паролю).
- [ ] Секреты только в `.env` на сервере; в git/графе — REDACTED.
