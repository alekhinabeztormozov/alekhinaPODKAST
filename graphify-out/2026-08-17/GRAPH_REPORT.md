# Graph Report - music bot  (2026-08-16)

## Corpus Check
- 84 files · ~48,557 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 664 nodes · 1720 edges · 49 communities (48 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e224691`
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
- session_scope
- Settings
- seasons.py
- models.py
- producer.py
- PipelineInputs
- renderer.py
- notion.py
- Алёхина без тормозов — бот и автоматизация подкаста
- get_settings
- sheets.py
- test_phase2.py
- Чеклист go-live (VPS)
- test_spec_features.py
- Логика бота (спека клиента, 14.08) — источник правды
- Гайд владельца — как пользоваться ботом
- catalog.py
- generate_ambient.py
- Google Sheets — service-account JSON
- alehina-bot
- seed_demo.py
- notion_sync.py
- subscriptions.py
- admin_content.py

## God Nodes (most connected - your core abstractions)
1. `session_scope()` - 71 edges
2. `get_settings()` - 60 edges
3. `Settings` - 38 edges
4. `show()` - 26 edges
5. `is_subscribed()` - 18 edges
6. `PipelineInputs` - 18 edges
7. `Base` - 17 edges
8. `process_episode()` - 16 edges
9. `User` - 15 edges
10. `Season` - 15 edges

## Surprising Connections (you probably didn't know these)
- `set_workbook()` --calls--> `session_scope()`  [EXTRACTED]
  bot/services/admin_content.py → db/session.py
- `test_voice_demo_once()` --calls--> `take_voice_demo()`  [EXTRACTED]
  tests/test_core_flows.py → bot/services/users.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_notion_sync.py → config.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_phase2.py → config.py
- `FakeBot` --uses--> `Season`  [INFERRED]
  tests/test_phase2.py → db/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **6 сценариев Telegram-бота** — project_scenario_start, project_scenario_pdf_bonus, project_scenario_quiz, project_scenario_closed_channel, project_scenario_shop, project_scenario_admin [EXTRACTED 1.00]
- **Пайплайн: запись→Podster→анонс→бот→продажа** — project_audio_processing, project_podster, project_rss_feed, project_open_channel_announce, project_telegram_bot, project_monetization [EXTRACTED 1.00]
- **Механизм закрытого канала: оплата→invite→ревокация** — project_telegram_stars, project_invite_revocation, project_apscheduler, project_scenario_closed_channel [EXTRACTED 0.95]

## Communities (49 total, 1 thin omitted)

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

### Community 9 - "session_scope"
Cohesion: 0.21
Nodes (22): all_user_ids(), _aware(), can_trial(), drop_subscription(), expired_subscribers(), get_or_create(), grant_subscription(), grant_trial() (+14 more)

### Community 10 - "Settings"
Cohesion: 0.15
Nodes (31): BaseSettings, _already_done(), fulfill(), _fulfill_all(), _fulfill_season(), _fulfill_sub(), _fulfill_workbook(), _invite_link() (+23 more)

### Community 11 - "seasons.py"
Cohesion: 0.09
Nodes (58): buy_club(), club_bonuses(), club_trial(), _offer(), Bot, callback_query, CallbackQuery, _return_url() (+50 more)

### Community 12 - "models.py"
Cohesion: 0.22
Nodes (14): Записать контакт в БД + Google Sheets. Один пользователь = одна строка (дедуп…, record(), record(), Base, Contact, ProcessedPayment, Sale, SeenKey (+6 more)

### Community 13 - "producer.py"
Cohesion: 0.06
Nodes (61): bonus_by_button(), deliver(), Any, callback_query, CallbackQuery, Message, choose_ambient(), _is_owner() (+53 more)

### Community 14 - "PipelineInputs"
Cohesion: 0.22
Nodes (25): make_episode(), Path, AudioProfile, build_filter_complex(), _cli(), _ordered_inputs(), PipelineError, PipelineInputs (+17 more)

### Community 15 - "renderer.py"
Cohesion: 0.20
Nodes (19): build_guide(), Path, _transparent_logo(), _ensure_gtk(), GuideStyle, _header_block(), _logo_img(), PdfError (+11 more)

### Community 16 - "notion.py"
Cohesion: 0.11
Nodes (31): catalog_pages(), _client(), create_episodes_db(), _create_episodes_db_sync(), episode_id(), episode_status(), episode_title(), extract_catalog() (+23 more)

### Community 17 - "Алёхина без тормозов — бот и автоматизация подкаста"
Cohesion: 0.11
Nodes (16): Ассеты от клиента (кладём в `media/assets/`), Аудио-пайплайн (ffmpeg), Запуск, Профиль звука, Docker Compose (рекомендуется), GTK для WeasyPrint на Windows, systemd (без Docker), Алёхина без тормозов — бот и автоматизация подкаста (+8 more)

### Community 18 - "get_settings"
Cohesion: 0.08
Nodes (44): BaseMiddleware, BaseStorage, add_bonus(), add_episode(), add_product(), add_season(), admin_stats(), content_counts() (+36 more)

### Community 19 - "sheets.py"
Cohesion: 0.31
Nodes (13): add_contact(), add_sale(), _append(), _append_sync(), bootstrap(), _bootstrap_sync(), _client(), _now() (+5 more)

### Community 20 - "test_phase2.py"
Cohesion: 0.24
Nodes (9): add_purchased_season(), MainProduct, User, test_season_purchase(), FakeBot, test_active_intensive(), test_all_seasons_access(), test_finale_broadcast() (+1 more)

### Community 21 - "Чеклист go-live (VPS)"
Cohesion: 0.07
Nodes (25): 1. Подготовка сервера, 2. .env, 3. Запуск, 4. Числовой id закрытого канала, 5.05. Webhook ЮKassa (обязательно для оплат), 5.1. Шрифты PDF (только без Docker), 5. Notion и Sheets, 6. Проверка цепочки (+17 more)

### Community 22 - "test_spec_features.py"
Cohesion: 0.28
Nodes (9): date, Season, _seasons_ending(), FakeBot, _seed_seasons(), test_fulfill_all_grants_everything(), test_fulfill_season_and_idempotent(), test_fulfill_sub_3m() (+1 more)

### Community 23 - "Логика бота (спека клиента, 14.08) — источник правды"
Cohesion: 0.20
Nodes (9): БД (таблицы), Логика бота (спека клиента, 14.08) — источник правды, Модель, Статус реализации (на 2026-08-16) — готово к деплою, Сценарии, Технические, Фазы, Цены (жёстко; скидка подписчику по `is_subscribed`) (+1 more)

### Community 24 - "Гайд владельца — как пользоваться ботом"
Cohesion: 0.18
Nodes (10): PDF-гайд из текста, Гайд владельца — как пользоваться ботом, Готовый подкаст из аудио, Наполнение контентом через Notion (основной способ), Настройка таблиц и Notion (разово, команды в боте), Пакеты магазина и цены, Подписка и триал (автоматически), Про большие файлы (+2 more)

### Community 25 - "catalog.py"
Cohesion: 0.24
Nodes (18): active_main_product(), all_seasons(), _bonus(), bonus_by_id(), bonus_by_keyword(), current_season(), _episode(), _matches() (+10 more)

### Community 26 - "generate_ambient.py"
Cohesion: 0.67
Nodes (5): _build_command(), _cli(), _filter_complex(), generate(), SynthSpec

### Community 27 - "Google Sheets — service-account JSON"
Cohesion: 0.50
Nodes (3): Google Sheets — service-account JSON, Что дальше делаю я, Шаги

### Community 45 - "seed_demo.py"
Cohesion: 0.23
Nodes (10): async_sessionmaker, AsyncEngine, AsyncSession, get_engine(), get_sessionmaker(), init_models(), fixture, main() (+2 more)

### Community 46 - "notion_sync.py"
Cohesion: 0.32
Nodes (10): Any, sync_catalog(), _upsert_bonus(), _upsert_episode(), Bonus, Episode, _seed(), test_keyword_bonus_cyrillic() (+2 more)

### Community 47 - "subscriptions.py"
Cohesion: 0.33
Nodes (11): expired(), grant(), has_used_trial(), is_active(), mark_expired(), _now(), datetime, Subscription (+3 more)

### Community 48 - "admin_content.py"
Cohesion: 0.33
Nodes (9): add_bonus(), add_episode(), add_product(), add_season(), counts(), set_workbook(), _tags(), _upsert() (+1 more)

## Knowledge Gaps
- **72 isolated node(s):** `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows`, `Запуск`, `Аудио-пайплайн` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `Settings`, `seasons.py`, `models.py`, `producer.py`, `PipelineInputs`, `seed_demo.py`, `notion.py`, `sheets.py`, `catalog.py`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `session_scope()` connect `session_scope` to `Settings`, `seasons.py`, `models.py`, `seed_demo.py`, `notion_sync.py`, `subscriptions.py`, `admin_content.py`, `get_settings`, `test_phase2.py`, `test_spec_features.py`, `catalog.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `producer.py`, `notion_sync.py`, `notion.py`, `get_settings`, `test_phase2.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Settings` (e.g. with `FakeBot` and `FakeBot`) actually correct?**
  _`Settings` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Settings` be split into smaller, more focused modules?**
  _Cohesion score 0.145748987854251 - nodes in this community are weakly interconnected._
- **Should `seasons.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09307244843997885 - nodes in this community are weakly interconnected._