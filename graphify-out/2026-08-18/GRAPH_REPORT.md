# Graph Report - music bot  (2026-08-17)

## Corpus Check
- 84 files · ~76,067 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 666 nodes · 1724 edges · 45 communities (44 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6b5f3639`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Мастер-документ проекта «Алёхина без тормозов»
- Сценарий Закрытый канал (оплата → invite)
- Обработка аудио (ffmpeg, без нейронки)
- Оплаты Telegram-нативно (ключевое решение)
- Апселлы фаза 2+ (отдельная плата)
- Google Sheets (витрина для клиента)
- Секреты / env-переменные (.env)
- Пошаговая инструкция по доступам для Юлии
- Автоматизация подкаста бизнес-блогера
- users.py
- Settings
- seasons.py
- session_scope
- producer.py
- PipelineInputs
- render_guide
- notion.py
- Алёхина без тормозов — бот и автоматизация подкаста
- get_settings
- sheets.py
- Технический стек
- Чеклист go-live (VPS)
- fulfillment.py
- Логика бота (спека клиента, 14.08) — источник правды
- Гайд владельца — как пользоваться ботом
- catalog.py
- generate_ambient.py
- Google Sheets — service-account JSON
- alehina-bot

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
- `test_split_guide_strips_markdown_title()` --calls--> `split_guide()`  [EXTRACTED]
  tests/test_pdf.py → bot/handlers/producer.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_notion_sync.py → config.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_phase2.py → config.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_scheduler_db.py → config.py
- `FakeBot` --uses--> `User`  [INFERRED]
  tests/test_phase2.py → db/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **6 сценариев Telegram-бота** — project_scenario_start, project_scenario_pdf_bonus, project_scenario_quiz, project_scenario_closed_channel, project_scenario_shop, project_scenario_admin [EXTRACTED 1.00]
- **Пайплайн: запись→Podster→анонс→бот→продажа** — project_audio_processing, project_podster, project_rss_feed, project_open_channel_announce, project_telegram_bot, project_monetization [EXTRACTED 1.00]
- **Механизм закрытого канала: оплата→invite→ревокация** — project_telegram_stars, project_invite_revocation, project_apscheduler, project_scenario_closed_channel [EXTRACTED 0.95]

## Communities (45 total, 1 thin omitted)

### Community 0 - "Мастер-документ проекта «Алёхина без тормозов»"
Cohesion: 0.15
Nodes (16): доступы-для-юлии.md (инструкция клиенту), Доступы + материалы от клиента, Дедлайн 3-4 недели от старта, Условия сделки, Прямая оплата, не через Kwork, Разделение труда исполнитель/клиент, Первый шаг: ffmpeg аудио-пайплайн, Проверка всей цепочки (аудио→Podster→бот→продажа) (+8 more)

### Community 1 - "Сценарий Закрытый канал (оплата → invite)"
Cohesion: 0.24
Nodes (10): Два Telegram-канала (открытый публичный + закрытый частный), CLOSED_CHANNEL_ID, Воронка продаж, Логика воронки: дешёвый гайд толкает в подписку, Монетизация, PDF-гайды 20-30 ₽, Сценарий Закрытый канал (оплата → invite), Сценарий PDF-бонус (+2 more)

### Community 2 - "Обработка аудио (ffmpeg, без нейронки)"
Cohesion: 0.25
Nodes (8): Обработка аудио (ffmpeg, без нейронки), PODSTER_RSS_URL, feedparser (RSS), ffmpeg, Авто-анонс в открытый Telegram-канал, Распространение подкаста (Podster → площадки), Podster (хостинг аудио), RSS-лента подкаста

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

### Community 9 - "users.py"
Cohesion: 0.15
Nodes (26): add_purchased_season(), all_user_ids(), _aware(), can_trial(), drop_subscription(), expired_subscribers(), get_or_create(), grant_subscription() (+18 more)

### Community 10 - "Settings"
Cohesion: 0.26
Nodes (18): BaseSettings, is_seen(), mark_seen(), Settings, announce_text(), _broadcast(), notify_finale(), notify_ready() (+10 more)

### Community 11 - "seasons.py"
Cohesion: 0.10
Nodes (50): buy_club(), club_bonuses(), club_trial(), _offer(), Bot, callback_query, CallbackQuery, _return_url() (+42 more)

### Community 12 - "session_scope"
Cohesion: 0.06
Nodes (65): async_sessionmaker, AsyncEngine, AsyncSession, add_bonus(), add_episode(), add_product(), add_season(), counts() (+57 more)

### Community 13 - "producer.py"
Cohesion: 0.07
Nodes (56): bonus_by_button(), deliver(), Any, callback_query, CallbackQuery, Message, choose_ambient(), _is_owner() (+48 more)

### Community 14 - "PipelineInputs"
Cohesion: 0.22
Nodes (25): make_episode(), Path, AudioProfile, build_filter_complex(), _cli(), _ordered_inputs(), PipelineError, PipelineInputs (+17 more)

### Community 15 - "render_guide"
Cohesion: 0.17
Nodes (21): build_guide(), Path, _data_uri(), _ensure_gtk(), GuideStyle, _logo_block(), PdfError, Path (+13 more)

### Community 16 - "notion.py"
Cohesion: 0.16
Nodes (25): catalog_pages(), _client(), create_episodes_db(), _create_episodes_db_sync(), episode_id(), episode_status(), episode_title(), extract_catalog() (+17 more)

### Community 17 - "Алёхина без тормозов — бот и автоматизация подкаста"
Cohesion: 0.11
Nodes (16): Ассеты от клиента (кладём в `media/assets/`), Аудио-пайплайн (ffmpeg), Запуск, Профиль звука, Docker Compose (рекомендуется), GTK для WeasyPrint на Windows, systemd (без Docker), Алёхина без тормозов — бот и автоматизация подкаста (+8 more)

### Community 18 - "get_settings"
Cohesion: 0.06
Nodes (54): BaseMiddleware, BaseStorage, add_bonus(), add_episode(), add_product(), add_season(), admin_stats(), content_counts() (+46 more)

### Community 19 - "sheets.py"
Cohesion: 0.31
Nodes (13): add_contact(), add_sale(), _append(), _append_sync(), bootstrap(), _bootstrap_sync(), _client(), _now() (+5 more)

### Community 20 - "Технический стек"
Cohesion: 0.24
Nodes (10): aiogram 3.x, Caddy (авто-TLS HTTPS для вебхуков), BOT_TOKEN, FastAPI + uvicorn, httpx (async HTTP-клиент), Redis (FSM-хранилище), Сценарий /start (приветствие + кнопки), Технический стек (+2 more)

### Community 21 - "Чеклист go-live (VPS)"
Cohesion: 0.07
Nodes (25): 1. Подготовка сервера, 2. .env, 3. Запуск, 4. Числовой id закрытого канала, 5.05. Webhook ЮKassa (обязательно для оплат), 5.1. Шрифты PDF (только без Docker), 5. Notion и Sheets, 6. Проверка цепочки (+17 more)

### Community 22 - "fulfillment.py"
Cohesion: 0.24
Nodes (16): _already_done(), fulfill(), _fulfill_all(), _fulfill_season(), _fulfill_sub(), _fulfill_workbook(), _invite_link(), Any (+8 more)

### Community 23 - "Логика бота (спека клиента, 14.08) — источник правды"
Cohesion: 0.20
Nodes (9): БД (таблицы), Логика бота (спека клиента, 14.08) — источник правды, Модель, Статус реализации (на 2026-08-16) — готово к деплою, Сценарии, Технические, Фазы, Цены (жёстко; скидка подписчику по `is_subscribed`) (+1 more)

### Community 24 - "Гайд владельца — как пользоваться ботом"
Cohesion: 0.18
Nodes (10): PDF-гайд из текста, Гайд владельца — как пользоваться ботом, Готовый подкаст из аудио, Наполнение контентом через Notion (основной способ), Настройка таблиц и Notion (разово, команды в боте), Пакеты магазина и цены, Подписка и триал (автоматически), Про большие файлы (+2 more)

### Community 25 - "catalog.py"
Cohesion: 0.13
Nodes (27): active_main_product(), all_seasons(), all_seasons_pack(), _bonus(), bonus_by_id(), bonus_by_keyword(), current_season(), _episode() (+19 more)

### Community 26 - "generate_ambient.py"
Cohesion: 0.67
Nodes (5): _build_command(), _cli(), _filter_complex(), generate(), SynthSpec

### Community 27 - "Google Sheets — service-account JSON"
Cohesion: 0.50
Nodes (3): Google Sheets — service-account JSON, Что дальше делаю я, Шаги

## Knowledge Gaps
- **72 isolated node(s):** `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows`, `Запуск`, `Аудио-пайплайн` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `Settings`, `seasons.py`, `session_scope`, `producer.py`, `PipelineInputs`, `notion.py`, `sheets.py`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `session_scope()` connect `session_scope` to `users.py`, `Settings`, `seasons.py`, `get_settings`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `session_scope`, `producer.py`, `notion.py`, `get_settings`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Settings` (e.g. with `FakeBot` and `FakeBot`) actually correct?**
  _`Settings` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `seasons.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10101010101010101 - nodes in this community are weakly interconnected._
- **Should `session_scope` be split into smaller, more focused modules?**
  _Cohesion score 0.06358543417366946 - nodes in this community are weakly interconnected._