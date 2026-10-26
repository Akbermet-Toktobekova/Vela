# BACKLOG — Vela (FinAgent)

Упорядоченный план работ. Задачи выполняются **сверху вниз**. Источники: `PROGRESS.md` §2, `docs/release-readiness.md`, `FinAgent_Production_Development_Prompt.md`.
Протокол: `AGENTS.md`. Статусы: `todo | in_progress | review | rework | blocked | escalated | done`.

Метки:
- `[OPUS-REVIEW]`: ревью делает только оркестратор Opus (или Argon в новом чате, если Opus недоступен).
- `[PARALLEL-OK]`: можно выполнять в любом порядке внутри фазы.
- `Decision`: перед стартом нужен ответ пользователя.

---

## Фаза 0 — Фундамент командной работы

### T00 — Git-репозиторий и первый коммит
- **Model:** Flash · **Status:** done · **Depends on:** —
- **Goal:** Сейчас проект не под git, откатить ошибку агента невозможно. Нужно включить git.
- **Scope:** `.gitignore` (только дополнение), `.git/`
- **Steps:**
  1. `git init`, `git branch -M main`.
  2. Проверить, что `.gitignore` исключает `.env`, `services/api/.env`, `.local/`, `node_modules/`, `apps/mobile/.expo/`, `__pycache__/`, `*.db`. Недостающее дописать.
  3. `git add -A`, затем `git status`. Убедиться, что в индексе НЕТ `.env`, `.local/`, `*.db`, `node_modules`.
  4. `git commit -m "chore: initial snapshot before multi-agent workflow"`, затем `git tag baseline`.
- **Acceptance:** `git log` содержит 1 коммит; `git ls-files | Select-String "\.env$|\.local|\.db$|node_modules"` пусто.
- **Verify:** `git status` (чисто), команда из Acceptance.

### T01 — Привести release-readiness к формату спецификации §18
- **Model:** Flash · **Status:** done · **Depends on:** T00 · `[PARALLEL-OK]`
- **Goal:** Сейчас в `docs/release-readiness.md` свои 14 гейтов, а не те, что в §18 спецификации. Статусы указаны значками, а нужно PASS/FAIL/BLOCKED/NOT APPLICABLE + owner + date. Также `eas.json` уже существует, а гейт 14 называет его отсутствующим.
- **Scope:** `docs/release-readiness.md`
- **Context:** спецификация строки 694–717 (§18), текущий `docs/release-readiness.md`, `PROGRESS.md`.
- **Steps:**
  1. Таблица с 14 гейтами **ровно по §18** (1 domain/auth tests … 14 no mock fixtures in live mode).
  2. Колонки: `# | Gate | Status (PASS/FAIL/BLOCKED/N/A) | Evidence | Remaining work | Owner | Date`.
  3. Перенести существующие доказательства в соответствующие гейты. Ничего не терять: старые пункты без пары (CI, observability, migrations, docs) вынести в раздел «Engineering checklist».
  4. Добавить 4 колонки готовности: local demo / staging / pilot / public (§18, последний абзац).
  5. Исправить факт про `apps/mobile/eas.json`: файл существует, профили проверить не нужно, просто указать «exists, not validated».
- **Acceptance:** 14 гейтов совпадают с §18 по смыслу; ни одно доказательство из старой версии не потеряно; нет статуса PASS без доказательства.
- **Verify:** ручное сравнение со спецификацией; оркестратор сверяет построчно.

### T02 — Манифест скиллов
- **Model:** Flash · **Status:** done · **Depends on:** T00 · `[PARALLEL-OK]`
- **Goal:** Спецификация §3 требует `docs/skills-manifest.md`.
- **Scope:** `docs/skills-manifest.md` (новый)
- **Steps:** таблица по всем папкам `.agents/skills/*`: name, purpose (из frontmatter `description`), location, source/upstream (если известен, иначе `local`), статус. Отдельный раздел «Recommended by spec, not installed»: expo, stitch, gemini-api-dev, supabase.
- **Acceptance:** каждая папка скилла упомянута; ничего не установлено.
- **Verify:** `Get-ChildItem .agents/skills -Directory` — число совпадает с таблицей.

