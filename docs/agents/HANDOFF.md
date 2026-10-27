# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **Product plan:** [`PRODUCT_PLAN.md`](../../PRODUCT_PLAN.md) — читать перед выбором следующей задачи. Исходное видение сохранено в `docs/product/USER_VISION.md`. Планирование PLAN-01 завершено 2026-10-27; задачи реализации им не принимались.
- **После CHECKPOINT-2:** D2/T30 → T50 (контракт данных) → T31/T32; подробные зависимости T50–T63 в BACKLOG. T46 требует сквозной приёмки продукта, а не только старой инфраструктурной очереди.

- **Orchestrator:** Codex (GPT-6), review session 2026-10-26
- **Current phase:** 2 — Безопасность ИИ и приватность (Приоритет 2)
- **Current task:** T24b (review, GPT-6.1 Sol, attempt 2).
- **Last reviewed:** 2026-10-27, T24b REWORK; backend 205/205, targeted 54/54, offline 60/60, drift 0; 3 unsafe mocked replies accepted.
- **Next action:** Astra / Argon: `Проверь T24b` в отдельном чате; CHECKPOINT-2 после приёмки.
- **Git:** инициализирован (ветка main, теги `baseline`, `phase-0`, `phase-1`)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | Да (`provisional: true`) |
| D2 | БД/авторизация: (A) локальный Postgres в Docker, (B) Supabase cloud, (C) пока SQLite + Alembic | T30 | — |
| D3 | Есть ли Android-эмулятор / iOS-симулятор / устройство для Maestro? | T42 | — |
| D4 | Кто проверит финансовый контент уроков (человек)? | T17/T18 | — |

Дополнительные решения из PRODUCT_PLAN §7: **D5** — хранение оригиналов и сроки удаления/backup (до T34/T62); **D6** — страна/язык первого пилота (до T61/T63); **D7** — бюджет ИИ и критерии пилота (до T63). Открыты; не блокируют текущее ревью T24b. Подготовить конкретные варианты перед началом зависимой задачи, не выбирать автоматически.

Актуальные доказательства: T24b attempt 2 — **review**, 209 backend / 58 targeted / 60 offline указаны исполнителем; последнее независимое ревью — **REWORK**, 205 / 54 / 60. Старые записи и phase-log ниже исторические; закрытие фазы 2 требует нового ревью и CHECKPOINT-2.

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

## T22 re-review — 2026-10-26

T22 Attempt 3 → rework. CLI 5/5 и 25/25 harness зелёные, backend 166/166, drift 0. Независимые негативные пробы показали ложный PASS на нераспознанных денежный суммах и изменении due обязательства без revision. Замечания и реальные результаты сохранены в reports/T22.md; T23 не запускать до приёмки T22. T22b этим решением не принята. Код приложения при ревью не менялся.

Git persistence (T22 review): targeted git add and git commit failed with `.git/index.lock: Permission denied`. No commit created; review documentation remains saved in the working tree.

## Remaining phase 2 review — 2026-10-26

Проверка текущего дерева, без исправлений исходников.

- Backend: scripts/check.py, 166 tests in 7.989s, OK, exit 0.
- Schema: evals/run.py --offline --validate-only, 5/5 PASS, exit 0.
- Offline: evals/run.py --offline, 5/5 PASS in 0.034s, exit 0.
- Contracts: scripts/generate-contracts.py --check, Contract check passed., exit 0.
- Обычный exec не запустился из-за helper_sandbox_lock_failed; проверки выполнены через Node child_process и C:/Python314/python.exe с добавлением существующего C:/Users/sanat/AppData/Roaming/Python/Python314/site-packages в sys.path. Первоначальный запуск без этого пути дал ModuleNotFoundError: pydantic; зависимости не устанавливались.

