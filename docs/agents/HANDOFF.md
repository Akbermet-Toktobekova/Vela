# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **Orchestrator:** Codex (GPT-6), review session 2026-10-26
- **Current phase:** 2 — Безопасность ИИ и приватность (Приоритет 2)
- **Current task:** T21b — done (ACCEPT); T22 (включая T22b) — review (5/5 offline evals PASS, 25/25 harness tests OK, 166/166 backend tests OK); T24a — rework.
- **Last reviewed:** 2026-10-26, Codex: T21b ACCEPT; T24a attempt 3 REWORK; backend 164/164, targeted 47/47, contract drift 0.
- **Next action:**
  - Astra GPT 6 / Argon: `Выполни T24a` (четыре конкретных замечания в отчёте).
  - Затем `Выполни T22b`: отдельный scoped fallback fix, устраняющий цикл зависимостей T22 → T23 → T24b.
  - Оркестратор: `Проверь T22` (5/5 offline evals PASS, все замечания Re-review закрыты).
- **Git:** инициализирован (ветка main, теги `baseline`, `phase-0`, `phase-1`)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | Да (`provisional: true`) |
| D2 | БД/авторизация: (A) локальный Postgres в Docker, (B) Supabase cloud, (C) пока SQLite + Alembic | T30 | — |
| D3 | Есть ли Android-эмулятор / iOS-симулятор / устройство для Maestro? | T42 | — |
| D4 | Кто проверит финансовый контент уроков (человек)? | T17/T18 | — |

## Последние проверенные показатели (CHECKPOINT-1, 2026-10-26)

- `python scripts/check.py` → 152/152
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
| 2026-10-26 | Codex (GPT-6) | Review T20: ACCEPT; Review T21a, T22, T24a (attempts 1–2): REWORK → ESCALATE |
| 2026-10-26 | Gemini 4 Argon | Review T21a (attempt 3, выполнен Codex heavy executor): ACCEPT (16/16 тестов PII, 152/152 `check.py`); разблокирована `T21b` |

## Phase log

| Фаза | Статус | Дата | Итог |
|---|---|---|---|
| 0 | done | 2026-10-25 | Git инициализирован (`baseline`), `docs/release-readiness.md` приведён к §18, `docs/skills-manifest.md` создан (26 папок). Тег `phase-0`. |
| 1 | done | 2026-10-26 | Полностью реализовано финансовое ядро (T10–T18): фикстура §9, горизонтный прогноз баланса, Debt Engine + `/debts`, каталог 15 действий, MCDA + чувствительность ±20%, машина координации §10, 10 мини-уроков + Journey E `/learn`. 87/87 тестов, 0 drift, 0 TS ошибок. Тег `phase-1`. |
| 2 | in progress | 2026-10-26 | Ожидает старта задач на Flash 3.8 (`T20`, `T21a`, `T22`, `T24a`, `T23`) и последующей склейки на Astra GPT 6 (`T21b`, `T24b`). |

## Review batch — 2026-10-26

Codex (GPT-6): T20 ACCEPT; T21a/T22/T24a REWORK. Детальные воспроизведения и требования к регрессиям — в разделах Review соответствующих отчётов. Проверки: 132/132 backend, 45/45 targeted, schema 5/5, offline evals 5/5, contract drift 0. Зелёные проверки не покрывали найденные дефекты. Следующая задача: Gemini Flash 3.8 → `Выполни T21a`.

### Git persistence

Коммит ревью не создан: `git add -A` и `git commit` завершились `fatal: Unable to create .../.git/index.lock: Permission denied`. Каталог .git доступен только для чтения в текущей среде. Изменения отчётов, BACKLOG, HANDOFF и фактического eval-отчёта сохранены в рабочем дереве.

## Re-review batch — 2026-10-26

T20 ACCEPT confirmed; T21a/T22/T24a ESCALATE → Argon после второй попытки Flash. Backend 148/148, targeted 61/61, schema 5/5, contract drift 0; offline evals 4/5 (exit 1). Подробности и реальные воспроизведения — в отчётах Re-review. Более ранние статусы выше исторические. PROGRESS/release gates не повышались.

## Executor update — 2026-10-26

T21a attempt 3 завершён Codex heavy executor и передан в `review`: оставшиеся утечки карт рядом с суммой и телефона `00` на верхней границе исправлены. Проверки: PII 16/16, backend 152/152. Коммит невозможен из-за запрета записи `.git/index.lock`; файлы сохранены в рабочем дереве.

Re-review Git: commit not created; git add/commit failed with `.git/index.lock: Permission denied`. Review changes remain saved in the working tree.

## Review all pending — 2026-10-26

Проверены все задачи со статусом review: T21b → done, T24a → rework. Четыре воспроизводимых дефекта numeric verifier записаны в T24a. Backend 164/164, PII/tools 47/47, contract drift 0, schema 5/5. Offline evals 4/5: блокер T22 сохраняется. T22b выделена в BACKLOG с отдельным Scope chat.py + test_chat_tools.py, без ослабления evals. PROGRESS и release-readiness не пересчитывались: это ревью задач, не чекпоинт фазы.

Git persistence: review files saved in working tree. Targeted git add and git commit both failed: fatal: Unable to create .git/index.lock: Permission denied. No commit created; unrelated executor changes were not staged. git diff --check exited 0.