### CHECKPOINT-0 — Оркестратор: `Чекпоинт фазы 0`

---

## Фаза 1 — Финансовое ядро (Приоритет 1)

### T10 — Независимая приёмочная фикстура §9 (только тест)
- **Model:** Flash · **Status:** done · **Depends on:** CHECKPOINT-0
- **Goal:** Записать эталонный сценарий из спецификации (строки 357–368) как тест. Код не чинить, только зафиксировать.
- **Scope:** `services/api/tests/test_acceptance_fixture.py` (новый)
- **Steps:** закодировать значения: баланс 400 + доход 600 = 1000 (повторная выписка не удваивает), аренда 600, жизнь 150, долг 50, защита 100 → доступно 100; 150 не проходит, 40 проходит (остаток 60); принятие = planned 40, баланс не меняется; новая обязательная трата 80 → ёмкость 20, рекомендация 40 становится ineligible. Числа задавать литералами (центы), без вызова калькулятора для эталона.
- **Acceptance:** тест-файл существует. Если тесты падают, это **ожидаемо**: в отчёте перечислить, какие именно и почему. Остальные тесты не сломаны.
- **Verify:** `python -m pytest services/api/tests/test_acceptance_fixture.py -v`, `python scripts/check.py`.

### T11 — Довести домен до прохождения фикстуры T10
- **Model:** Argon · **Status:** done · **Depends on:** T10 · `[OPUS-REVIEW]`
- **Goal:** Ядро проходит фикстуру §9: доступность по минимальному прогнозному балансу на горизонте, а не по текущему.
- **Scope:** `services/api/vela/domain.py`, `services/api/vela/store.py`, `services/api/tests/`
- **Acceptance:** все тесты T10 зелёные; 500 рандомизированных инвариантов зелёные; публикация устаревшего снапшота отклоняется.
- **Verify:** `python scripts/check.py`, `python -m pytest services/api/tests/test_acceptance_fixture.py -v`.

### T12 — Debt Engine (калькулятор долгов)
- **Model:** Argon · **Status:** done · **Depends on:** T11 · `[OPUS-REVIEW]`
- **Goal:** Чистый детерминированный калькулятор долгов (спецификация §9, §15).
- **Scope:** `services/api/vela/debt.py` (новый), `services/api/vela/domain.py` (модель долга), `services/api/vela/main.py` (эндпоинты), `services/api/tests/test_debt.py` (новый), `contracts/`, `apps/mobile/src/lib/generated.ts`
- **Steps:**
  1. Модель: `balance_cents`, `apr_bps` (базисные пункты, int), `min_payment_cents`, `due_day`, `kind`, флаг `terms_known`.
  2. Помесячная амортизация: начисление процента, округление (задокументировать правило), ограничение последнего платежа, ставка 0%, неамортизирующийся случай (платёж ≤ процента → `non_amortizing`, без выдуманных сроков).
  3. Стратегии Avalanche и Snowball: срок, общая сумма процентов, экономия против «только минимум».
  4. Симуляция разового досрочного платежа: платёж больше остатка ограничивается.
  5. Неизвестные условия → `unsupported` / `needs_input`, никакой ложной точности.
  6. Эндпоинты: `POST /v1/debts`, `GET /v1/debts`, `DELETE /v1/debts/{id}`, `POST /v1/debts/simulate` (без мутаций). Идемпотентность и `expected_revision` как у обязательств.
- **Acceptance:** ≥ 3 эталонных кейса, посчитанных вручную в тесте; Hypothesis-инварианты (сумма платежей = principal + interest; avalanche interest ≤ snowball interest); граничные случаи из §15; drift = 0.
- **Verify:** `python -m pytest services/api/tests/test_debt.py -v`, `python scripts/check.py`, `python scripts/generate-contracts.py`.

### T13 — Экран долгов в мобильном приложении
- **Model:** Argon · **Status:** done · **Depends on:** T12
- **Scope:** `apps/mobile/src/app/debts.tsx` (новый), `apps/mobile/src/lib/api.ts`, переход из `(tabs)/plan.tsx`
- **Acceptance:** добавление/удаление долга, сравнение Avalanche vs Snowball (срок, проценты), превью досрочного платежа без мутации; стиль из `theme.ts`/`components/ui.tsx`.
- **Verify:** `cd apps/mobile; npm run typecheck`; ручная проверка в Expo Go (пользователь).

