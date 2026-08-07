# Google Sheets — service-account JSON

Боту для записи в таблицы нужен ключ service-account (JSON), не пароль от почты. Делается на единой почте проекта (`alekhinabeztormozov@gmail.com`), ~10 минут.

## Шаги

1. Открой console.cloud.google.com, войди под единой почтой проекта.
2. Вверху создай проект: выпадающий список проектов → New Project → имя `alehina-bot` → Create.
3. Включи два API: APIs & Services → Library → найди и нажми Enable для:
   - Google Sheets API
   - Google Drive API
4. Создай service-account: APIs & Services → Credentials → Create Credentials → Service account → имя `sheets-bot` → Create and Continue → Done (роли не нужны).
5. Скачай ключ: открой созданный service-account → вкладка Keys → Add Key → Create new key → тип **JSON** → Create. Скачается файл `*.json`.
6. **Пришли мне этот JSON-файл** в Telegram. Внутри есть строка `client_email` вида `sheets-bot@alehina-bot.iam.gserviceaccount.com`.
7. Создай (или открой) Google-таблицу проекта, нажми Share, добавь этот `client_email` с правом **Editor**.
8. Пришли мне **ID таблицы** — из её ссылки: `docs.google.com/spreadsheets/d/`**`ЭТОТ_ID`**`/edit`.

## Что дальше делаю я

- Кладу JSON на сервер, путь в `GOOGLE_SA_JSON`, ID в `GOOGLE_SHEETS_ID` (в `.env`, не в git).
- Команда `/setup_sheets` создаёт 4 листа с заголовками: База контактов, Продажи, Участники марафона, Игры и амбассадоры.

JSON — это секрет (даёт доступ на запись в таблицы). Храню локально, в git не попадает. После сдачи ключ можно отозвать в том же Credentials.
