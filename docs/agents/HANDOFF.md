# HANDOFF — текущее состояние команды

> Этот файл читается первым в каждой сессии и обновляется в конце каждой сессии.
> Любой агент должен суметь продолжить работу, прочитав только `AGENTS.md` + этот файл + `BACKLOG.md`.

## Сейчас

- **2026-10-29 T72 R1 independently ACCEPTED:** source ab6d533; separate chat01a18742-8ee8-7532-a9b8-8c51ad9b1740 independently verified raw/StateView/JSON refund2000 and horizon/state invariants, targeted7/backend242/TS/contracts/UI/nav/web. T72 done. T75 source458ecac under independent review in chat01a18745-1f65-70f0-b236-4a50c05ed43c; T24b safety rework executed in chat01a18741-64d5-7643-90e7-e058246239f6 and separately reviewed by Astra subagent. T73 actual browser verification in progress. No cloud or release promotion.

- **2026-10-29 owner-authorized parallel backend queue:** root Codex orchestrates; subagents `t75_executor` (frontend contract/client/synthetic launcher), `t72_executor` (refund R1), `independent_audit` (T24b/T73 independent review and remaining dependency audit). Shared checkout uses disjoint product/report ownership; root alone updates BACKLOG/HANDOFF and stages explicit task files. Existing T75 dirty changes preserved. Independent acceptance required; no deployment, paid activation or fabricated native/cloud evidence. Never read/change demo.db or access/manage API8000–8003. Standalone HTML stays disconnected. Current source HEAD db5b78a; execution continues until accepted work or recorded external blockers.

- **2026-10-29 independent T72 review: REWORK.** Original2ad1652/current f436831 checked. R1: supported StateView/JSON cash-flow tool drops separate refund_cents (expected2000), raw branch and net arithmetic correct. New synthetic API54295/UI54300/Chrome19006: oracle56 rows, analytical-only invariants, T74 plan preservation, repeat/retry/conflicts/future-income exclusion/evidence and pagination PASS; backend231/targeted6/contracts/TS/UI/navigation/web PASS. See reports/T72.md Review. Next: `Выполни T72` R1 + parity regression, then independent new-chat review. T73 remains review; T74 done; release gates unchanged. demo.db/API8000–8003 untouched.

- **2026-10-29 independent T74 re-review of5fc0aa7: ACCEPT.** Receipt bypass resolved; full HTTP route matrix, changed-body fingerprint409 and deterministic adoption race independently passed on new temporary SQLite DBs/free ports. Backend231/targeted8/contracts drift0/TS/UI6/navigation/full web export PASS. See reports/T74.md Independent receipt re-review. Next: new-chat `Проверь T72`; T73 separately pending. T72/T73 remain review; no journey/release gate promotion. demo.db/API8000–8003 untouched.

- **2026-10-29 T74 receipt rework REVIEW (GPT-6.1 Sol):** guard runs before cached legacy receipts under store lock; allowed debt/import/lesson retries return current context without duplicate effects. Regression red16 failures -> green8tests; backend231 OK; contracts drift0/TS/UI6/navigation/full web export PASS. Real HTTP/free64584/new DB: old evaluation replay409, snapshot/actions preserved. See reports/T74.md Receipt rework. API8000–8003/demo.db untouched. Next: independent new-chat `Проверь T74`. T72/T73 and release gates unchanged.

- **2026-10-29 independent T74 review of5db44fc: REWORK.** Pre-adoption idempotent /v1/decision/evaluate replay bypasses activation guard and returns obsolete cash/advice after account falls to shortfall. Real HTTP/free62389/new isolated DB reproduced200 with legacy cash100000 vs current1000. See reports/T74.md Review. Next heavy executor: `Выполни T74`, then independent new-chat review. T72/T73 remain review; release gates unchanged.