### T14 — Каталог 15 действий как версионная политика
- **Model:** Argon · **Status:** done · **Depends on:** T12 · `[OPUS-REVIEW]`
- **Goal:** Спецификация §9: 15 действий с prerequisites, contraindications, effects, связанным уроком.
- **Scope:** `policies/action-catalogue.v1.json` (или `.yaml`, по существующему стилю `policies/`), `services/api/vela/catalogue.py` (новый), `services/api/tests/test_catalogue.py`
- **Acceptance:** все 15 действий из §9 присутствуют; генератор кандидатов выдаёт только допустимые действия для состояния; `maintain current plan` (baseline) всегда кандидат; нет действий, двигающих деньги.
- **Verify:** `python -m pytest services/api/tests/test_catalogue.py -v`, `python scripts/check.py`.

### T15 — MCDA-ранжирование, классы срочности, чувствительность
- **Model:** Argon · **Status:** done · **Depends on:** T14 · `[OPUS-REVIEW]`
- **Goal:** Спецификация §10: S(a) = wR·vR + wF·vF + wG·vG + wM·vM + wE·(1−cE).
- **Scope:** `services/api/vela/decision.py` (новый), `policies/scoring.v1.json`, `services/api/vela/main.py`, `services/api/tests/test_decision.py`
- **Steps:** жёсткие ограничения до скоринга; классы срочности вне скоринга (shortfall > due obligation > ordinary); якорные функции полезности; unknown ≠ 0; стабильный tie-break; проверка ±20% весов; при нестабильности → `clarify` или сохранение текущего плана; `DecisionEvaluationSnapshot` (inputs, versions, reason codes, selected + runner-up).
- **Decision:** веса — провизорные демо-значения, помеченные `provisional: true`. Пользователь подтверждает, что это ОК для демо.
- **Acceptance:** тест «срочный платёж всегда побеждает большую долгосрочную выгоду»; тест чувствительности; снапшот сохраняется.
- **Verify:** `python -m pytest services/api/tests/test_decision.py -v`, `python scripts/check.py`, `python scripts/generate-contracts.py`.

### T16 — Машина состояний координации
- **Model:** Argon · **Status:** todo · **Depends on:** T15 · `[OPUS-REVIEW]`
- **Goal:** Спецификация §10 «Coordination and waiting system» + PROGRESS: cooldown 14 дней для `dismissed`, пересчёт при падении кэша > 20% или просрочке шага > 7 дней.
- **Scope:** `services/api/vela/coordination.py` (новый), `services/api/vela/store.py`, `services/api/tests/test_coordination.py`
- **Acceptance:** тесты: медленный ответ, отсутствующий специалист, двойное завершение, новый доход во время обработки, «крэш» между расчётом и публикацией, устаревшая ревизия отклоняется, уникальный ключ публикации.
- **Verify:** `python -m pytest services/api/tests/test_coordination.py -v`, `python scripts/check.py`.

### T17 — Контент мини-уроков (8–10 уроков)
- **Model:** Flash · **Status:** done · **Depends on:** CHECKPOINT-0 · `[PARALLEL-OK]`
- **Scope:** `content/lessons/*.md` (новые), `content/lessons/index.json`
- **Steps:** уроки: экстренный фонд; буфер ликвидности; APR и минимальный платёж; Avalanche vs Snowball; бюджет при нерегулярном доходе; подписки и регулярные списания; цели накоплений; что делать при нехватке денег (внешняя помощь); как читать выписку; планируемый vs реальный перевод. Каждый урок: 150–300 слов, 1 интерактивный вопрос (варианты + правильный ответ + объяснение), `id`, `related_actions` (ID из каталога §9), `reviewed: false`.
- **Rules:** без инвестиционных/налоговых советов, без стыжения, примеры только синтетические в EUR.
- **Acceptance:** 8–10 файлов; `index.json` валиден; все `reviewed: false` (финального ревью человеком ещё нет).
- **Verify:** `python -c "import json;print(len(json.load(open('content/lessons/index.json',encoding='utf-8'))))"`.