| Task | Verdict | Evidence / remaining work |
|---|---|---|
| T22 | REWORK confirmed | check_numeric_grounding с {10000}: EUR 999.00 и €999.9 проходят; изменение due обязательства на 100 дней не замечается. Исправить два замечания последнего ревью. |
| T22b | REWORK: tests missing | 8 независимых fallback-проб прошли: crypto/tax/legal/budget при выключенном Gemini и mock AIUnavailable; source=local, state неизменен. В test_chat_tools.py нет тестов chat/fallback/AIUnavailable/ENABLE_GEMINI, обязательных по задаче. Добавить регрессии и отдельный отчёт. |
| T23 | Not implemented (todo) | 3 dev + 2 heldout JSON, всего 5; нужно >=60 уникальных family. |
| T24a | REWORK confirmed | €1 100 подтверждается 100 центами; 1.5 cents подтверждается 1 центом; 18.504% подтверждается 1850 bps; корректное €1.234.567 отклоняется при 123456700 центах. Все четыре прежних замечания воспроизведены. |
| T24b | Not implemented (todo) | В chat.py отсутствуют collect_all_tool_outputs и verify_reply_numbers; нет отклонения/повтора небезопасного ответа и 20-секундного общего лимита. |

Фаза 2 не закрыта. Порядок: исправить T22 и T24a, добавить тесты T22b; затем T23 и T24b. Зелёные 5 сценариев не подтверждают безопасность грейдеров и интеграции. Релизные гейты не повышались.

## Fresh T22/T24 review — 2026-10-26

Повторное независимое ревью текущего дерева: T22 REWORK (2 прежних блокера), T24a REWORK (4 прежних дефекта); все негативные примеры снова воспроизведены. T24b не реализована, остаётся todo. Подробности и фактический вывод проверок добавлены в reports/T22.md и reports/T24a.md. Backend 166/166, tools+harness 52/52, schema/offline 5/5, drift 0. Следующая команда для Astra GPT 6 / Argon: `Выполни T22`, затем отдельное ревью; далее T24a. T22b сохраняет прежний rework из-за отсутствия обязательных fallback-тестов. Фаза 2 не закрыта; релизные гейты не повышались.

Коммит этого ревью включает только документы ревью и eval-отчёт. Незакоммиченные изменения исполнителей в исходниках сохранены отдельно в рабочем дереве.

## Причины повторного REWORK — 2026-10-26

Диагностика по запросу пользователя, без изменения исходников:
- T22: распознавание суммы и проверка разделены так, что нераспознанная денежная запись исчезает из проверки; пустой список трактуется как успех. Сравнение состояния вручную перечисляет только часть полей вложенных моделей.
- T24a: regex может захватывать только часть суммы, остаток попадает в whitelist обычных чисел; парсер cents усекает дробь, парсер процентов округляет. Целочисленная арифметика сама по себе не обеспечивает точность исходного значения.
- Тесты покрывают конкретные прошлые примеры, но не полный класс вариантов формата/точности и изменений вложенных финансовых полей. Два самостоятельных парсера (evals и tools) имеют разные правила; это увеличивает риск расхождения, но объединять их без изменения Scope не следует.
- Последнее ревью повторно обнаружило те же незакрытые замечания; это не доказательство появления новых регрессий после исправления. T24b ещё todo и блокируется зависимостями.
- Следующий executor должен сначала добавить падающие тесты на ВСЕ открытые замечания своей задачи, затем исправить механизм и проверить соседние варианты (знаки, валютный префикс/суффикс, разделители, точность). После этого отдельное ревью. T22 и T24a выполнять раздельно по протоколу.
- Для устранения подтверждённых дефектов пользовательские финансовые решения/новые доступы не нужны. Неоднозначные и неподдержанные денежные записи безопасно отклонять вместо угадывания или округления. Расширение поддерживаемых форматов при необходимости фиксировать отдельно.

## T22 executor — Attempt 4 (2026-10-26)

Оба блокера исправлены: строгий парсинг полных денежных токенов с отказом на ошибочном формате; сравнение полного State. Harness 29/29, backend 170/170, schema/offline 5/5, contract drift 0. T22 → review. Подробности в reports/T22.md. Предшествующие изменения сохранены отдельно в 213f534.

## T22 Attempt 4 review — 2026-10-26

REWORK: прежние конкретные примеры исправлены, полное сравнение State принято. Один оставшийся P1: €.99 / .99 EUR / EUR999.00 исчезают из проверки, €1e3 обрезается до €1; с allowed={100} numeric grader и grade_scenario возвращают PASS. Детали в reports/T22.md. Backend 170/170, harness 29/29, schema/offline 5/5, drift 0. Следующая задача — доработка T22; остальные статусы не повышались.

