# Graph Report - C:/1 КОДИНГ/1 ПРОЕКТЫ/music bot  (2026-08-03)

## Corpus Check
- Corpus is ~2,887 words - fits in a single context window. You may not need a graph.

## Summary
- 93 nodes · 129 edges · 9 communities
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.86)
- Token cost: 71,789 input · 0 output

## Community Hubs (Navigation)
- Доступы и хранилища данных
- Распространение подкаста и публикация
- Бот-ядро и надёжность
- Обработка контента без AI и цена
- Оплаты и вебхуки Telegram
- Концепция проекта и клиент
- Апселлы фазы 2
- Community 7
- Community 8

## God Nodes (most connected - your core abstractions)
1. `Мастер-документ проекта «Алёхина без тормозов»` - 15 edges
2. `Технический стек` - 13 edges
3. `Секреты / env-переменные (.env)` - 13 edges
4. `Telegram-бот (aiogram 3.x)` - 10 edges
5. `Апселлы фаза 2+ (отдельная плата)` - 7 edges
6. `Пошаговая инструкция по доступам для Юлии` - 6 edges
7. `Сценарий Закрытый канал (оплата → invite)` - 6 edges
8. `Автоматизация подкаста бизнес-блогера` - 5 edges
9. `Условия сделки` - 5 edges
10. `Воронка продаж` - 5 edges

## Surprising Connections (you probably didn't know these)
- `BotFather (создание бота, получение токена)` --references--> `Telegram-бот (aiogram 3.x)`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md
- `Два Telegram-канала (открытый публичный + закрытый частный)` --references--> `Сценарий Закрытый канал (оплата → invite)`  [INFERRED]
  доступы-для-юлии.md → PROJECT.md
- `Пошаговая инструкция по доступам для Юлии` --references--> `Podster (хостинг аудио)`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md
- `Notion Internal Integration Secret` --references--> `Notion (пульт контента, база «Эпизоды»)`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md
- `Пошаговая инструкция по доступам для Юлии` --references--> `Единая почта Gmail под весь проект`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md

## Hyperedges (group relationships)
- **6 сценариев Telegram-бота** — project_scenario_start, project_scenario_pdf_bonus, project_scenario_quiz, project_scenario_closed_channel, project_scenario_shop, project_scenario_admin [EXTRACTED 1.00]
- **Пайплайн: запись→Podster→анонс→бот→продажа** — project_audio_processing, project_podster, project_rss_feed, project_open_channel_announce, project_telegram_bot, project_monetization [EXTRACTED 1.00]
- **Механизм закрытого канала: оплата→invite→ревокация** — project_telegram_stars, project_invite_revocation, project_apscheduler, project_scenario_closed_channel [EXTRACTED 0.95]

## Communities (9 total, 0 thin omitted)

### Community 0 - "Доступы и хранилища данных"
Cohesion: 0.15
Nodes (16): доступы-для-юлии.md (инструкция клиенту), Доступы + материалы от клиента, Дедлайн 3-4 недели от старта, Условия сделки, Прямая оплата, не через Kwork, Разделение труда исполнитель/клиент, Первый шаг: ffmpeg аудио-пайплайн, Проверка всей цепочки (аудио→Podster→бот→продажа) (+8 more)

### Community 1 - "Распространение подкаста и публикация"
Cohesion: 0.18
Nodes (14): Два Telegram-канала (открытый публичный + закрытый частный), BOT_TOKEN, CLOSED_CHANNEL_ID, Воронка продаж, Логика воронки: дешёвый гайд толкает в подписку, Монетизация, PDF-гайды 20-30 ₽, Redis (FSM-хранилище) (+6 more)

### Community 2 - "Бот-ядро и надёжность"
Cohesion: 0.16
Nodes (14): aiogram 3.x, Обработка аудио (ffmpeg, без нейронки), Caddy (авто-TLS HTTPS для вебхуков), PODSTER_RSS_URL, FastAPI + uvicorn, feedparser (RSS), ffmpeg, httpx (async HTTP-клиент) (+6 more)

