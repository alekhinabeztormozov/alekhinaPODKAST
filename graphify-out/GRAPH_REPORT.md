# Graph Report - music bot  (2026-08-18)

## Corpus Check
- 87 files · ~77,333 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 706 nodes · 1847 edges · 44 communities (43 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ab823831`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Мастер-документ проекта «Алёхина без тормозов»
- Telegram-бот (aiogram 3.x)
- Технический стек
- Оплаты Telegram-нативно (ключевое решение)
- Апселлы фаза 2+ (отдельная плата)
- Google Sheets (витрина для клиента)
- Секреты / env-переменные (.env)
- Пошаговая инструкция по доступам для Юлии
- Автоматизация подкаста бизнес-блогера
- test_vk.py
- Settings
- get_settings
- session_scope
- producer.py
- PipelineInputs
- render_guide
- Алёхина без тормозов — бот и автоматизация подкаста
- admin.py
- fulfillment.py
- Чеклист go-live (VPS)
- Логика бота (спека клиента, 14.08) — источник правды
- Гайд владельца — как пользоваться ботом
- catalog.py
- generate_ambient.py
- Google Sheets — service-account JSON
- alehina-bot
- ThrottlingMiddleware
- env.py

## God Nodes (most connected - your core abstractions)
1. `session_scope()` - 73 edges
2. `get_settings()` - 68 edges
3. `Settings` - 42 edges
4. `show()` - 26 edges
5. `handle_incoming()` - 19 edges
6. `is_subscribed()` - 18 edges
7. `PipelineInputs` - 18 edges
8. `Base` - 17 edges
9. `process_episode()` - 16 edges
10. `User` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_split_guide_strips_markdown_title()` --calls--> `split_guide()`  [EXTRACTED]
  tests/test_pdf.py → bot/handlers/producer.py
- `test_publish_vk_posts_gate_when_unconfigured()` --calls--> `publish_vk_posts()`  [EXTRACTED]
  tests/test_vk.py → bot/services/notion_sync.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_phase2.py → config.py
- `_Sink` --uses--> `Settings`  [INFERRED]
  tests/test_vk.py → config.py
- `BotFather (создание бота, получение токена)` --references--> `Telegram-бот (aiogram 3.x)`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **6 сценариев Telegram-бота** — project_scenario_start, project_scenario_pdf_bonus, project_scenario_quiz, project_scenario_closed_channel, project_scenario_shop, project_scenario_admin [EXTRACTED 1.00]
- **Пайплайн: запись→Podster→анонс→бот→продажа** — project_audio_processing, project_podster, project_rss_feed, project_open_channel_announce, project_telegram_bot, project_monetization [EXTRACTED 1.00]
- **Механизм закрытого канала: оплата→invite→ревокация** — project_telegram_stars, project_invite_revocation, project_apscheduler, project_scenario_closed_channel [EXTRACTED 0.95]

## Communities (44 total, 1 thin omitted)

### Community 0 - "Мастер-документ проекта «Алёхина без тормозов»"
Cohesion: 0.15
Nodes (16): доступы-для-юлии.md (инструкция клиенту), Доступы + материалы от клиента, Дедлайн 3-4 недели от старта, Условия сделки, Прямая оплата, не через Kwork, Разделение труда исполнитель/клиент, Первый шаг: ffmpeg аудио-пайплайн, Проверка всей цепочки (аудио→Podster→бот→продажа) (+8 more)

### Community 1 - "Telegram-бот (aiogram 3.x)"
Cohesion: 0.18
Nodes (14): Два Telegram-канала (открытый публичный + закрытый частный), BOT_TOKEN, CLOSED_CHANNEL_ID, Воронка продаж, Логика воронки: дешёвый гайд толкает в подписку, Монетизация, PDF-гайды 20-30 ₽, Redis (FSM-хранилище) (+6 more)

### Community 2 - "Технический стек"
Cohesion: 0.16
Nodes (14): aiogram 3.x, Обработка аудио (ffmpeg, без нейронки), Caddy (авто-TLS HTTPS для вебхуков), PODSTER_RSS_URL, FastAPI + uvicorn, feedparser (RSS), ffmpeg, httpx (async HTTP-клиент) (+6 more)

### Community 3 - "Оплаты Telegram-нативно (ключевое решение)"
Cohesion: 0.20
Nodes (10): APScheduler, Объём контента (планирование), PAYMENT_PROVIDER_TOKEN, Одноразовый invite + ревокация доступа, Оплаты Telegram-нативно (ключевое решение), Сценарий Магазин (PDF-гайды), Планировщик отложенной публикации, Telegram Stars / ЮKassa через sendInvoice (+2 more)

### Community 4 - "Апселлы фаза 2+ (отдельная плата)"
Cohesion: 0.20
Nodes (10): Продажа книг, Игра «бизнес-покер», Лендинг под подкасты, Марафоны, бизнес-сессии, Детерминированные пайплайны без нейронки, Генерация PDF (WeasyPrint, без нейронки), Рилсы / AI-видео (единственная нейронка), Апселлы фаза 2+ (отдельная плата) (+2 more)

### Community 5 - "Google Sheets (витрина для клиента)"
Cohesion: 0.25
Nodes (9): Хранилища данных, GOOGLE_SA_JSON, NOTION_TOKEN, Google Sheets (витрина для клиента), Идемпотентность оплат/выдачи, Notion (пульт контента, база «Эпизоды»), Внутренняя БД PostgreSQL (источник правды), Надёжность (заложить с нуля) (+1 more)

### Community 6 - "Секреты / env-переменные (.env)"
Cohesion: 0.25
Nodes (8): ADMIN_TG_IDS, DATABASE_URL, GOOGLE_SHEETS_ID, NOTION_DB_EPISODES, OPEN_CHANNEL_ID, REDIS_URL, Секреты / env-переменные (.env), Сценарий /admin (статистика, whitelist)

### Community 7 - "Пошаговая инструкция по доступам для Юлии"
Cohesion: 0.33
Nodes (6): BotFather (создание бота, получение токена), Пошаговая инструкция по доступам для Юлии, Notion Internal Integration Secret, Безопасная передача секретов (в TG, удалить после подтверждения), gspread + google-auth (service account), Единая почта Gmail под весь проект

### Community 8 - "Автоматизация подкаста бизнес-блогера"
Cohesion: 0.33
Nodes (6): Стиль сообщений клиенту (прямые кавычки, короткое тире, сплошные абзацы), Разработчик Лев (соло, lev.dev), Автоматизация подкаста бизнес-блогера, Принцип: записал один раз → система разнесла и продала, Windows-заметка PYTHONIOENCODING=utf-8, Юлия Алёхина (клиент, бизнес-стратег)

### Community 9 - "test_vk.py"
Cohesion: 0.09
Nodes (38): _bonus_text(), _club_text(), _command(), handle_incoming(), main_keyboard(), _none_text(), _results_text(), _search_prompt() (+30 more)

### Community 10 - "Settings"
Cohesion: 0.07
Nodes (60): BaseSettings, catalog_pages(), _client(), create_episodes_db(), _create_episodes_db_sync(), episode_id(), episode_status(), episode_title() (+52 more)

### Community 11 - "get_settings"
Cohesion: 0.06
Nodes (91): BaseStorage, deliver(), Any, Message, buy_club(), club_bonuses(), club_trial(), _offer() (+83 more)

### Community 12 - "session_scope"
Cohesion: 0.05
Nodes (88): async_sessionmaker, AsyncEngine, AsyncSession, add_bonus(), add_episode(), add_product(), add_season(), counts() (+80 more)

### Community 13 - "producer.py"
Cohesion: 0.11
Nodes (37): choose_ambient(), _is_owner(), list_ambients(), owner_only(), owner_panel(), preview_ambient(), _process(), Bot (+29 more)

### Community 14 - "PipelineInputs"
Cohesion: 0.22
Nodes (25): make_episode(), Path, AudioProfile, build_filter_complex(), _cli(), _ordered_inputs(), PipelineError, PipelineInputs (+17 more)

### Community 15 - "render_guide"
Cohesion: 0.17
Nodes (21): build_guide(), Path, _data_uri(), _ensure_gtk(), GuideStyle, _logo_block(), PdfError, Path (+13 more)

### Community 17 - "Алёхина без тормозов — бот и автоматизация подкаста"
Cohesion: 0.11
Nodes (16): Ассеты от клиента (кладём в `media/assets/`), Аудио-пайплайн (ffmpeg), Запуск, Профиль звука, Docker Compose (рекомендуется), GTK для WeasyPrint на Windows, systemd (без Docker), Алёхина без тормозов — бот и автоматизация подкаста (+8 more)

### Community 18 - "admin.py"
Cohesion: 0.34
Nodes (16): add_bonus(), add_episode(), add_product(), add_season(), admin_stats(), content_counts(), _is_admin(), Message (+8 more)

### Community 19 - "fulfillment.py"
Cohesion: 0.19
Nodes (23): _already_done(), fulfill(), _fulfill_all(), _fulfill_season(), _fulfill_sub(), _fulfill_workbook(), _invite_link(), Any (+15 more)

### Community 21 - "Чеклист go-live (VPS)"
Cohesion: 0.07
Nodes (25): 1. Подготовка сервера, 2. .env, 3. Запуск, 4. Числовой id закрытого канала, 5.05. Webhook ЮKassa (обязательно для оплат), 5.1. Шрифты PDF (только без Docker), 5. Notion и Sheets, 6. Проверка цепочки (+17 more)

### Community 23 - "Логика бота (спека клиента, 14.08) — источник правды"
Cohesion: 0.20
Nodes (9): БД (таблицы), Логика бота (спека клиента, 14.08) — источник правды, Модель, Статус реализации (на 2026-08-16) — готово к деплою, Сценарии, Технические, Фазы, Цены (жёстко; скидка подписчику по `is_subscribed`) (+1 more)

### Community 24 - "Гайд владельца — как пользоваться ботом"
Cohesion: 0.17
Nodes (11): PDF-гайд из текста, ВКонтакте (верх воронки), Гайд владельца — как пользоваться ботом, Готовый подкаст из аудио, Наполнение контентом через Notion (основной способ), Настройка таблиц и Notion (разово, команды в боте), Пакеты магазина и цены, Подписка и триал (автоматически) (+3 more)

### Community 25 - "catalog.py"
Cohesion: 0.20
Nodes (20): bonus_by_button(), callback_query, CallbackQuery, active_main_product(), all_seasons(), _bonus(), bonus_by_id(), bonus_by_keyword() (+12 more)

### Community 26 - "generate_ambient.py"
Cohesion: 0.67
Nodes (5): _build_command(), _cli(), _filter_complex(), generate(), SynthSpec

### Community 27 - "Google Sheets — service-account JSON"
Cohesion: 0.50
Nodes (3): Google Sheets — service-account JSON, Что дальше делаю я, Шаги

### Community 45 - "ThrottlingMiddleware"
Cohesion: 0.27
Nodes (6): BaseMiddleware, Any, ThrottlingMiddleware, TelegramObject, test_missing_user_passes_through(), test_second_call_suppressed()

### Community 46 - "env.py"
Cohesion: 0.53
Nodes (5): Connection, do_run_migrations(), get_url(), run_migrations_offline(), run_migrations_online()

## Knowledge Gaps
- **72 isolated node(s):** `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows`, `Запуск`, `Аудио-пайплайн` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `test_vk.py`, `Settings`, `session_scope`, `producer.py`, `PipelineInputs`, `env.py`, `admin.py`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `session_scope()` connect `session_scope` to `test_vk.py`, `Settings`, `get_settings`, `admin.py`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `test_vk.py`, `get_settings`, `session_scope`, `producer.py`, `admin.py`, `fulfillment.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `FakeBot` and `FakeBot`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_vk.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._
- **Should `Settings` be split into smaller, more focused modules?**
  _Cohesion score 0.07006151742993848 - nodes in this community are weakly interconnected._