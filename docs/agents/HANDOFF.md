# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **Orchestrator:** Gemini 4 Argon (inherited from Claude Opus 5.5 on 2026-10-25)
- **Current phase:** 1 — Финансовое ядро (Приоритет 1)
- **Current task:** — (T11 принята)
- **Last reviewed:** T11 — ACCEPT (Gemini 4 Argon, 2026-10-25)
- **Next action:** **Gemini 4 Argon** → `Выполни T12` (Debt Engine — калькулятор долгов, стратегии Avalanche и Snowball, эндпоинты `/v1/debts`).
- **Git:** инициализирован (ветка main, теги `baseline`, `phase-0`)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | — |
| D2 | БД/авторизация: (A) локальный Postgres в Docker, (B) Supabase cloud, (C) пока SQLite + Alembic | T30 | — |
| D3 | Есть ли Android-эмулятор / iOS-симулятор / устройство для Maestro? | T42 | — |
| D4 | Кто проверит финансовый контент уроков (человек)? | T17/T18 | — |

## Последние проверенные показатели (baseline 2026-10-25, из PROGRESS.md)

- `python scripts/check.py` → 44/44
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

## Phase log

| Фаза | Статус | Дата | Итог |
|---|---|---|---|
| 0 | done | 2026-10-25 | Git инициализирован (`baseline`), `docs/release-readiness.md` приведён к §18, `docs/skills-manifest.md` создан (26 папок). Тег `phase-0`. |
| 1 | in progress | 2026-10-25 | T10, T17, T11 приняты; следующая задача: T12 (Argon) |
