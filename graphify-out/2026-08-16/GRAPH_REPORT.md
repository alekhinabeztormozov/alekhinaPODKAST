# Graph Report - music bot  (2026-08-14)

## Corpus Check
- 77 files · ~97,104 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 546 nodes · 1300 edges · 44 communities (43 shown, 1 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `67bf1fc4`
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
- session_scope
- get_settings
- common.py
- models.py
- producer.py
- PipelineInputs
- render_guide
- notion.py
- Алёхина без тормозов — бот и автоматизация подкаста
- admin.py
- sheets.py
- ThrottlingMiddleware
- Деплой на VPS (runbook)
- Технический стек
- Логика бота (спека клиента, 14.08) — источник правды
- Гайд владельца — как пользоваться ботом
- Настройка оплат в Telegram
- generate_ambient.py
- Google Sheets — service-account JSON
- alehina-bot

## God Nodes (most connected - your core abstractions)
1. `session_scope()` - 59 edges
2. `get_settings()` - 49 edges
3. `Settings` - 30 edges
4. `show()` - 18 edges
5. `Base` - 17 edges
6. `get_ambients()` - 15 edges
7. `Мастер-документ проекта «Алёхина без тормозов»` - 15 edges
8. `User` - 13 edges
9. `PipelineInputs` - 13 edges
10. `Технический стек` - 13 edges

## Surprising Connections (you probably didn't know these)
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_phase2.py → config.py
- `BotFather (создание бота, получение токена)` --references--> `Telegram-бот (aiogram 3.x)`  [EXTRACTED]
  доступы-для-юлии.md → PROJECT.md
- `Два Telegram-канала (открытый публичный + закрытый частный)` --references--> `Сценарий Закрытый канал (оплата → invite)`  [INFERRED]
  доступы-для-юлии.md → PROJECT.md
- `_is_admin()` --references--> `Settings`  [EXTRACTED]
  bot/handlers/admin.py → config.py
- `admin_stats()` --calls--> `get_settings()`  [EXTRACTED]
  bot/handlers/admin.py → config.py

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

### Community 9 - "session_scope"
Cohesion: 0.08
Nodes (56): message, route_text(), add_bonus(), add_episode(), add_product(), add_season(), counts(), _tags() (+48 more)

### Community 10 - "get_settings"
Cohesion: 0.08
Nodes (44): BaseSettings, BaseStorage, bonus_by_button(), deliver(), Any, callback_query, CallbackQuery, Message (+36 more)

### Community 11 - "common.py"
Cohesion: 0.08
Nodes (50): buy_club(), club_bonuses(), callback_query, CallbackQuery, _return_url(), show_club(), callback_query, CallbackQuery (+42 more)

### Community 12 - "models.py"
Cohesion: 0.09
Nodes (39): async_sessionmaker, AsyncEngine, AsyncSession, _already_done(), fulfill(), _invite_link(), Any, Bot (+31 more)

### Community 13 - "producer.py"
Cohesion: 0.11
Nodes (36): choose_ambient(), _is_owner(), list_ambients(), owner_only(), owner_panel(), preview_ambient(), _process(), Bot (+28 more)

### Community 14 - "PipelineInputs"
Cohesion: 0.27
Nodes (18): make_episode(), Path, AudioProfile, build_filter_complex(), _cli(), _ordered_input_paths(), PipelineError, PipelineInputs (+10 more)

### Community 15 - "render_guide"
Cohesion: 0.23
Nodes (16): build_guide(), Path, _ensure_gtk(), GuideStyle, _logo_block(), PdfError, Path, RuntimeError (+8 more)

### Community 16 - "notion.py"
Cohesion: 0.22
Nodes (13): _client(), create_episodes_db(), _create_episodes_db_sync(), episode_id(), episode_status(), episode_title(), NotionNotConfigured, Any (+5 more)

### Community 17 - "Алёхина без тормозов — бот и автоматизация подкаста"
Cohesion: 0.11
Nodes (16): Ассеты от клиента (кладём в `media/assets/`), Аудио-пайплайн (ffmpeg), Запуск, Профиль звука, Docker Compose (рекомендуется), GTK для WeasyPrint на Windows, systemd (без Docker), Алёхина без тормозов — бот и автоматизация подкаста (+8 more)

### Community 18 - "admin.py"
Cohesion: 0.37
Nodes (14): add_bonus(), add_episode(), add_product(), add_season(), admin_stats(), content_counts(), _is_admin(), Message (+6 more)

### Community 19 - "sheets.py"
Cohesion: 0.31
Nodes (13): add_contact(), add_sale(), _append(), _append_sync(), bootstrap(), _bootstrap_sync(), _client(), _now() (+5 more)

### Community 20 - "ThrottlingMiddleware"
Cohesion: 0.27
Nodes (6): BaseMiddleware, Any, ThrottlingMiddleware, TelegramObject, test_missing_user_passes_through(), test_second_call_suppressed()

### Community 21 - "Деплой на VPS (runbook)"
Cohesion: 0.20
Nodes (9): 1. Подготовка сервера, 2. .env, 3. Запуск, 4. Числовой id закрытого канала, 5.05. Webhook ЮKassa (обязательно для оплат), 5.1. Шрифты PDF (только без Docker), 5. Notion и Sheets, 6. Проверка цепочки (+1 more)

### Community 22 - "Технический стек"
Cohesion: 0.24
Nodes (10): aiogram 3.x, Caddy (авто-TLS HTTPS для вебхуков), BOT_TOKEN, FastAPI + uvicorn, httpx (async HTTP-клиент), Redis (FSM-хранилище), Сценарий /start (приветствие + кнопки), Технический стек (+2 more)

### Community 23 - "Логика бота (спека клиента, 14.08) — источник правды"
Cohesion: 0.22
Nodes (8): БД (таблицы), Логика бота (спека клиента, 14.08) — источник правды, Модель, Сценарии, Технические, Фазы, Цены (жёстко; скидка подписчику по `is_subscribed`), Что переиспользуем из готового

### Community 24 - "Гайд владельца — как пользоваться ботом"
Cohesion: 0.25
Nodes (7): PDF-гайд из текста, Гайд владельца — как пользоваться ботом, Готовый подкаст из аудио, Наполнение контентом (сезоны, бонусы, эпизоды, интенсивы), Настройка таблиц и Notion (разово, команды в боте), Про большие файлы, Статистика

### Community 25 - "Настройка оплат в Telegram"
Cohesion: 0.33
Nodes (5): Запасной вариант: Telegram Stars, Как я проведу тебя при запуске, Настройка оплат в Telegram, Основной вариант: ЮMoney / ЮKassa (рубли), Что уже готово в коде

### Community 26 - "generate_ambient.py"
Cohesion: 0.67
Nodes (5): _build_command(), _cli(), _filter_complex(), generate(), SynthSpec

### Community 27 - "Google Sheets — service-account JSON"
Cohesion: 0.50
Nodes (3): Google Sheets — service-account JSON, Что дальше делаю я, Шаги

## Knowledge Gaps
- **59 isolated node(s):** `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows`, `Запуск`, `Аудио-пайплайн` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `session_scope`, `common.py`, `models.py`, `producer.py`, `PipelineInputs`, `notion.py`, `admin.py`, `sheets.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `session_scope()` connect `session_scope` to `common.py`, `admin.py`, `get_settings`, `models.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `Settings` connect `get_settings` to `session_scope`, `admin.py`, `models.py`, `producer.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Settings` (e.g. with `FakeBot` and `FakeBot`) actually correct?**
  _`Settings` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows` to the rest of the system?**
  _59 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `session_scope` be split into smaller, more focused modules?**
  _Cohesion score 0.08344988344988345 - nodes in this community are weakly interconnected._
- **Should `get_settings` be split into smaller, more focused modules?**
  _Cohesion score 0.08299240210403273 - nodes in this community are weakly interconnected._