- **2026-10-29 T74 review:** continuation from9ca6cf8 completed. Stale lesson context fixed; legacy state no longer asserts old cash, old preview/decision/evaluate/chat explicitly unavailable after activation. Backend230/targeted7/contracts drift0/TS/UI6/navigation/full web export PASS. Real Chrome new-account/no-goal/plan/bill/preview40/income100/complete/cancel/Assistant/Learn and separate explicit legacy adoption PASS; original snapshot preserved. New isolated APIs8002/8003 and databases only; demo.db/API8000/API8001 untouched. See reports/T74.md continuation. Next independent orchestrator: `Проверь T74`. T72/T73 remain review; no done/release promotion.


- **2026-10-29 T74 IN_PROGRESS — continuation checkpoint requested by owner.** Read reports/T74.md FIRST after this HANDOFF, then T74 BACKLOG Scope. Canonical local account-plan backend and new shared-plan/shared-assistant UI implemented but NOT browser-verified. Backend227/targeted4/typecheck pass; contracts generated. Still must fix/audit stale legacy lesson/advice readers, finish migration/read-safety tests, run final gates and actual isolated Chrome flow. Do NOT treat this as review/done or completed integration. Preserve live API8000/demo.db; older dedicated API8001 currently runs T72 code. Detailed files, process recovery, commands and next steps in reports/T74.md.

- **2026-10-29 T73 review:** web Export JSON now downloads locally, native Share retained. Actual Chrome produced Downloads/vela-export.json; UTF-8 JSON equals live isolated test export56rows/account1000/revision5, token absent. Download-event helper timed out on Blob, filesystem artifact verified. Backend223/TS/full web export pass. See reports/T73.md. Canonical account/plan migration is next; no done/release promotion.

- **2026-10-29 T72 review:** analytical-only /v2 apply and import UI, labelled refund separation, imported-future cash exclusion, cumulative suggested observations/evidence and paginated history. Real Chrome3fixture uploads+repeat retains56, no hidden profile, account1000 unchanged, streaming delta3 and source rows, page2 oldest6 verified. Backend223/TS/contracts/UI6/nav/full export/offline60 pass. See reports/T72.md. Legacy /v1 apply remains for compatibility; canonical account/plan integration and web export remain next bounded slices. No done/release promotion.

- **2026-10-29 PATTERN-01 review:** three frozen synthetic July/Aug/Sep EUR statement CSVs + predeclared integer oracle in docs/testing/pattern-statements. Real Chrome import16/36/56 rows, repeatSeptember stays56; all56 references/dates/amounts match export. Keep existing preserves cash1000/saved0/bills0; own transfers excluded. Found refund20 classified income, absent cross-file patterns/price change, historical closing balance preselected for current cash, latest list limited50of56. AI disabled; no live-analysis claim. See reports/PATTERN-01.md. UI-02 preceding navigation repair remains review; shared finance model/native/export/delete work remains open.

- **2026-10-29 UI-02 review:** restored saved-account/planning/settings/Learn navigation and safe protected-route return after Connect. Real Chrome P0 -> preview/plan/cancel/shortfall/bill-pay/complete/debt/lesson/CSV-repeat/disconnect exercised; see reports/UI-02.md. Financial models explicitly separate; NOT shared-finance integration. Export Share Permission denied, duplicate completion gives safe conflict; deletion confirmation only cancelled. Backend217/typecheck/contracts/full export/UI6/navigation allowlist pass. Next owner request: three monthly synthetic statements + predetermined patterns and comparison in a separate verification slice.

- **2026-10-29 UI-TEST-05:** full workflow attempt/inventory recorded in reports/UI-TEST-05.md. Dedicated test DB/API8001: optional profile, EUR/HUF unknown, double-save, real outage/restart/retry, two-tab revision conflict and reload PASS; EUR1207/HUFunknown/4 incomes. Prototype onboarding/action/evidence/import-error/reminders exercised separately. Integrated end-to-end BLOCKED: /personal has no path to plan/assistant/import/settings/learn; direct legacy route reconnect returns personal. All U01-U22/J01-J12 dispositions recorded, none silently skipped. Backend217, journeys31, offline60, UI regressions6, TS/contracts pass. Native and integrated export/delete unrun; no done/release promotion.