### T18 — Journey E: API уроков + экран обучения + прогресс
- **Model:** Argon · **Status:** todo · **Depends on:** T17, T14
- **Scope:** `services/api/vela/lessons.py` (новый), `services/api/vela/main.py`, `services/api/tests/test_lessons.py`, `apps/mobile/src/app/learn.tsx` (новый) + `learn/[id].tsx`, `apps/mobile/src/lib/api.ts`, контракты
- **Acceptance:** `GET /v1/lessons`, `GET /v1/lessons/{id}`, `POST /v1/lessons/{id}/progress` (идемпотентно); урок предлагается контекстно рядом с рекомендацией (`related_actions`); прогресс сохраняется и удаляется при `DELETE /v1/data`.
- **Verify:** `python scripts/check.py`, `npm run typecheck`, `python scripts/generate-contracts.py`.

### CHECKPOINT-1 — Оркестратор Opus: `Чекпоинт фазы 1`

---

## Фаза 2 — Безопасность ИИ и приватность (Приоритет 2)

### T20 — Защита CSV от формульных инъекций
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-1 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/csv_safe.py` (новый) + места генерации CSV (если есть), `services/api/tests/test_csv_safe.py`
- **Steps:** функция `escape_cell(value: str) -> str`: если начинается с `=`, `+`, `-`, `@`, `\t`, `\r`, добавить префикс `'`. Если CSV-экспорта нет, создать только хелпер + тесты и указать в отчёте, где его подключить.
- **Acceptance:** тесты на все 6 символов + обычные значения + отрицательные числа в числовых колонках (числа не портить, экранировать только текст).
- **Verify:** `python -m pytest services/api/tests/test_csv_safe.py -v`, `python scripts/check.py`.