## T24a executor — Attempt 4 (2026-10-26)

Current task: T24a (in_progress, Codex GPT-6), parallel to the existing T22 execution. Fix the four numeric-verification review findings; T24b remains pending dependencies.

## T24a executor completion — Attempt 4 (2026-10-26)

Current task: T24a (review, Codex GPT-6). Four numeric-verifier findings fixed; 32/32 tools tests, 180/180 backend tests, git diff --check exit 0. Report: docs/agents/reports/T24a.md. Next action: Оркестратор: `Проверь T24a` в отдельном чате. Existing T22 execution preserved; T24b still awaits dependencies.

## T22 full rework — Attempt 5, 2026-10-26

Исправлено распознавание полного денежного выражения; добавлены проверки всех маркеров валюты, строгая предвалидация каждого прогона, отказ на пустом наборе и ошибках доменных данных, отчёт FAIL при исключении чата, проверка исчезновения State. Harness 37/37, backend 183/183, schema/offline 5/5, drift 0. Во время выполнения другой чат создал 0211175 и 236a0a4 (T24a) и включил часть промежуточных изменений T22; история сохранена. Ревью T22 следует читать относительно 903b56f по файлам T22, а не только последний коммит.

## Review T22 / T24a — 2026-10-26

T22 attempt 5 ACCEPT; T23 dependency unblocked. Non-blocking Markdown false rejection documented in report. T24a attempt 4 REWORK: all four earlier defects fixed, but €1k / €1/2 / €1’000 still approved by balance_cents=100. Needs complete-token rejection instead of prefix approval. Backend 183/183; harness+tools 69/69; schema/offline 5/5; drift 0. T22b remains rework and is next by backlog order. Phase 2 not complete; release gates unchanged. No source edits in this review.

## T24a redo — Attempt 5, 2026-10-26

Current task: T24a (in_progress, Codex GPT-6). Address independent review of partial-token approval; keep T22 accepted and unchanged.

## T24a redo completed — Attempt 5, 2026-10-26

Current task: T24a (review, Codex GPT-6). Closed remaining P1 from Review Attempt 4: unsupported continuations are captured and rejected as complete claims. Tools 34/34; backend 185/185; diff check exit 0. Next action: Оркестратор: `Проверь T24a` в отдельном чате. T22 status and implementation preserved; T24b still awaits dependencies.

## T24a Attempt 5 review — 2026-10-26

REWORK: prior suffix/fraction/apostrophe bypasses fixed; malformed repeated separators and internal * can still escape currency matching into plain-number whitelist. Five probes reproduced with balance_cents=100; details in reports/T24a.md. Backend 185/185, tools 34/34. T24b remains todo, integration absent. Sources unchanged during review. Backlog next task remains T22b; T24a rework can be assigned separately.

## T24a executor — Attempt 6, 2026-10-26

Исправлен оставшийся P1 Attempt 5: повторные разделители и операторы внутри денежного/процентного выражения захватываются целиком и отклоняются строгим парсером. Добавлены 48 отрицательных случаев и 11 положительных контролей пунктуации/Markdown. Tools 36/36, backend 187/187, git diff --check exit 0. T24a → review; независимое ревью в новом чате.

## T24a Attempt 6 review — 2026-10-26

ACCEPT, commit reviewed 3ab98f6. Remaining malformed separator/operator finding closed. Backend 187/187; tools 36/36; independent 11 negative probes rejected and 4 exact-value controls passed with adjacent-cent rejection. Detailed evidence in reports/T24a.md. T24a done; T24b still todo pending T23. Next by backlog order T22b. No application source changes during review; release gates unchanged.

## Выбор моделей с приоритетом экономии — 2026-10-26

Прямая инструкция пользователя: учитывать доступные в Codex модели и экономить. На присланном скриншоте доступны GPT-6.1 Sol, GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-5.6 Luna. Gemini/Claude остаются вариантами вне этого списка, если доступны пользователю; не считать их исчезнувшими.

