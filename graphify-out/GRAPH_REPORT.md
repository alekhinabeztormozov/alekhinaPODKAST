# Graph Report - music bot  (2026-08-31)

## Corpus Check
- 89 files · ~79,213 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 766 nodes · 2001 edges · 54 communities (53 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `05184bb0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Мастер-документ проекта «Алёхина без тормозов»
- Сценарий Закрытый канал (оплата → invite)
- Технический стек
- Оплаты Telegram-нативно (ключевое решение)
- Апселлы фаза 2+ (отдельная плата)
- Google Sheets (витрина для клиента)
- Секреты / env-переменные (.env)
- Пошаговая инструкция по доступам для Юлии
- Автоматизация подкаста бизнес-блогера
- test_vk.py
- get_settings
- producer.py
- Settings
- notion_sync.py
- PipelineInputs
- render_guide
- notion.py
- Алёхина без тормозов — бот и автоматизация подкаста
- admin.py
- session_scope
- sheets.py
- Чеклист go-live (VPS)
- fulfillment.py
- Логика бота (спека клиента, 14.08) — источник правды
- Гайд владельца — как пользоваться ботом
- catalog.py
- generate_ambient.py
- Google Sheets — service-account JSON
- alehina-bot
- ThrottlingMiddleware
- models.py
- test_spec_features.py
- seed_demo.py
- admin_content.py
- Season
- test_phase2.py
- test_core_flows.py

## God Nodes (most connected - your core abstractions)
1. `session_scope()` - 75 edges
2. `get_settings()` - 68 edges
3. `Settings` - 44 edges
4. `show()` - 26 edges
5. `sync_catalog()` - 25 edges
6. `Season` - 23 edges
7. `is_subscribed()` - 19 edges
8. `handle_incoming()` - 18 edges
9. `PipelineInputs` - 18 edges
10. `fulfill()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `set_workbook()` --calls--> `session_scope()`  [EXTRACTED]
  bot/services/admin_content.py → db/session.py
- `test_subscription_renewal_stacks()` --calls--> `grant_subscription()`  [EXTRACTED]
  tests/test_spec_features.py → bot/services/users.py
- `test_voice_demo_once()` --calls--> `take_voice_demo()`  [EXTRACTED]
  tests/test_core_flows.py → bot/services/users.py
- `FakeBot` --uses--> `Settings`  [INFERRED]
  tests/test_phase2.py → config.py
- `_Sink` --uses--> `Settings`  [INFERRED]
  tests/test_vk.py → config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **6 сценариев Telegram-бота** — project_scenario_start, project_scenario_pdf_bonus, project_scenario_quiz, project_scenario_closed_channel, project_scenario_shop, project_scenario_admin [EXTRACTED 1.00]
- **Пайплайн: запись→Podster→анонс→бот→продажа** — project_audio_processing, project_podster, project_rss_feed, project_open_channel_announce, project_telegram_bot, project_monetization [EXTRACTED 1.00]
- **Механизм закрытого канала: оплата→invite→ревокация** — project_telegram_stars, project_invite_revocation, project_apscheduler, project_scenario_closed_channel [EXTRACTED 0.95]

## Communities (54 total, 1 thin omitted)

### Community 0 - "Мастер-документ проекта «Алёхина без тормозов»"
Cohesion: 0.15
Nodes (16): доступы-для-юлии.md (инструкция клиенту), Доступы + материалы от клиента, Дедлайн 3-4 недели от старта, Условия сделки, Прямая оплата, не через Kwork, Разделение труда исполнитель/клиент, Первый шаг: ffmpeg аудио-пайплайн, Проверка всей цепочки (аудио→Podster→бот→продажа) (+8 more)

### Community 1 - "Сценарий Закрытый канал (оплата → invite)"
Cohesion: 0.24
Nodes (10): Два Telegram-канала (открытый публичный + закрытый частный), CLOSED_CHANNEL_ID, Воронка продаж, Логика воронки: дешёвый гайд толкает в подписку, Монетизация, PDF-гайды 20-30 ₽, Сценарий Закрытый канал (оплата → invite), Сценарий PDF-бонус (+2 more)

### Community 2 - "Технический стек"
Cohesion: 0.18
Nodes (13): Обработка аудио (ffmpeg, без нейронки), Caddy (авто-TLS HTTPS для вебхуков), PODSTER_RSS_URL, FastAPI + uvicorn, feedparser (RSS), ffmpeg, httpx (async HTTP-клиент), Авто-анонс в открытый Telegram-канал (+5 more)

### Community 3 - "Оплаты Telegram-нативно (ключевое решение)"
Cohesion: 0.29
Nodes (7): APScheduler, Объём контента (планирование), Одноразовый invite + ревокация доступа, Оплаты Telegram-нативно (ключевое решение), Планировщик отложенной публикации, VK Donut / VK Товары (отклонено для денег), VK только как площадка RSS

### Community 4 - "Апселлы фаза 2+ (отдельная плата)"
Cohesion: 0.20
Nodes (10): Продажа книг, Игра «бизнес-покер», Лендинг под подкасты, Марафоны, бизнес-сессии, Детерминированные пайплайны без нейронки, Генерация PDF (WeasyPrint, без нейронки), Рилсы / AI-видео (единственная нейронка), Апселлы фаза 2+ (отдельная плата) (+2 more)

### Community 5 - "Google Sheets (витрина для клиента)"
Cohesion: 0.25
Nodes (9): Хранилища данных, GOOGLE_SA_JSON, NOTION_TOKEN, Google Sheets (витрина для клиента), Идемпотентность оплат/выдачи, Notion (пульт контента, база «Эпизоды»), Внутренняя БД PostgreSQL (источник правды), Надёжность (заложить с нуля) (+1 more)

### Community 6 - "Секреты / env-переменные (.env)"
Cohesion: 0.14
Nodes (16): aiogram 3.x, ADMIN_TG_IDS, BOT_TOKEN, DATABASE_URL, GOOGLE_SHEETS_ID, NOTION_DB_EPISODES, OPEN_CHANNEL_ID, PAYMENT_PROVIDER_TOKEN (+8 more)

### Community 7 - "Пошаговая инструкция по доступам для Юлии"
Cohesion: 0.33
Nodes (6): BotFather (создание бота, получение токена), Пошаговая инструкция по доступам для Юлии, Notion Internal Integration Secret, Безопасная передача секретов (в TG, удалить после подтверждения), gspread + google-auth (service account), Единая почта Gmail под весь проект

### Community 8 - "Автоматизация подкаста бизнес-блогера"
Cohesion: 0.33
Nodes (6): Стиль сообщений клиенту (прямые кавычки, короткое тире, сплошные абзацы), Разработчик Лев (соло, lev.dev), Автоматизация подкаста бизнес-блогера, Принцип: записал один раз → система разнесла и продала, Windows-заметка PYTHONIOENCODING=utf-8, Юлия Алёхина (клиент, бизнес-стратег)

### Community 9 - "test_vk.py"
Cohesion: 0.12
Nodes (30): _bonus_text(), _club_text(), _command(), handle_incoming(), main_keyboard(), _none_text(), _results_text(), _search_prompt() (+22 more)

### Community 10 - "get_settings"
Cohesion: 0.06
Nodes (64): BaseStorage, bonus_by_button(), deliver(), Any, callback_query, CallbackQuery, Message, buy_club() (+56 more)

### Community 11 - "producer.py"
Cohesion: 0.07
Nodes (63): choose_ambient(), _is_owner(), list_ambients(), owner_only(), owner_panel(), preview_ambient(), _process(), Bot (+55 more)

### Community 12 - "Settings"
Cohesion: 0.10
Nodes (34): BaseSettings, published_pages(), publish_ready_posts(), publish_vk_posts(), Bot, any_seen(), is_seen(), mark_seen() (+26 more)

### Community 13 - "notion_sync.py"
Cohesion: 0.12
Nodes (37): bonus_by_keyword(), season_bonuses(), _keyword_owners(), _prune_missing(), Any, Ключевое слово (регистр не важен) → bonus_id, который его уже занял., Почему страница не попала ни в эпизоды, ни в бонусы., Сезоны по слагу и по названию (регистр не важен) + текущий сезон как запасной. (+29 more)

### Community 14 - "PipelineInputs"
Cohesion: 0.22
Nodes (25): make_episode(), Path, AudioProfile, build_filter_complex(), _cli(), _ordered_inputs(), PipelineError, PipelineInputs (+17 more)

### Community 15 - "render_guide"
Cohesion: 0.19
Nodes (20): build_guide(), Path, _data_uri(), _ensure_gtk(), GuideStyle, _logo_block(), PdfError, Path (+12 more)

### Community 16 - "notion.py"
Cohesion: 0.16
Nodes (25): catalog_pages(), _client(), create_episodes_db(), _create_episodes_db_sync(), episode_id(), episode_status(), episode_title(), extract_catalog() (+17 more)

### Community 17 - "Алёхина без тормозов — бот и автоматизация подкаста"
Cohesion: 0.11
Nodes (16): Ассеты от клиента (кладём в `media/assets/`), Аудио-пайплайн (ffmpeg), Запуск, Профиль звука, Docker Compose (рекомендуется), GTK для WeasyPrint на Windows, systemd (без Docker), Алёхина без тормозов — бот и автоматизация подкаста (+8 more)

### Community 18 - "admin.py"
Cohesion: 0.34
Nodes (16): add_bonus(), add_episode(), add_product(), add_season(), admin_stats(), content_counts(), _is_admin(), Message (+8 more)

### Community 19 - "session_scope"
Cohesion: 0.22
Nodes (23): all_user_ids(), _aware(), can_trial(), drop_subscription(), expired_subscribers(), get_or_create(), grant_subscription(), grant_trial() (+15 more)

### Community 20 - "sheets.py"
Cohesion: 0.31
Nodes (13): add_contact(), add_sale(), _append(), _append_sync(), bootstrap(), _bootstrap_sync(), _client(), _now() (+5 more)

### Community 21 - "Чеклист go-live (VPS)"
Cohesion: 0.07
Nodes (25): 1. Подготовка сервера, 2. .env, 3. Запуск, 4. Числовой id закрытого канала, 5.05. Webhook ЮKassa (обязательно для оплат), 5.1. Шрифты PDF (только без Docker), 5. Notion и Sheets, 6. Проверка цепочки (+17 more)

### Community 22 - "fulfillment.py"
Cohesion: 0.33
Nodes (15): _already_done(), fulfill(), _fulfill_all(), _fulfill_season(), _fulfill_sub(), _fulfill_workbook(), _invite_link(), _notify() (+7 more)

### Community 23 - "Логика бота (спека клиента, 14.08) — источник правды"
Cohesion: 0.20
Nodes (9): БД (таблицы), Логика бота (спека клиента, 14.08) — источник правды, Модель, Статус реализации (на 2026-08-16) — готово к деплою, Сценарии, Технические, Фазы, Цены (жёстко; скидка подписчику по `is_subscribed`) (+1 more)

### Community 24 - "Гайд владельца — как пользоваться ботом"
Cohesion: 0.17
Nodes (11): PDF-гайд из текста, ВКонтакте (верх воронки), Гайд владельца — как пользоваться ботом, Готовый подкаст из аудио, Наполнение контентом через Notion (основной способ), Настройка таблиц и Notion (разово, команды в боте), Пакеты магазина и цены, Подписка и триал (автоматически) (+3 more)

### Community 25 - "catalog.py"
Cohesion: 0.12
Nodes (43): callback_query, CallbackQuery, show_intensive(), _all_price(), buy_all_seasons(), buy_season(), buy_workbook(), _pay() (+35 more)

### Community 26 - "generate_ambient.py"
Cohesion: 0.67
Nodes (5): _build_command(), _cli(), _filter_complex(), generate(), SynthSpec

### Community 27 - "Google Sheets — service-account JSON"
Cohesion: 0.50
Nodes (3): Google Sheets — service-account JSON, Что дальше делаю я, Шаги

### Community 45 - "ThrottlingMiddleware"
Cohesion: 0.27
Nodes (6): BaseMiddleware, Any, ThrottlingMiddleware, TelegramObject, test_missing_user_passes_through(), test_second_call_suppressed()

### Community 46 - "models.py"
Cohesion: 0.22
Nodes (14): Записать контакт в БД + Google Sheets. Один пользователь = одна строка (дедуп…, record(), record(), Base, Contact, ProcessedPayment, Sale, DatabaseNotConfigured (+6 more)

### Community 47 - "test_spec_features.py"
Cohesion: 0.28
Nodes (11): has_season(), FakeBot, _reserved(), _seed_seasons(), test_fulfill_all_grants_everything(), test_fulfill_releases_reservation_on_grant_failure(), test_fulfill_season_and_idempotent(), test_fulfill_send_failure_still_grants() (+3 more)

### Community 48 - "seed_demo.py"
Cohesion: 0.23
Nodes (10): async_sessionmaker, AsyncEngine, AsyncSession, get_engine(), get_sessionmaker(), init_models(), main(), _upsert() (+2 more)

### Community 49 - "admin_content.py"
Cohesion: 0.27
Nodes (11): add_bonus(), add_episode(), add_product(), add_season(), counts(), _make_only_current(), Текущий сезон ровно один: current_season() берёт первую попавшуюся строку с…, set_workbook() (+3 more)

### Community 50 - "Season"
Cohesion: 0.26
Nodes (6): Season, FakeCallback, FakeMessage, Не подписчик жмёт «Бонусы клуба» — должен увидеть оффер, а не упасть., test_club_bonuses_offers_subscription_to_guest(), test_club_bonuses_subscriber_without_bonuses()

### Community 51 - "test_phase2.py"
Cohesion: 0.29
Nodes (5): MainProduct, FakeBot, test_active_intensive(), test_all_seasons_access(), test_finale_broadcast()

### Community 52 - "test_core_flows.py"
Cohesion: 0.43
Nodes (6): Episode, _seed(), test_keyword_bonus_cyrillic(), test_search_by_tag_and_title(), test_season_purchase(), test_voice_demo_once()

## Knowledge Gaps
- **72 isolated node(s):** `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows`, `Запуск`, `Аудио-пайплайн` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `get_settings` to `test_vk.py`, `producer.py`, `Settings`, `PipelineInputs`, `models.py`, `notion.py`, `seed_demo.py`, `admin.py`, `sheets.py`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `session_scope()` connect `session_scope` to `test_vk.py`, `Settings`, `notion_sync.py`, `models.py`, `test_spec_features.py`, `seed_demo.py`, `admin_content.py`, `admin.py`, `Season`, `test_core_flows.py`, `test_phase2.py`, `fulfillment.py`, `catalog.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `test_vk.py`, `get_settings`, `producer.py`, `notion_sync.py`, `admin.py`, `test_phase2.py`, `fulfillment.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `FakeBot` and `FakeBot`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alehina-bot`, `Требования`, `GTK для WeasyPrint на Windows` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Секреты / env-переменные (.env)` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._
- **Should `test_vk.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12100840336134454 - nodes in this community are weakly interconnected._