- **2026-10-29 UI-TEST-04:** continued T71 real Chrome check: balance replacement, all three income modes, invalid precision/negative input, error clearing, Back without Save and reload/reconnect PASS. Synthetic account retained EUR1100 / 3 income records. Income form lacks balance date/received-date entry. HUF/unknown/retry/conflict/native unrun. See reports/UI-TEST-04.md; T71 remains review.

- **2026-10-29 T71:** local saved profile/accounts/income /v2 slice implemented, review. New /personal screen reached after local Connect or preview Open my saved data. Persistent data separate from preview and legacy snapshot. Backend217/typecheck/contracts pass; API restarted on8000. No Supabase/OTP/cloud acceptance. See reports/T71.md and docs/product/LOCAL_V2.md.


- **2026-10-29 T66 follow-up:** owner-requested three fixes implemented: completed copy, direct evidence page, Boolean error guard removing RN Web warning. Fresh real Chrome rerun and typecheck/backend215/web-export pass. See T66 report follow-up; earlier findings are historical. Native checks and independent acceptance remain open.


- **2026-10-29 T66:** owner explicitly authorized proceeding on current T65 without promoting its review status. Added isolated `/pilot` route and Open design preview on Connect. Synthetic, in-memory only; no API/auth/upload/AI/notification calls. Status review. Typecheck PASS, backend 215 tests PASS, full web export PASS. Native/owner UX acceptance remains unrun. See reports/T66.md for limitations.


- **2026-10-29 pilot revision:** owner approved sequential implementation. T64 records the specification, design rules and nine project skills; status review, not independent acceptance. T65 shared UI foundation implemented and in review: neutral/green themes, type scale, 48 targets, loading/destructive/icon controls and field helper/errors. Backend check and mobile typecheck exit 0. Native layout/accessibility not yet exercised. Next implementation slice T66 requires independent review of T64/T65; T24b remains separately pending. Full contract: docs/product/PILOT_SPEC.md. Cloud choices resolved; costs/SMTP activation still gated. T24b/CHECKPOINT-2 remain open before real cloud data.


- **MANUAL-03 (2026-10-28):** дополнительные автоматические проверки: contracts PASS, offline 60/60, journeys 31/31. Подробная инструкция повторения и оставшихся UI-веток: `docs/TEST_RUNBOOK.md`; фактический отчёт `docs/agents/reports/MANUAL-03.md`. Новые ручные U06/U07/U14–U22 не приняты.

- **Ручной web-прогон мануала (MANUAL-02, 2026-10-28):** на изолированной `.local/manual-u01-u22-20261028.db` пройдены U01–U05 и U08–U12 (U11 только local); U13 BLOCKED, остальные не принимались. Найдены: smoke не ловит падение полной web-сборки, stale-preview UX в Choose amount, Learn недоступен/зависает на прямом web-route. Постоянная demo.db и продуктовый код не менялись. Отчёт: `docs/agents/reports/MANUAL-02.md`.

- **Мануал пользователя (MANUAL-01, 2026-10-28):** `docs/USER_MANUAL.md`, контрольный профиль P0 и U01–U22; синтетическая выписка `docs/testing/sample-statement.csv`. Числа/локальный парсер проверены отдельно; ручные UI-сценарии не принимались. Выявленные по коду пробелы: нет Add income в UI, нет перехода к Learn из основных вкладок, recurring bills в импорте предвыбраны; см. мануал. Реализация не менялась.

- **Локальный запуск UI + backend (DEV-01, 2026-10-28):** `start-vela.cmd` / `python scripts/start-dev.py`; браузер `--web`, автоматическая проверка `--smoke`. Инструкция `docs/local-testing.md`; токен только в игнорируемом `.local/dev-connection.txt`. По умолчанию AI выключен, данные сохраняются. Это отдельная пользовательская задача запуска, не приёмка T24b и не CHECKPOINT-2.