Рабочая рекомендация для проекта (не утверждение о списании квоты конкретного тарифа):
- GPT-6 Luna: чётко заданные JSON-сценарии, документация, небольшие автономные изменения и тесты по готовым требованиям. Не принимать собственную работу и не выполнять роль оркестратора.
- GPT-6.1 Sol: основной исполнитель для обычного кода, регрессий и интеграции; начать с medium, повышать сложность рассуждения при необходимости.
- GPT-6 Astra / Argon: оркестрация по действующему протоколу, независимое ревью безопасности/финансов, сложные неясные ошибки и эскалации. Не тратить на рутинные правки.
- GPT-6 Sol и GPT-5.6 Sol/Terra/Luna: резерв при недоступности основной модели или подтверждённо более выгодных условиях аккаунта; не выбирать старую версию только по возрасту.
- После двух неуспешных попыток лёгкой модели передавать Sol/Astra с конкретными падающими тестами. Не повторять полное ревью неизменённого кода; обязательные Verify/DoD сохраняются. Одна задача на чат; самостоятельное переключение текущего чата не выполнялось.

Ближайшие назначения: T22b → GPT-6.1 Sol; T23 → GPT-6 Luna; T24b → GPT-6.1 Sol с независимым ревью Astra/Argon. Назначения исполнителей уточняют старые поля Model по прямому запросу пользователя, требования приёмки не ослабляются.

Источник общих характеристик: https://developers.openai.com/api/docs/models (проверено 2026-10-26): Sol — баланс качества/стоимости, Luna — экономичные узкие задачи, Astra — сложные задачи. API-цены не используются как доказательство расхода лимитов Codex на пользовательском тарифе.

## T22b review — 2026-10-26

ACCEPT (c8e6d25): обязательное покрытие fallback добавлено; disabled/AIUnavailable, отказы, бюджет, последнее сообщение, неизменность состояния и PII проверены. Backend 191/191; targeted 40/40; schema/offline 5/5; независимые бюджетные эталоны 2/2. Следующее: GPT-6 Luna → Выполни T23. Релизные гейты не повышались.

## T23 review — 2026-10-26

REWORK despite formal 60/60 PASS: task-specific oracles and meaningful financial topic coverage insufficient; 10 heldout prompts repeat dev. Details/evidence in reports/T23.md. Backend 191/191. Next GPT-6.1 Sol → Выполни T23, to redesign fixtures/expectations rather than extend templates mechanically. No app/scenario changes in review; T24b not unblocked.

## T23 re-review — 2026-10-26

ACCEPT: scenario redesign 30c26de + app-gap fixes 4aa01be. Prior weak-oracle, fixture and heldout duplication findings closed; bare Cash passes 0/55 new cases, exact prompt overlap 0. All original failing app-gap inputs retained. Backend 196/196, targeted 45/45, schema/offline 60/60, drift 0. T24b unblocked → GPT-6.1 Sol. Offline tests do not establish live-model safety; phase/release gates remain pending. Detailed evidence and heldout/phrase-matching limitations in reports/T23.md.

## T24b executor — 2026-10-27

T24b → review. Deterministic tools included in context; numeric and conservative scope validation; one corrective retry with a shared 20-second deadline; local fallback on rejection/unavailability/timeout. Quota reservations and PII masking preserved. Tools/chat 54/54, backend 205/205, offline evals 60/60, contracts generated and drift 0. See reports/T24b.md. Independent security review Astra/Argon required; no self-acceptance or phase checkpoint performed.

## T24b security review — 2026-10-27

REWORK f1dbc0f. Retry/deadline/quota/PII checks pass, but real-chat mocked outputs accept completed transfers and direct bond recommendation (3 independent probes). Two P1 findings in reports/T24b.md. Backend 205/205, targeted 54/54, offline 60/60, drift 0. No source edits; next GPT-6.1 Sol → Выполни T24b. Phase 2/release gates remain pending.

## T24b rework — Attempt 2, 2026-10-27

Оба P1 закрыты: отдельная выходная проверка завершённых финансовых действий и рекомендаций по bonds/securities/funds. Проверяются обе попытки; отрицания и нейтральные контроли покрыты тестами. Tools/chat 58/58, backend 209/209, offline 60/60, contracts generated/drift 0, diff check 0. T24b → review; независимое security-ревью Astra/Argon. Подробности в reports/T24b.md.