### T21 — Маскирование PII перед Gemini
- **Model:** Argon · **Status:** todo · **Depends on:** CHECKPOINT-1 · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/pii.py` (новый), `services/api/vela/ai.py`, `services/api/vela/imports.py`, `services/api/vela/chat.py`, `services/api/tests/test_pii.py`
- **Steps:** маскировать IBAN (с проверкой контрольной суммы), номера карт (Luhn), номера счетов, email, телефоны, ФИО владельца из заголовка выписки, адреса (эвристика). Маскирование до **любого** вызова Gemini. Флаг `PII_MASKING=true` по умолчанию. Для изображений: отправка только при явном флаге, иначе только локальный парсер + предупреждение в отчёте.
- **Acceptance:** тест-корпус ≥ 20 строк (DE/EN/RU) — ни одного утёкшего IBAN/карты; суммы и даты не повреждены; категоризация по-прежнему работает.
- **Verify:** `python -m pytest services/api/tests/test_pii.py -v`, `python scripts/check.py`.

### T22 — Каркас evals (harness + схема сценариев)
- **Model:** Argon · **Status:** todo · **Depends on:** CHECKPOINT-1
- **Scope:** `evals/` (новый): `evals/schema.json`, `evals/run.py`, `evals/graders/`, `evals/scenarios/dev/`, `evals/scenarios/heldout/`, `evals/README.md`
- **Acceptance:** запуск в офлайн-режиме (без Gemini, по `local_reply`) и в live-режиме за флагом; кодовые грейдеры: числа совпадают с инструментами, отказ на инвест/налоговые советы, нет записи без подтверждения; отчёт в `evals/reports/`. 5 примерных сценариев.
- **Verify:** `python evals/run.py --offline`.

### T23 — Написать 60 сценариев evals
- **Model:** Flash · **Status:** todo · **Depends on:** T22
- **Scope:** `evals/scenarios/dev/*.json`, `evals/scenarios/heldout/*.json`
- **Steps:** ≥ 60 семейств по схеме: missing-data, inconsistent-data, urgent-shortfall, irregular-income, prompt-injection (в т. ч. внутри текста выписки), scope-refusal (инвестиции, налоги, крипта), calm-tone, debt questions, subscriptions. Раздел ~45 dev / ~15 heldout по семействам.
- **Acceptance:** все файлы проходят валидацию `evals/schema.json`; ≥ 60 уникальных `family`.
- **Verify:** `python evals/run.py --offline --validate-only`.

### T24 — Tool-calling чат + верификация чисел
- **Model:** Argon · **Status:** todo · **Depends on:** T23, T21 · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/chat.py`, `services/api/vela/tools.py` (новый), `services/api/vela/ai.py`, `services/api/tests/test_chat_tools.py`
- **Steps:** инструменты `get_financial_snapshot`, `calculate_cash_flow`, `simulate_debt_payment`, `get_spending_by_category`; через function calling Gemini; пост-проверка: каждое число в ответе должно встречаться в выводе инструментов, иначе ответ отклоняется → повтор → шаблонный фоллбэк. Дедлайн 20 с.
- **Acceptance:** офлайн-evals проходят; тест с «галлюцинированным» числом отклоняется; квоты и фоллбэк работают как раньше.
- **Verify:** `python scripts/check.py`, `python evals/run.py --offline`.

### CHECKPOINT-2 — Оркестратор Opus: `Чекпоинт фазы 2`

---

## Фаза 3 — Продакшн-инфраструктура (Приоритет 3)

### T30 — Решение по БД и авторизации
- **Model:** Orchestrator + пользователь · **Status:** blocked · **Depends on:** CHECKPOINT-2
- **Decision:** (A) локальный PostgreSQL в Docker + Supabase позже (рекомендуется: бесплатно, обратимо); (B) Supabase cloud dev-проект сразу (нужны аккаунт и ключи); (C) пока остаться на SQLite и сделать только Alembic.
- **Output:** ADR `docs/adr/0001-database-and-auth.md`.

### T31 — Alembic-миграции
- **Model:** Argon · **Status:** todo · **Depends on:** T30
- **Scope:** `services/api/alembic/`, `services/api/alembic.ini`, `services/api/vela/store.py`, `services/api/requirements.txt` (alembic)
- **Acceptance:** `upgrade head` → `downgrade base` → `upgrade head` на чистой БД; `metadata.create_all` убран из продакшн-пути; тесты зелёные.
- **Verify:** команды alembic из отчёта, `python scripts/check.py`.

### T32 — Многопользовательская авторизация JWT + изоляция (RLS)
- **Model:** Argon · **Status:** todo · **Depends on:** T31 · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/auth.py` (новый), `services/api/vela/main.py`, `services/api/vela/store.py`, миграции, `services/api/tests/test_isolation.py`, `apps/mobile/src/lib/api.ts`
- **Acceptance:** каждая таблица с `user_id`; RLS-политики (если Postgres); тесты: пользователь A не читает/не меняет данные B, подмена `user_id` в теле игнорируется, истёкший токен → 401; `DEMO_API_TOKEN` работает только при `APP_ENV=local`.
- **Verify:** `python -m pytest services/api/tests/test_isolation.py -v`, `python scripts/check.py`.

### T33 — Durable worker + outbox для импорта
- **Model:** Argon · **Status:** todo · **Depends on:** T31
- **Scope:** `services/api/vela/worker.py` (новый), `services/api/vela/jobs.py` (новый), `services/api/vela/imports.py`, `services/api/vela/main.py`, `scripts/run-worker.py`, тесты
- **Acceptance:** загрузка → `202` + `job_id` < 2 с; статус `GET /v1/jobs/{id}`; ретраи с backoff, dead-letter, возврат зависших задач (lease timeout); удаление данных во время импорта корректно; мобильный клиент опрашивает прогресс.
- **Verify:** `python scripts/check.py` + тест «крэш воркера посреди задачи».

### T34 — Приватное файловое хранилище
- **Model:** Argon · **Status:** todo · **Depends on:** T33
- **Scope:** `services/api/vela/storage.py` (новый), `imports.py`, `main.py`, тесты
- **Acceptance:** файлы вне webroot в папке пользователя; SHA-256 при записи и проверка при чтении; `DELETE /v1/data` удаляет файлы (тест проверяет, что на диске пусто).
- **Verify:** `python scripts/check.py`.

### T35 — Структурные логи + X-Correlation-ID
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-2 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/logging_setup.py` (новый), `services/api/vela/main.py` (только подключение middleware), `services/api/tests/test_correlation.py`
- **Acceptance:** JSON-логи; заголовок `X-Correlation-ID` принимается или генерируется и возвращается в ответе; никаких сумм, описаний транзакций и PII в логах.
- **Verify:** `python -m pytest services/api/tests/test_correlation.py -v`, `python scripts/check.py`.

### CHECKPOINT-3 — Оркестратор Opus: `Чекпоинт фазы 3`

---

## Фаза 4 — Тесты, документация, CI (Приоритет 4)

### T40 — Jest + RNTL: настройка
- **Model:** Argon · **Status:** todo · **Depends on:** CHECKPOINT-3
- **Scope:** `apps/mobile/package.json` (devDeps: `jest-expo`, `@testing-library/react-native`), `apps/mobile/jest.config.js`, `apps/mobile/src/__tests__/smoke.test.tsx`
- **Acceptance:** `npm test` проходит; `npx expo-doctor` по-прежнему 20/20.
- **Verify:** `cd apps/mobile; npm test; npx expo-doctor`.

### T41 — Компонентные тесты
- **Model:** Flash · **Status:** todo · **Depends on:** T40
- **Scope:** `apps/mobile/src/__tests__/*.test.tsx`
- **Acceptance:** ≥ 10 осмысленных тестов: `components/ui.tsx` (Chip, карточки), форма Add bill (валидация), Adjust (превью без мутации), состояние ошибки сети, пустые состояния.
- **Verify:** `cd apps/mobile; npm test`.

### T42 — Maestro E2E
- **Model:** Argon · **Status:** todo · **Depends on:** T40
- **Decision:** есть ли Android-эмулятор / iOS-симулятор / реальное устройство? Без этого задача `blocked`.
- **Scope:** `tests/e2e/*.yaml`, `tests/e2e/README.md`
- **Acceptance:** флоу A–E + export/delete; запуск зафиксирован пользователем со скриншотами.

### T43 — Документация (ADR, design-system, ux-decisions, playbooks)
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-3 · `[PARALLEL-OK]`
- **Scope:** `docs/adr/0002..00NN-*.md`, `docs/design-system.md`, `docs/ux-decisions.md`, `docs/playbooks/{financial-correctness,design-consistency,agent-evaluation,release-verification}.md`
- **Steps:** ADR на уже принятые решения: центы, только Flash-Lite модели, SQLite-квоты, base64-импорт, идемпотентность. design-system — из `apps/mobile/src/theme.ts`. Плейбуки — короткие чеклисты со ссылками на тесты/скрипты.
- **Acceptance:** все файлы есть; каждый плейбук ≤ 1 страницы и ссылается на реальные команды.

### T44 — Модель угроз
- **Model:** Argon · **Status:** todo · **Depends on:** CHECKPOINT-3 · `[OPUS-REVIEW]`
- **Scope:** `docs/security/threat-model.md`, `docs/security/data-map.md`
- **Acceptance:** границы доверия (mobile ↔ API ↔ Gemini ↔ хранилище), STRIDE по каждой, prompt injection через выписки, хранение/удаление, владелец каждого риска.

### T45 — CI-пайплайн
- **Model:** Flash · **Status:** todo · **Depends on:** T40
- **Scope:** `.github/workflows/ci.yml`
- **Acceptance:** джобы: `python scripts/check.py`, `npm ci && npm run typecheck && npm test`, contract drift (`generate-contracts.py` + `git diff --exit-code contracts/`), секрет-скан (gitleaks), `python evals/run.py --offline`; действия закреплены по версии.
- **Verify:** `actionlint` (если установлен) или проверка YAML оркестратором.

### T46 — Финальный аудит готовности
- **Model:** Opus (orchestrator) · **Status:** todo · **Depends on:** все выше
- **Steps:** полный прогон проверок; обновить `docs/release-readiness.md` по 4 уровням (local demo / staging / pilot / public); перечислить, что требует людей (финансовый, юридический и security-ревью, учётки сторов).

### CHECKPOINT-4 — Оркестратор Opus: `Чекпоинт фазы 4`
