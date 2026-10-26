# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **Orchestrator:** Astra GPT 6 / Gemini 4 Argon (inherited from Claude Opus 5.5 on 2026-10-25)
- **Current phase:** 2 — Безопасность ИИ и приватность (Приоритет 2)
- **Current task:** T20 (todo, Flash); T21a (todo, Flash); T22 (todo, Flash); T24a (todo, Flash)
- **Last reviewed:** T16, T18 — ACCEPT; CHECKPOINT-1 — PASS (Gemini 4 Argon, 2026-10-26)
- **Next action:**
  - **Gemini Flash 3.8** (все 4 задачи независимы `[PARALLEL-OK]`, выполнять по одной за сессию):
    1. `Выполни T20` — Защита CSV от формульных инъекций (`csv_safe.py` + `test_csv_safe.py`)
    2. `Выполни T21a` — Автономный модуль маскирования PII (`pii.py` + `test_pii.py` на ≥20 строках DE/EN/RU)
    3. `Выполни T22` — Каркас evals (`evals/schema.json`, `evals/run.py`, грейдеры и 5 сценариев)
    4. `Выполни T24a` — Автономный модуль инструментов чата и проверки чисел (`tools.py` + `test_chat_tools.py`)
  - Затем на **Flash 3.8**: `Выполни T23` (60 сценариев evals).
  - Затем на **Astra GPT 6**: `Выполни T21b` и `Выполни T24b` (склейка с `ai.py` / `imports.py` / `chat.py`).
- **Git:** инициализирован (ветка main, теги `baseline`, `phase-0`, `phase-1`)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | Да (`provisional: true`) |
| D2 | БД/авторизация: (A) локальный Postgres в Docker, (B) Supabase cloud, (C) пока SQLite + Alembic | T30 | — |
| D3 | Есть ли Android-эмулятор / iOS-симулятор / устройство для Maestro? | T42 | — |
| D4 | Кто проверит финансовый контент уроков (человек)? | T17/T18 | — |

## Последние проверенные показатели (CHECKPOINT-1, 2026-10-26)

- `python scripts/check.py` → 87/87
- `python scripts/generate-contracts.py --check` → 0 drift
- `npm run typecheck` → 0 ошибок
- `npx expo-doctor` → 20/20

## Orchestrator log

| Дата | Модель | Событие |
|---|---|---|
| 2026-10-25 | Claude Opus 5.5 | Создан протокол команды (AGENTS.md, skills, BACKLOG, HANDOFF) |
| 2026-10-25 | Claude Opus 5.5 | Review T00: ACCEPT |
| 2026-10-25 | Claude Opus 5.5 / Gemini 4 Argon | Review T01, T02: ACCEPT; наследование роли оркестратора; CHECKPOINT-0 закрыт |
| 2026-10-25 | Gemini 4 Argon | Review T10: ACCEPT (40/40 тестов) |
| 2026-10-25 | Gemini 4 Argon | Review T17: ACCEPT (10 мини-уроков в `content/lessons/`) |
| 2026-10-25 | Gemini 4 Argon | Review T11: ACCEPT (44/44 тестов, все 13 тестов фикстуры §9 зелёные) |
| 2026-10-26 | Gemini 4 Argon | Review T12: ACCEPT (52/52 тестов, Debt Engine + 500 рандомизированных инвариантов + 0 drift) |
| 2026-10-26 | Gemini 4 Argon | Review T13, T14: ACCEPT (65/65 тестов, экран `/debts` + каталог 15 действий §9) |
| 2026-10-26 | Gemini 4 Argon | Review T15: ACCEPT (74/74 тестов, MCDA + классы срочности + чувствительность ±20% + DecisionEvaluationSnapshot) |
| 2026-10-26 | Gemini 4 Argon | Review T16, T18: ACCEPT (87/87 тестов, координация §10 + Journey E мини-уроки); CHECKPOINT-1 закрыт (тег `phase-1`) |
| 2026-10-26 | Gemini 4 Argon | Перераспределён BACKLOG (Фазы 2–4): добавлена модель Astra GPT 6 (Orchestrator + Heavy Executor); задачи T21 и T24 разбиты на автономные модули для Flash 3.8 (`T21a`, `T24a`) и интеграцию для Astra GPT 6 (`T21b`, `T24b`); задачи `T22`, `T30`, `T31`, `T34`, `T40`, `T42`, `T44` детализированы и переведены на Flash 3.8 |

## Phase log

| Фаза | Статус | Дата | Итог |
|---|---|---|---|
| 0 | done | 2026-10-25 | Git инициализирован (`baseline`), `docs/release-readiness.md` приведён к §18, `docs/skills-manifest.md` создан (26 папок). Тег `phase-0`. |
| 1 | done | 2026-10-26 | Полностью реализовано финансовое ядро (T10–T18): фикстура §9, горизонтный прогноз баланса, Debt Engine + `/debts`, каталог 15 действий, MCDA + чувствительность ±20%, машина координации §10, 10 мини-уроков + Journey E `/learn`. 87/87 тестов, 0 drift, 0 TS ошибок. Тег `phase-1`. |
| 2 | in progress | 2026-10-26 | Ожидает старта задач на Flash 3.8 (`T20`, `T21a`, `T22`, `T24a`, `T23`) и последующей склейки на Astra GPT 6 (`T21b`, `T24b`). |