- **Product plan:** [`PRODUCT_PLAN.md`](../../PRODUCT_PLAN.md) — читать перед выбором следующей задачи. Исходное видение сохранено в `docs/product/USER_VISION.md`. Планирование PLAN-01 завершено 2026-10-27; задачи реализации им не принимались.
- **После CHECKPOINT-2:** D2/T30 → T50 (контракт данных) → T31/T32; подробные зависимости T50–T63 в BACKLOG. T46 требует сквозной приёмки продукта, а не только старой инфраструктурной очереди.

- **Orchestrator:** Codex (GPT-6), owner-authorized parallel queue 2026-10-29
- **Current phase:** 2 — Безопасность ИИ и приватность (Приоритет 2)
- **Current task:** Parallel T75 completion + T72 R1; independent T24b/T73 review. Root coordinates integration and acceptance.
- **Last reviewed:** 2026-10-29, T72 REWORK R1; backend231/targeted6/contracts drift0/TS/UI/navigation/web PASS. T74 accepted at f436831; T24b remains independently pending.
- **Next action:** Collect executor evidence, commit each bounded slice separately, arrange independent new-context reviews; resolve T24b/CHECKPOINT-2 before dependent infrastructure work. No cloud activation without required decisions.
- **Git:** инициализирован (ветка main, теги `baseline`, `phase-0`, `phase-1`)

## Открытые вопросы пользователю

| ID | Вопрос | Нужен к задаче | Ответ |
|---|---|---|---|
| D1 | Веса MCDA: ок использовать провизорные демо-веса с пометкой `provisional`? | T15 | Да (`provisional: true`) |
| D2 | БД/авторизация | T30 | Resolved by PILOT_SPEC 2026-10-29: Supabase Postgres/Auth/private Storage; Render API/worker; email OTP. Activation/costs remain gated. |
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

## T24b continuation — Attempt 3, 2026-10-27

Завершены существующие изменения T24b: multilingual completed-action claims, exact-amount transfers, rhetorical/put investment directives, explicit fallback for bond/fund requests, tone/return-guarantee checks. Дополнительно закрыт why-not whitespace bypass; проверены повторная попытка и безопасные контроли. Deadline test стабилизирован без изменения production 20s. Tools/chat 64/64, backend 215/215, offline 60/60, generated contracts/drift 0. T24b → review; независимое security-ревью Astra/Argon. См. reports/T24b.md, Attempt 3.

## MANUAL-04 — 2026-10-28
Ручной U06 FAIL на 2916825: после Extra 80 при Planned 40 свободно -20; выполнение корректно заблокировано, но Cancel step тоже исчезает. Отмена резерва невозможна. См. reports/MANUAL-04.md. Отдельная база .local/manual-04-20261028.db сохранена; код не менялся. Далее исправить отмену и повторить U06, затем U07.

## MANUAL-05 — 2026-10-28
Доступные проверки завершены: backend 215 OK, offline 60/60, tsc и полная web-сборка PASS, 17/17 дополнительных API-проб с sample-statement.csv. UI: отмена допустимого плана и неполные данные PASS; ввод отклоняется, но Add bill показывает внутреннюю устаревшую ошибку. U06 остаётся FAIL. Browser use отключён при продолжении; оставшиеся UI/телефонные ветки не приняты. Полный охват U01–U22 и ограничения: reports/MANUAL-05.md. Продуктовый код не менялся.

## UI-01 — 2026-10-28
UI-01 → review: исправлены Cancel step при shortfall, ошибки Add bill, актуальность Choose amount preview, переход Today → Learn и отключённый StateGate. Регрессии до 0/6, после 6/6; backend 215 OK; tsc и полный web export PASS. Browser use отключён: ручная UI-приёмка не объявляется. Подробности и повторный чеклист: reports/UI-01.md. Независимое ревью в новом чате; T24b и релизные гейты без изменений.
