# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **Orchestrator:** Claude Opus 5.5 (since 2026-10-25)
- **Current phase:** 0 — Фундамент командной работы
- **Current task:** T01, T02 (review, Gemini Flash 3.8)
- **Last reviewed:** T00 — ACCEPT (Claude Opus 5.5, 2026-10-25)
- **Next action:** Оркестратор Claude Opus 5.5: `Проверь T01, T02` (затем `Чекпоинт фазы 0`)
- **Git:** инициализирован (ветка main, тег `baseline` = откат к состоянию до мультиагентной работы)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | — |
| D2 | БД/авторизация: (A) локальный Postgres в Docker, (B) Supabase cloud, (C) пока SQLite + Alembic | T30 | — |
| D3 | Есть ли Android-эмулятор / iOS-симулятор / устройство для Maestro? | T42 | — |
| D4 | Кто проверит финансовый контент уроков (человек)? | T17/T18 | — |

## Последние проверенные показатели (baseline 2026-10-25, из PROGRESS.md)

- `python scripts/check.py` → 31/31
- `npm run typecheck` → 0 ошибок
- `npx expo-doctor` → 20/20

## Orchestrator log

| Дата | Модель | Событие |
|---|---|---|
| 2026-10-25 | Claude Opus 5.5 | Создан протокол команды (AGENTS.md, skills, BACKLOG, HANDOFF) |
| 2026-10-25 | Claude Opus 5.5 | Review T00: ACCEPT |

## Phase log

| Фаза | Статус | Дата | Итог |
|---|---|---|---|
| 0 | in progress | — | — |