### Community 3 - "Обработка контента без AI и цена"
Cohesion: 0.20
Nodes (10): APScheduler, Объём контента (планирование), PAYMENT_PROVIDER_TOKEN, Одноразовый invite + ревокация доступа, Оплаты Telegram-нативно (ключевое решение), Сценарий Магазин (PDF-гайды), Планировщик отложенной публикации, Telegram Stars / ЮKassa через sendInvoice (+2 more)

### Community 4 - "Оплаты и вебхуки Telegram"
Cohesion: 0.20
Nodes (10): Продажа книг, Игра «бизнес-покер», Лендинг под подкасты, Марафоны, бизнес-сессии, Детерминированные пайплайны без нейронки, Генерация PDF (WeasyPrint, без нейронки), Рилсы / AI-видео (единственная нейронка), Апселлы фаза 2+ (отдельная плата) (+2 more)

### Community 5 - "Концепция проекта и клиент"
Cohesion: 0.25
Nodes (9): Хранилища данных, GOOGLE_SA_JSON, NOTION_TOKEN, Google Sheets (витрина для клиента), Идемпотентность оплат/выдачи, Notion (пульт контента, база «Эпизоды»), Внутренняя БД PostgreSQL (источник правды), Надёжность (заложить с нуля) (+1 more)

### Community 6 - "Апселлы фазы 2"
Cohesion: 0.25
Nodes (8): ADMIN_TG_IDS, DATABASE_URL, GOOGLE_SHEETS_ID, NOTION_DB_EPISODES, OPEN_CHANNEL_ID, REDIS_URL, Секреты / env-переменные (.env), Сценарий /admin (статистика, whitelist)

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (6): BotFather (создание бота, получение токена), Пошаговая инструкция по доступам для Юлии, Notion Internal Integration Secret, Безопасная передача секретов (в TG, удалить после подтверждения), gspread + google-auth (service account), Единая почта Gmail под весь проект

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (6): Стиль сообщений клиенту (прямые кавычки, короткое тире, сплошные абзацы), Разработчик Лев (соло, lev.dev), Автоматизация подкаста бизнес-блогера, Принцип: записал один раз → система разнесла и продала, Windows-заметка PYTHONIOENCODING=utf-8, Юлия Алёхина (клиент, бизнес-стратег)

## Knowledge Gaps
- **20 isolated node(s):** `Юлия Алёхина (клиент, бизнес-стратег)`, `доступы-для-юлии.md (инструкция клиенту)`, `Локальный граф graphify-out/`, `Цена базы 45 000 ₽`, `Дедлайн 3-4 недели от старта` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Мастер-документ проекта «Алёхина без тормозов»` connect `Доступы и хранилища данных` to `Распространение подкаста и публикация`, `Бот-ядро и надёжность`, `Обработка контента без AI и цена`, `Оплаты и вебхуки Telegram`, `Концепция проекта и клиент`, `Community 8`?**
  _High betweenness centrality (0.566) - this node is a cross-community bridge._
- **Why does `Технический стек` connect `Бот-ядро и надёжность` to `Доступы и хранилища данных`, `Распространение подкаста и публикация`, `Обработка контента без AI и цена`, `Оплаты и вебхуки Telegram`, `Концепция проекта и клиент`, `Community 7`?**
  _High betweenness centrality (0.264) - this node is a cross-community bridge._
- **Why does `Секреты / env-переменные (.env)` connect `Апселлы фазы 2` to `Доступы и хранилища данных`, `Распространение подкаста и публикация`, `Бот-ядро и надёжность`, `Обработка контента без AI и цена`, `Концепция проекта и клиент`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Telegram-бот (aiogram 3.x)` (e.g. with `BOT_TOKEN` and `Redis (FSM-хранилище)`) actually correct?**
  _`Telegram-бот (aiogram 3.x)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Юлия Алёхина (клиент, бизнес-стратег)`, `доступы-для-юлии.md (инструкция клиенту)`, `Локальный граф graphify-out/` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._