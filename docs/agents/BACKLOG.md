> **2026-10-29 approved pilot:** docs/product/PILOT_SPEC.md is the revised behaviour contract. Existing done statuses are historical module acceptance. T30 decision resolved: Supabase Postgres/Auth/private Storage + Render API/worker, email OTP; paid activation awaits estimate. D5: originals expire 30 days after upload. T50 must separate analytics from finances and specify /v2 EUR/HUF migration. T53 import cannot change finances. T52 onboarding precedes optional statements.

# BACKLOG — Vela (FinAgent)

Упорядоченный план работ. Сначала независимое ревью готовых задач, затем первая задача с выполненными **Depends on** и закрытыми обязательными Decision; номер не заменяет зависимости. Общая картина: [`PRODUCT_PLAN.md`](../../PRODUCT_PLAN.md), исходное видение: [`USER_VISION.md`](../product/USER_VISION.md). Источники: `PROGRESS.md` §2, `docs/release-readiness.md`, `FinAgent_Production_Development_Prompt.md`.
Протокол: `AGENTS.md`. Статусы: `todo | in_progress | review | rework | blocked | escalated | done`.

Метки:
- `[OPUS-REVIEW]`: ревью делает только оркестратор Opus (или Argon в новом чате, если Opus недоступен).
- `[PARALLEL-OK]`: можно выполнять в любом порядке внутри фазы.
- `Decision`: перед стартом нужен ответ пользователя.

---

## Фаза 0 — Фундамент командной работы

### DEV-01 — Один запуск локального API и Expo
- **Model:** Codex · **Status:** review · **Depends on:** — (пользовательская проверка существующего прототипа, разрешена до CHECKPOINT-2)
- **Scope:** `scripts/start-dev.py`, `start-vela.cmd`, `docs/local-testing.md`; навигационные ссылки `PRODUCT_PLAN.md`, `docs/agents/HANDOFF.md`; эта карточка и `docs/agents/reports/DEV-01.md`.
- **Goal:** запускать backend и Expo одной командой для проверки на телефоне/в браузере; дать агенту диагностический режим без оставленных процессов.
- **Acceptance:** существующие настройки/данные сохраняются; авторизованный API проверен до Expo; QR для Expo Go и web-режим; токен не в bundle/выводе агента; занятые порты не присваиваются; Ctrl+C/smoke останавливают только запущенные процессы; инструкция для пользователя и агента.
- **Verify:** `python scripts/start-dev.py --check`, `python scripts/start-dev.py --smoke`, повторный `--check` после smoke; отказ при занятом порте; `python scripts/check.py`; ручной запуск Expo. Полный пользовательский E2E и совместимость физического телефона фиксируются отдельно.

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
- **Model:** Argon · **Status:** done · **Depends on:** T15 · `[OPUS-REVIEW]`
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
- **Model:** Argon · **Status:** done · **Depends on:** T17, T14
- **Scope:** `services/api/vela/lessons.py` (новый), `services/api/vela/main.py`, `services/api/tests/test_lessons.py`, `apps/mobile/src/app/learn.tsx` (новый) + `learn/[id].tsx`, `apps/mobile/src/lib/api.ts`, контракты
- **Acceptance:** `GET /v1/lessons`, `GET /v1/lessons/{id}`, `POST /v1/lessons/{id}/progress` (идемпотентно); урок предлагается контекстно рядом с рекомендацией (`related_actions`); прогресс сохраняется и удаляется при `DELETE /v1/data`.
- **Verify:** `python scripts/check.py`, `npm run typecheck`, `python scripts/generate-contracts.py`.

### CHECKPOINT-1 — Оркестратор Opus: `Чекпоинт фазы 1`

---

## Фаза 2 — Безопасность ИИ и приватность (Приоритет 2)

### T20 — Защита CSV от формульных инъекций
- **Model:** Flash · **Status:** done · **Depends on:** CHECKPOINT-1 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/csv_safe.py` (новый) + места генерации CSV (если есть), `services/api/tests/test_csv_safe.py` (новый)
- **Steps:**
  1. Создать `services/api/vela/csv_safe.py` с функцией `escape_cell(value: object) -> str` (и `escape_row(row: Sequence[object]) -> list[str]`): если строковое значение начинается с `=`, `+`, `-`, `@`, `\t`, `\r`, но НЕ является чистым отрицательным/положительным числом (например `-42`, `-19.99`, `+100` в числовом виде или `int`/`float`), добавить префикс `'`. Если передана строка с формулой вида `=SUM(A1:A2)`, `+cmd|...`, `-2+3`, `@SUM(1)`, `\t=1`, `\r=1` — экранировать префиксом `'`.
  2. Так как CSV-экспорта в `main.py` сейчас нет (только JSON `/v1/export`), не трогать `main.py`, а в отчёте указать, где подключить `csv_safe`.
  3. Написать `services/api/tests/test_csv_safe.py` (`unittest.TestCase`).
- **Acceptance:** тесты на все 6 опасных префиксов (`=`, `+`, `-`, `@`, `\t`, `\r`) + обычные строки + отрицательные числа (`-150`, `-12.50`) не портятся.
- **Verify:** `python -m unittest services/api/tests/test_csv_safe.py -v`, `python scripts/check.py`.

### T21a — Автономный модуль маскирования PII (`pii.py` + тесты)
- **Model:** Argon · **Status:** done · **Depends on:** CHECKPOINT-1 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/pii.py` (новый), `services/api/tests/test_pii.py` (новый)
- **Steps:**
  1. Создать автономный модуль `services/api/vela/pii.py` (без изменения `ai.py`/`imports.py`/`chat.py`):
     - `is_pii_masking_enabled() -> bool`: читает `os.getenv("PII_MASKING", "true")`, по умолчанию `True`.
     - `mask_pii(text: str) -> str`: заменяет в тексте:
       - **IBAN** (2 буквы страны + 2 контрольные цифры + 11..30 алфавитно-цифровых символов, с пробелами или без, с проверкой контрольной суммы `mod 97 == 1`) → `[REDACTED_IBAN]`.
       - **Номера банковских карт** (13–19 цифр подряд или группами по 4 через пробел/дефис, проходящие проверку алгоритмом Луна / Luhn, и не являющиеся датами/суммами) → `[REDACTED_CARD]`.
       - **Email-адреса** → `[REDACTED_EMAIL]`.
       - **Телефоны** (международные форматы `+49...`, `+7...`, `+998...`, `0049...` от 9 до 15 цифр, не затрагивая даты `2026-03-15` и суммы `1200.50` / `-45,00 EUR`) → `[REDACTED_PHONE]`.
       - **Заголовки ФИО и адреса в шапке выписки** (строки с префиксами `Account holder:`, `Kontoinhaber:`, `Владелец счёта:`, `Address:`, `Adresse:`, `Адрес:`) → префикс + `[REDACTED_NAME]` / `[REDACTED_ADDRESS]`.
     - `mask_pii_lines(lines: list[str]) -> list[str]`: применяет `mask_pii` к списку строк.
  2. Создать `services/api/tests/test_pii.py` (`unittest.TestCase`) с корпусом ≥ 20 реалистичных строк выписок (DE/EN/RU): проверить, что ни один валидный IBAN, карта Luhn, email, телефон или `Kontoinhaber:` не остаётся в открытом виде, а даты (`2026-03-01`, `15.03.2026`), суммы (`-125,40 EUR`, `2400.00`) и названия мерчантов (`REWE Markt`, `Spotify`, `Netflix`) остаются неизменными.
- **Acceptance:** тест-корпус ≥ 20 строк (DE/EN/RU) — 0 утёкших IBAN/карт/email/телефонов; суммы, даты и мерчанты не повреждены.
- **Verify:** `python -m unittest services/api/tests/test_pii.py -v`, `python scripts/check.py`.

### T21b — Интеграция маскирования PII перед вызовами Gemini
- **Model:** Astra GPT 6 (или Argon) · **Status:** done · **Depends on:** T21a · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/ai.py`, `services/api/vela/imports.py`, `services/api/vela/chat.py`, `services/api/tests/test_pii.py`
- **Steps:**
  1. Подключить `mask_pii` из `services/api/vela/pii.py` перед **любым** текстовым вызовом Gemini в `ai.py`, `imports.py`, `chat.py` (если `is_pii_masking_enabled()` = `True`).
  2. Для мультимодальной отправки сырых изображений/PDF в `imports.py`: отправлять бинарник в Gemini только если явно задан `ALLOW_RAW_DOCUMENT_AI=true` (или когда маскирование отключено), иначе использовать локальный текстовый парсер (`pypdf` + `mask_pii` перед отправкой текста в ИИ) и записывать предупреждение.
  3. Дополнить `services/api/tests/test_pii.py` тестом, проверяющим через mock Gemini, что в промпт `ai.generate` уходит уже замаскированный текст без реального IBAN/карты, и категоризация продолжает работать.
- **Acceptance:** ни один вызов Gemini не получает необработанный IBAN/карту при `PII_MASKING=true`; категоризация и импорт работают; все тесты зелёные.
- **Verify:** `python -m unittest services/api/tests/test_pii.py -v`, `python scripts/check.py`.

### T22 — Каркас evals (harness + схема сценариев + 5 базовых сценариев)
- **Model:** Argon · **Status:** done · **Depends on:** CHECKPOINT-1 · `[PARALLEL-OK]`
- **Scope:** `evals/schema.json` (новый), `evals/run.py` (новый), `evals/graders/__init__.py` (новый), `evals/graders/checks.py` (новый), `evals/scenarios/dev/` (3 файла), `evals/scenarios/heldout/` (2 файла), `evals/README.md` (новый), `services/api/tests/test_evals_harness.py` (новый), `services/api/vela/chat.py` (детерминированный отказ в `local_reply`)
- **Steps:**
  1. Создать JSON-схему описания сценария `evals/schema.json` со следующими обязательными полями каждого сценария (`.json`):
     - `id` (str), `family` (str), `split` (`"dev"` | `"heldout"`), `category` (`"numeric_grounding"` | `"scope_refusal"` | `"prompt_injection"` | `"missing_data"` | `"calm_tone"` | `"no_unconfirmed_mutation"`), `user_message` (str), `state_overrides` (dict: `liquid_cash_cents`, `safe_buffer_cents`, `obligations`, `transactions`), `expected` (dict: `must_contain_any`: list[str], `must_not_contain`: list[str], `refuse_financial_advice`: bool, `allowed_numbers_only`: bool).
  2. Создать кодовые грейдеры в `evals/graders/checks.py`:
     - проверка отказа на инвестиционные/налоговые/крипто советы (например, при вопросе «купить акции/биткоин/как списать налоги» ассистент не даёт рекомендаций купить актив);
     - проверка отсутствия выдуманных чисел или запрещённых фраз (`must_not_contain`);
     - проверка спокойного нестыдящего тона и отсутствия несанкционированной мутации состояния.
  3. Создать `evals/run.py` с CLI-аргументами `--offline` (по умолчанию тестирует через детерминированный `local_reply` / `chat_reply` с отключённым внешним API) и `--validate-only` (проверяет все JSON в `evals/scenarios/dev/*.json` и `evals/scenarios/heldout/*.json` на соответствие `evals/schema.json` и уникальность `id`/`family`). Скрипт должен сохранять JSON-сводку в `evals/reports/latest.json` и возвращать код `0` при успехе.
  4. Создать 5 эталонных сценариев (3 в `evals/scenarios/dev/`, 2 в `evals/scenarios/heldout/`) и короткий тест `services/api/tests/test_evals_harness.py`.
- **Acceptance:** `python evals/run.py --offline` и `python evals/run.py --offline --validate-only` завершаются с кодом 0 (5/5 PASS); отчёт создаётся в `evals/reports/latest.json`.
- **Verify:** `python evals/run.py --offline`, `python evals/run.py --offline --validate-only`, `python scripts/check.py`.

### T22b — Исправить отказ в локальном chat fallback и разблокировать T22
- **Model:** GPT-6.1 Sol · **Status:** done · **Depends on:** T21b
- **Goal:** Устранить подтверждённый блокер T22 без ослабления сценариев; разорвать цикл T22 → T23 → T24b → T22.
- **Scope:** `services/api/vela/chat.py`, `services/api/tests/test_chat_tools.py`
- **Steps:** Передать последнее сообщение пользователя в детерминированный fallback; при запросах инвестиционных, налоговых, юридических и криптовалютных рекомендаций возвращать явный спокойный отказ и направление к квалифицированному специалисту. Сохранить текущие ответы по бюджету, отсутствие мутаций и маскирование T21b. Добавить тесты реального chat-пути при отключённом Gemini и AIUnavailable.
- **Acceptance:** `dev-scope-refusal-crypto` проходит без правок сценариев/грейдеров; все 5 offline evals PASS; backend зелёный. После этого T22 повторно передать оркестратору на ревью, не принимать автоматически.
- **Verify:** `python -m unittest services/api/tests/test_chat_tools.py -v`, `python scripts/check.py`, `python evals/run.py --offline --validate-only`, `python evals/run.py --offline`.

### T23 — Написать 60 сценариев evals
- **Model:** GPT-6.1 Sol · **Status:** done · **Depends on:** T22
- **Scope:** `evals/scenarios/dev/*.json`, `evals/scenarios/heldout/*.json`; `services/api/vela/chat.py`, `services/api/tests/test_chat_tools.py` (расширение явно разрешено пользователем 2026-10-26 для четырёх app-gap).
- **Steps:** довести общее число сценариев до ≥ 60 файлов (или ≥ 60 объектов сценариев с уникальным `family`) по схеме из T22: `missing-data`, `inconsistent-data`, `urgent-shortfall`, `irregular-income`, `prompt-injection` (в т. ч. внутри текста выписки), `scope-refusal` (инвестиции, налоги, крипта), `calm-tone`, `debt-questions`, `subscriptions`. Разбивка: ~45 в `dev/` и ~15 в `heldout/`.
- **Acceptance:** все сценарии проходят валидацию `evals/schema.json` и офлайн-прогон; ≥ 60 уникальных `family`.
- **Verify:** `python evals/run.py --offline --validate-only`, `python evals/run.py --offline`.

### T24a — Автономный модуль инструментов чата и верификации чисел (`tools.py` + тесты)
- **Model:** Argon · **Status:** done · **Depends on:** CHECKPOINT-1 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/tools.py` (новый), `services/api/tests/test_chat_tools.py` (новый)
- **Steps:**
  1. Создать `services/api/vela/tools.py` с 4 чистыми детерминированными функциями-инструментами, работающими поверх `State` / `StateView` и `debt.py`:
     - `get_financial_snapshot(state: State) -> dict` (баланс, буфер, доступно, обязательства на 30 дней, запланированный шаг в центах и отформатированных EUR);
     - `calculate_cash_flow(state: State, days: int = 30) -> dict` (доходы, расходы, чистый поток и минимальный прогнозный баланс в центах и EUR);
     - `simulate_debt_payment(state: State, extra_payment_cents: int = 0) -> dict` (сводка по долгам, Avalanche vs Snowball из `debt.py`);
     - `get_spending_by_category(state: State, limit: int = 5) -> dict` (топ категорий расходов и подписок за 30 дней).
  2. В `services/api/vela/tools.py` реализовать функцию пост-проверки чисел `verify_reply_numbers(reply_text: str, tool_outputs: dict) -> tuple[bool, list[str]]`: извлекает денежные суммы и проценты из текста ответа ИИ и проверяет, что каждое числовое значение присутствует среди чисел `tool_outputs` (в евро или центах, либо входит в белый список тривиальных констант вроде `30` дней / `14` дней / `1` шаг). Если в ответе есть «галлюцинированная» сумма, которой нет в `tool_outputs`, возвращает `(False, [список неподтверждённых чисел])`.
  3. Написать unit-тесты в `services/api/tests/test_chat_tools.py` (`unittest.TestCase`): проверка всех 4 инструментов на тестовом `State` и проверка, что `verify_reply_numbers` пропускает ответ с точными суммами из инструментов и отклоняет ответ с выдуманной суммой (например, `€999.00`).
- **Acceptance:** все 4 инструмента возвращают точные данные из домена; `verify_reply_numbers` надёжно ловит галлюцинированные суммы.
- **Verify:** `python -m unittest services/api/tests/test_chat_tools.py -v`, `python scripts/check.py`.

### T24b — Подключение tool-calling и верификации чисел в `chat.py` и `ai.py`
- **Model:** GPT-6.1 Sol (security review: Astra / Argon) · **Status:** done · **Depends on:** T24a, T23, T21b · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/chat.py`, `services/api/vela/ai.py`, `services/api/tests/test_chat_tools.py`
- **Steps:**
  1. В `chat.py` формировать контекст чата через вызов детерминированных инструментов из `tools.py` (`collect_all_tool_outputs(state)`) и проверять ответ модели через `verify_reply_numbers(reply, tool_outputs)` + проверку отказа на инвестиционные/налоговые советы.
  2. Если ответ Gemini содержит неподтверждённое число («галлюцинацию») или нарушает границы советов — отклонять ответ, делать максимум 1 повтор с жёстким напоминанием использовать только числа из инструментов, а при повторной неудаче или таймауте (> 20 с) возвращать детерминированный `local_reply`.
  3. Дополнить `services/api/tests/test_chat_tools.py` интеграционным тестом `chat_reply` с замоканным ответом Gemini, содержащим галлюцинированное число (проверить, что он отклоняется и срабатывает фоллбэк).
- **Acceptance:** офлайн-evals (60 сценариев) проходят; тест с галлюцинированным числом в `chat_reply` отклоняется и уходит в безопасный фоллбэк; квоты работают как раньше.
- **Verify:** `python -m unittest services/api/tests/test_chat_tools.py -v`, `python scripts/check.py`, `python evals/run.py --offline`.

### CHECKPOINT-2 — Оркестратор: `Чекпоинт фазы 2`

2026-10-29: **CHECKPOINT-2 PASS**. T24b independently ACCEPTED,20 mock outcomes/69 focused; root244 backend,60 offline/schema,contracts,TS,independent doctor20/20 after CP2-ENV; full web export PASS. See reports/CHECKPOINT-2.md. No cloud activation/pilot/public approval.

### CP2-ENV — Align installed Expo SDK patch dependencies
- **Model:** Codex delegated executor · **Status:** done · **Depends on:** owner-authorized queue; actual CHECKPOINT-2 diagnostic19/20.
- **Scope:** apps/mobile/package.json, apps/mobile/package-lock.json; reports/CP2-ENV.md. Existing dependency patch alignment only; no new packages, UI or backend changes.
- **Acceptance:** align doctor-reported expo~58.0.21, expo-constants~58.0.14, expo-dev-client~58.0.17, expo-font~58.0.11, expo-linking~58.0.15, expo-router~58.0.28, react-native0.88.1; doctor20/20 and typecheck. Preserve other dependencies and scripts. Lockfile reflects local install; no global install.
- **Verify:** npm run typecheck; npx expo-doctor; full Expo web export; diff check. Root independent diff/evidence review, no self acceptance.

---

## Фаза 3 — Продакшн-инфраструктура (Приоритет 3)

### T30 — Решение по БД и авторизации (ADR)
- **Model:** Codex delegated executor · **Status:** done · **Depends on:** approved PILOT_SPEC decision; documentation may be recorded before CHECKPOINT-2, real cloud data still requires accepted CHECKPOINT-2. Owner authorized full sequential/parallel queue.
- **Decision:** Resolved 2026-10-29: Supabase Postgres/Auth/private Storage, email OTP; Render FastAPI plus separate worker; Postgres jobs/outbox without Redis. Local synthetic SQLite remains a compatibility test mode. No cloud activation, purchase or local-data upload authorized.
- **Scope:** `docs/adr/0001-database-and-auth.md` (новый)
- **Steps:** зафиксировать выбранный пользователем вариант в архитектурном решении `docs/adr/0001-database-and-auth.md` (Context, Decision, Consequences, Migration Path).
- **Acceptance:** файл `docs/adr/0001-database-and-auth.md` создан и отражает выбранный вариант.
- **Review 2026-10-29:** root independent ACCEPT: ADR manually checked against PILOT_SPEC and actual local owner/store implementation; all approved decisions traced, no invented provider/paid settings, explicit migration/rollback and activation gates. Report T30.md. Documentation only, not cloud readiness.

### T31 — Alembic-миграции
- **Model:** GPT-6.1 Sol · **Status:** done · **Depends on:** T30, T50
- **Independent acceptance 2026-10-29:** reports/T31-independent.md ACCEPT; focused10/10, root combined backend259/259 (43.134s). SQLite baseline/adoption only; cloud/PostgreSQL evidence remains separate.
- **Scope:** `services/api/alembic/`, `services/api/alembic.ini`, `services/api/vela/store.py`, `services/api/tests/test_migrations.py` (новый)
- **Authorized scope clarification 2026-10-29:** services/api/requirements.txt may declare Alembic for this explicitly named task; install only in project-local virtualenv with existing system site packages, never globally. Add reports/T31.md and docs/product/migrations.md. Baseline preserves all five current tables/full JSON; no new product entities/cloud connection. No unspecified database driver until its scoped task requires one.
- **Steps:** настроить `alembic.ini` и `services/api/alembic/env.py` + начальную миграцию `0001_initial_schema.py` для всех таблиц `store.py` (`upgrade` создаёт таблицы, `downgrade` удаляет). Добавить тест `test_migrations.py`, проверяющий программный вызов `upgrade` → `downgrade` → `upgrade` на временной SQLite БД.
- **Acceptance:** `upgrade head` → `downgrade base` → `upgrade head` на чистой БД проходит в тесте; все тесты `check.py` зелёные.
- **Verify:** `python -m unittest services/api/tests/test_migrations.py -v`, `python scripts/check.py`.
- **PLAN-01 clarification:** T50 определяет совместимость существующей базы. Цикл downgrade base допустим только на одноразовой тестовой БД; отдельно проверить перенос заполненной demo-базы без потери сумм, операций и истории. Удаление существующей рабочей базы не является шагом миграции. Последующие схемы T51/T53/T55/T59 идут собственными миграциями.

### T32 — Многопользовательская авторизация JWT + изоляция по `user_id`
- **Model:** Codex delegated backend/session executors · **Status:** done · **Depends on:** T31 · `[OPUS-REVIEW]`
- **Independent acceptance 2026-10-29:** reports/T32-independent.md; root12 JWT/isolation +17 session +289 backend PASS, TS/contracts/UI6 pass. Mocked provider/synthetic SQLite only; T52 UI and T70 live cloud configuration remain separate.
- **Scope:** `services/api/vela/auth.py` (новый), `services/api/vela/main.py`, `services/api/vela/store.py`, `services/api/alembic/`, `services/api/tests/test_isolation.py` (новый), `apps/mobile/src/lib/api.ts`
- **Orchestrator scope clarification 2026-10-29:** implement accepted Supabase email OTP/session adapter and trusted asymmetric JWT verification as specified in reports/T32-preflight.md, using APP_MODE only. Scope additionally includes services/api/requirements.txt (explicit PyJWT[crypto] declaration, project-local environment only), a small mobile auth adapter and deterministic session-adapter tests, docs/product/authentication.md and reports/T32.md. Reuse existing httpx/fetch/SecureStore; no Supabase SDK, password system, live provider calls, new product tables or automatic local-data transfer. T52 owns screens/account-cache flows; T70 owns actual provider/SMTP configuration and activation. Begin only after T31 independent acceptance. Existing scripts/check-ui-regressions.cjs loader-only support for the new session module is included; preserve all prior assertions.
- **Acceptance:** изоляция состояния по `user_id` (из проверенного JWT-токена или `DEMO_API_TOKEN` при `APP_ENV=local`); тесты в `test_isolation.py`: пользователь A не читает и не меняет данные пользователя B, подмена `user_id` в теле запроса игнорируется, истёкший/невалидный токен → `401`; `DEMO_API_TOKEN` работает только при `APP_ENV=local`.
- **Verify:** `python -m unittest services/api/tests/test_isolation.py -v`, `python scripts/check.py`.
- **PLAN-01 clarification:** ADR T30/T50 определяет реальный путь получения/обновления/завершения сессии и входа пользователя; одной проверки заранее выданного JWT недостаточно для J02. До реализации уточнить Scope для выбранного провайдера/локального варианта, не вводить собственную парольную систему по догадке. Изоляция охватывает state, imports, runs, publications и командные receipts. Мобильный путь входа/выхода и очистку прежнего состояния завершает T52. Название переменной среды согласовать с фактическим APP_MODE в коде, не оставлять параллельный непроверенный APP_ENV-bypass.

### T33 — Durable worker + outbox для импорта
- **Model:** Astra GPT 6 (или Argon) · **Status:** todo · **Depends on:** T31, T32, T34
- **Scope:** `services/api/vela/worker.py` (новый), `services/api/vela/jobs.py` (новый), `services/api/vela/imports.py`, `services/api/vela/main.py`, `scripts/run-worker.py` (новый), `services/api/tests/test_worker.py` (новый)
- **Orchestrator scope clarification:** reports/T33-preflight.md is the bounded implementation contract after T34 acceptance. Include store.py common-transaction guards, new migration and version-aware validator, docs/product/jobs.md, generated contracts. Durable job row is its transactional dispatch outbox; no Redis or new SDK. Explicit infrastructure defaults: lease120seconds, heartbeat30seconds, maximum3attempts, exponential retry5seconds times2^(attempt-1), configurable/validated; these are operational controls, not financial rules. Idempotent enqueue/status/retry/cancel and owner deletion/generation races require focused proofs. No live AI/provider/database activation in verification.
- **Acceptance:** постановка импорта в очередь `POST /v1/imports/jobs` → `202` + `job_id`; статус `GET /v1/jobs/{id}`; ретраи с backoff, dead-letter, возврат зависших задач по `lease_until` (lease timeout); удаление данных (`DELETE /v1/data`) очищает задачи пользователя.
- **Verify:** `python -m unittest services/api/tests/test_worker.py -v`, `python scripts/check.py`.

### T34 — Приватное файловое хранилище (`storage.py`)
- **Model:** GPT-6.1 Sol delegated executor; independent security review required · **Status:** in_progress · **Depends on:** T32
- **Approved architecture clarification:** ADR0001/PILOT_SPEC replace the legacy filesystem-only cloud design: Supabase private Storage for cloud, isolated filesystem adapter for local tests, explicit retention consent, expiry30days and retryable physical deletion. Scope includes storage metadata persistence/migration, version-aware migration validation, docs/product/storage.md and report. Exact provider operations are mocked; activation/RLS/backup evidence stays T70/T62. Do not alter frozen initial migration. T34 starts after T32 acceptance; root serializes main/store/migration ownership.
- **Decision:** D5 — согласовать хранение оригиналов, сроки и согласие перед интеграцией сохранения файлов. Не передавать исходники внешнему провайдеру без действующих разрешений.
- **Scope:** `services/api/vela/storage.py` (новый), `services/api/vela/main.py`, `services/api/tests/test_storage.py` (новый)
- **Steps:**
  1. Создать `services/api/vela/storage.py` (`PrivateStorage` с корневой папкой `.local/storage/` вне webroot):
     - `save_file(user_id: str, filename: str, data: bytes) -> StoredFile`: сохраняет файл в изолированную папку пользователя `.local/storage/<safe_user_id>/<file_id>`, считает и сохраняет контрольную сумму `sha256` в `.meta.json`. Запрещает path traversal (`..`, `/`, `\`).
     - `read_file(user_id: str, file_id: str) -> bytes`: читает файл и проверяет `sha256` (при несовпадении выбрасывает `ValueError("Integrity check failed")`).
     - `erase_user_files(user_id: str) -> None` и `erase_all() -> None`: полностью удаляет файлы с диска.
  2. Подключить `erase_user_files(authenticated_user_id)` в `DELETE /v1/data` в `services/api/vela/main.py`. `erase_all()` не доступна пользовательскому API; тестовая очистка изолированной среды не является пользовательским удалением.
  3. Написать `services/api/tests/test_storage.py`: сохранение, проверка `sha256`, ошибка при повреждении байтов на диске, защита от path traversal, полное удаление файлов при `DELETE /v1/data`.
- **Acceptance:** файлы хранятся в папке пользователя с проверкой `SHA-256` при чтении; `DELETE /v1/data` удаляет все файлы только текущего пользователя. A не читает и не удаляет файлы B; проверено отдельными тестами. Владелец берётся из проверенной сессии, не из тела запроса. SHA-256 — проверка целостности, не шифрование.
- **Verify:** `python -m unittest services/api/tests/test_storage.py -v`, `python scripts/check.py`.

### T35 — Структурные логи + X-Correlation-ID
- **Model:** Codex delegated executor · **Status:** done · **Depends on:** CHECKPOINT-2 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/logging_setup.py` (новый), `services/api/vela/main.py` (только подключение middleware), `services/api/tests/test_correlation.py` (новый)
- **Acceptance:** JSON-форматтер логов; middleware принимает заголовок `X-Correlation-ID` (или генерирует UUID4, если не передан) и возвращает его в заголовке ответа `X-Correlation-ID`; фильтр логов гарантирует отсутствие сырых сумм, описаний транзакций и PII в логах.
- **Verify:** `python -m unittest services/api/tests/test_correlation.py -v`, `python scripts/check.py`.

### CHECKPOINT-3 — Оркестратор: `Чекпоинт фазы 3`

---

## Фаза 4 — Тесты, документация, CI (Приоритет 4)

### T40 — Jest + RNTL: настройка
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-3
- **Scope:** `apps/mobile/package.json` (devDeps: `jest-expo`, `@testing-library/react-native`), `apps/mobile/jest.config.js`, `apps/mobile/src/__tests__/smoke.test.tsx`
- **Acceptance:** `npm test` проходит; `npx expo-doctor` по-прежнему 20/20.
- **Verify:** `cd apps/mobile; npm test; npx expo-doctor`.

### T41 — Компонентные тесты
- **Model:** Flash · **Status:** todo · **Depends on:** T40
- **Scope:** `apps/mobile/src/__tests__/*.test.tsx`
- **Acceptance:** ≥ 10 осмысленных тестов: `components/ui.tsx` (Chip, карточки), форма Add bill (валидация), Adjust (превью без мутации), состояние ошибки сети, пустые состояния.
- **Verify:** `cd apps/mobile; npm test`.

### T42 — Maestro E2E сценарии
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-3 · `[PARALLEL-OK]`
- **Decision:** есть ли Android-эмулятор / iOS-симулятор / реальное устройство для живого прогона? (Создание самих YAML-флоу не блокируется; живой прогон отмечается отдельно).
- **Scope:** `tests/e2e/*.yaml` (новые), `tests/e2e/README.md` (новый)
- **Steps:** написать декларативные Maestro E2E сценарии для Journeys A–E (`01_snapshot.yaml`, `02_import.yaml`, `03_plan_and_debts.yaml`, `04_assistant_chat.yaml`, `05_lessons_and_delete.yaml`) и инструкцию запуска в `tests/e2e/README.md`.
- **Acceptance:** все 5 YAML-флоу для Journeys A–E + export/delete созданы и синтаксически валидны.

### T43 — Документация (ADR, design-system, ux-decisions, playbooks)
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-3 · `[PARALLEL-OK]`
- **Scope:** `docs/adr/0002..0006-*.md`, `docs/design-system.md`, `docs/ux-decisions.md`, `docs/playbooks/{financial-correctness,design-consistency,agent-evaluation,release-verification}.md`
- **Steps:** ADR на уже принятые решения: (0002) целые центы EUR и горизонтный прогноз баланса, (0003) только Gemini Flash-Lite модели + SQLite-квоты, (0004) идемпотентность и оптимистичная блокировка `expected_revision`, (0005) base64-импорт для React Native, (0006) каталог 15 действий и MCDA со снапшотами. `design-system.md` — токены из `apps/mobile/src/theme.ts`. Плейбуки — короткие чеклисты (≤ 1 страницы) с реальными командами проверки.
- **Acceptance:** все файлы созданы; каждый плейбук ≤ 1 страницы и ссылается на реальные команды проекта.
- **PLAN-01 clarification:** исторический текст Steps не доказывает принятия решения. ADR 0003 фиксирует реально выбранную маршрутизацию runtime-моделей и её расхождения со спецификацией §11; формулировку «только Flash-Lite» нельзя выдавать за согласованную без доказательства. ADR 0001/0007 создаются T30/T50, не дублируются T43.

### T44 — Модель угроз и карта данных (`threat-model.md`, `data-map.md`)
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-3 · `[PARALLEL-OK]` · `[OPUS-REVIEW]`
- **Scope:** `docs/security/threat-model.md` (новый), `docs/security/data-map.md` (новый)
- **Steps:** описать границы доверия (Mobile App ↔ FastAPI ↔ Gemini Cloud API ↔ Local/DB Storage), таблицу угроз по STRIDE для каждой границы, защиту от prompt injection через банковские выписки, маскирование PII (`pii.py`), хранение и полное удаление по `DELETE /v1/data`, владельца каждого остаточного риска.
- **Acceptance:** оба документа созданы, покрывают STRIDE, prompt injection, PII и удаление данных; проходят ревью оркестратора.

### T45 — CI-пайплайн
- **Model:** Flash · **Status:** todo · **Depends on:** T40
- **Scope:** `.github/workflows/ci.yml`
- **Acceptance:** джобы: `python scripts/check.py`, `npm ci && npm run typecheck && npm test`, contract drift (`generate-contracts.py --check`), секрет-скан (`gitleaks`), `python evals/run.py --offline`; все GitHub Actions закреплены по мажорной/полной версии.
- **Verify:** проверка валидности YAML и совпадения команд с локальными скриптами.

### T46 — Финальный аудит готовности
- **Model:** Astra GPT 6 (orchestrator) · **Status:** todo · **Depends on:** T30–T35, T40–T45, T50–T63, CHECKPOINT-2, CHECKPOINT-3 (все done)
- **Steps:** полный прогон проверок; обновить `docs/release-readiness.md` по 4 уровням (`local demo` / `staging` / `pilot` / `public`); перечислить гейты, требующие подписи человека (финансовый, юридический и security-ревью, учётки сторов).
- **Acceptance:** A–J и J01–J12 из PRODUCT_PLAN сопоставлены с доказательствами; ни один обязательный продуктовый пробел не спрятан за зелёной инфраструктурой. Готовность каждой среды оценивается отдельно; недостающая человеческая проверка остаётся BLOCKED. Аудит не является разрешением на деплой.

### CHECKPOINT-4 — Оркестратор: `Чекпоинт фазы 4`

## Продуктовые срезы — соответствие видению (T50–T63)

Добавлены PLAN-01, 2026-10-27. Порядок выполнения определяется **Depends on**, не номером: T50 обязателен перед T31; T51–T60 могут выполняться после своих зависимостей, не дожидаясь всех задач фазы 4. Подготовка T40–T45 не блокируется окончанием продуктовых срезов. Финальный T46 ждёт их приёмки. Это основной объём исходного видения, не необязательные улучшения P1–P5.

Для новых задач:
- Общий Definition of Done из AGENTS обязателен; API-изменения включают `contracts/openapi.json`, `apps/mobile/src/lib/generated.ts` в Scope и генерацию + `--check`.
- Названия новых файлов — проектируемые; перед стартом подтвердить реальные пути. Если путь/Scope нужно изменить, сначала обновить карточку задачи с объяснением.
- При слишком большом срезе оркестратор до реализации делит его на T<NN>a/b с отдельными Scope/Acceptance/Verify; родитель done только после всех частей и интеграционной приёмки. Не исполнять несколько задач за чат.
- Новые библиотеки отдельно согласуются по AGENTS; этот план не разрешает установку сервисов, оплату или деплой.
- `review` → `done` только независимым ревью. В Verify `backend` означает `python scripts/check.py`, `contracts` — генерацию и проверку drift, `mobile typecheck` — `npm run typecheck` в apps/mobile. Указанный новый тестовый файл создаётся задачей, до реализации его команды не считаются выполненными.

### T50 — Контракт данных и переход от demo к пользовательскому продукту
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** done · **Depends on:** T30
- **Scope:** docs/adr/0007-product-data-contract.md (новый), docs/product/data-contract.md (новый)
- **Steps:** Спроектировать минимальный совместимый контракт для профиля, счетов/остатков, received/expected income, целей/allocations, provenance, import/source rows, action/execution links, preferences и chat. Сопоставить с текущим State; не требовать отдельную таблицу для каждой сущности. Зафиксировать API-совместимость, версии, сохранность существующих данных, миграционный путь и откат. БД берётся только из T30.
- **Acceptance:** Каждое A–J из PRODUCT_PLAN имеет владельца данных и последующую задачу; неизвестное не становится нулём; запрет двойного учёта и ownership описаны; спорные финансовые правила вынесены в Decision. Нет кода/новых зависимостей.
- **Independent review 2026-10-29:** ACCEPT docs contract by separate Astra context; reports/T50-independent.md. Current five tables/full JSON, personal/planning/legacy allocations, ownership, revision/idempotency, /v1 guards and additive /v2 migration verified against source. No runtime/cloud/migration acceptance implied.
- **Verify:** Ручная сверка с USER_VISION §2–8, мастер-спецификацией §7–10 и текущими моделями; независимое архитектурное ревью.

### T51 — Сохраняемый профиль и происхождение финансовых данных
- **Model:** GPT-6.1 Sol delegated executor; independent review accepted · **Status:** done · **Depends on:** T32, T50
- **Scope:** services/api/vela/{domain.py,store.py,main.py}, services/api/alembic/, services/api/tests/test_profile.py (новый)
- **Current ownership clarification:** reuse PersonalState JSON aggregate through personal.py profile fields and a dedicated profile.py installer; add docs/product/profile.md and report. Preserve legacy profile route/command. No new SQL entity needed without proof; T34 owns store/migrations/main during parallel work. Root registers profile installer after that source freezes. Optional income/provenance/preferences are not received financial events.
- **Steps:** Реализовать часть контракта T50: профиль, income type/range, явные предпочтения и подтверждение/свежесть/источник фактов. Сохранить текущий API совместимым либо документировать переход. Обновление предпочтений версионировать отдельно; пропуск допустим. Счета/балансовый anchor и связи операций завершаются T53.
- **Acceptance:** Профиль восстанавливается после перезапуска; A не читает/меняет B; неизвестный доход не превращается в полученный; значения вне диапазона/конфликт версий отклоняются; старая demo-база мигрирует без потери суммы/истории.
- **Verify:** python -m unittest discover -s services/api/tests -p test_profile.py -v; обязательные backend/migration/contract проверки.

### T52 — Постепенный onboarding и редактирование профиля
- **Model:** GPT-6.1 Sol · **Status:** todo · **Depends on:** T51
- **Scope:** apps/mobile/src/app/{snapshot.tsx,connect.tsx,settings.tsx}, apps/mobile/src/components/StateGate.tsx, apps/mobile/src/lib/{api.ts,state.tsx}, services/api/vela/main.py (только устранение скрытых defaults первого импорта), services/api/tests/test_profile.py
- **Steps:** Подключить пользовательскую сессию T32 и профиль T51, постепенные вопросы/пропуск/возврат/исправление. Привязать к фактическим путям после инвентаризации перед стартом. Предложенная цель требует выбора; неизвестный остаток блокирует только действия, которым он нужен. Не собирать лишние личные данные.
- **Acceptance:** J01/J02 проходят; после перезапуска сохраняются подтверждённые значения; первый импорт не навязывает demo-цель/буфер; выход из аккаунта не показывает данные прежнего пользователя; понятны ошибки и конфликт.
- **Verify:** npm run typecheck в apps/mobile; backend/contract при изменении API; воспроизводимый сценарий J01/J02 с указанной средой, автоматизация в T63.

### T53 — Сверка импорта, происхождение строк и исправления
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T51, T33, T34
- **Scope:** services/api/vela/{imports.py,domain.py,store.py,main.py}, services/api/alembic/, services/api/tests/test_import_reconciliation.py (новый), apps/mobile/src/app/import.tsx, apps/mobile/src/lib/api.ts
- **Steps:** Подключить UI к заданиям, показать статус/повтор/превью, строки с источником и исправлением категории/суммы/даты до применения. Реализовать контракт счетов/остатков/собственных переводов T50, связь manual income с импортом; неоднозначность дубля требует решения. Применение отдельной идемпотентной командой.
- **Acceptance:** J03/J04 и связь выполнения из J08: повтор/перекрытие не удваивает операции или доход; closing balance не складывается с историческими строками; перевод между своими счетами не доход; ошибка/удаление/повтор задания не создают лишних записей. Неподдержанная валюта обозначена без выдуманного FX.
- **Verify:** python -m unittest discover -s services/api/tests -p test_import_reconciliation.py -v; backend, contracts, mobile typecheck; независимые числовые фикстуры.

### T54 — Неопределённый доход и многопериодные сценарии
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T51, T53
- **Scope:** services/api/vela/{domain.py,debt.py,tools.py,catalogue.py,main.py}, services/api/tests/test_income_scenarios.py (новый), policies/ (только согласованные параметры)
- **Steps:** Разделить received/expected/confirmed future и допущения. Считать задержку дохода/изменение расходов, обязательства по датам, разовый и регулярный расход на раскрытом горизонте. Не устанавливать вероятности, буферы и пороги по догадке; при нехватке данных — уточнение.
- **Acceptance:** J05/J07: положительный итог месяца не скрывает промежуточный shortfall; регулярный платёж нельзя обосновать только текущим cash; долг с неизвестными существенными условиями не получает точного обещания; сравнение использует совместимые горизонты и явные допущения.
- **Verify:** python -m unittest discover -s services/api/tests -p test_income_scenarios.py -v; backend/contracts; независимые фиксированные эталоны и сохранение T10–T12.

### T55 — Несколько целей и калькулятор вкладов
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T51, T54
- **Scope:** services/api/vela/{domain.py,store.py,main.py,tools.py,catalogue.py}, services/api/vela/goals.py (новый), services/api/alembic/, services/api/tests/test_goals.py (новый)
- **Steps:** Цели с суммой/сроком/приоритетом, тип reserve или known expense, явные allocations, варианты вклада/срока и отказ от предложенной цели. Мигрировать одну существующую цель; не менять финансовые веса без решения.
- **Acceptance:** J06 на API: один евро не выделяется двум целям; перенос между счетами не создаёт прогресс; непосильный вклад отвергается; нет цели — разрешённый пустой сценарий; what-if не меняет state.
- **Verify:** python -m unittest discover -s services/api/tests -p test_goals.py -v; backend/migrations/contracts; эталоны для двух целей.

### T56 — Три специалиста на одной версии состояния
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T54, T55, T24b
- **Scope:** services/api/vela/{coordination.py,catalogue.py,decision.py,tools.py}, services/api/tests/test_coordination.py, services/api/tests/test_specialists.py (новый)
- **Steps:** Дополнить cash-flow/spending, debt и savings/goals структурированными результатами T50. Explanation оставить отдельной необязательной функцией. Описать достаточность данных для трендов расходов/комиссий/повторяющихся кассовых провалов; выдавать проверяемые наблюдения. Переиспользовать калькуляторы; отдельный платный LLM на роль не обязателен.
- **Acceptance:** Три направления дают кандидаты/ссылки на расчёты/неизвестное; причины неприменимости явные; missing debt не равен no debt; пакеты другой версии отклоняются; observations имеют источник и период; нет двойного счёта выгод.
- **Verify:** python -m unittest discover -s services/api/tests -p test_specialists.py -v; test_coordination.py/test_decision.py и полный backend.

### T57 — Единая публикация рекомендаций и пересчёт
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T56, T33, T35
- **Scope:** services/api/vela/{main.py,store.py,coordination.py,jobs.py,worker.py,domain.py}, services/api/tests/test_recommendation_flow.py (новый)
- **Steps:** Подключить coordinator/decision к API состояния и событиям изменений. Фоновая проверка по времени, coalescing, версии preferences/policy, отказ от устаревших результатов. Не создавать конкурирующий второй источник карточки; сохранить совместимость клиента до T58.
- **Acceptance:** J09/J11: одна действующая primary recommendation; старый worker не публикует; отказ обязательного расчёта отключает непроверенное действие; без существенного изменения карточка стабильна; crash между calculate/publish восстанавливается идемпотентно.
- **Verify:** python -m unittest discover -s services/api/tests -p test_recommendation_flow.py -v; backend/contracts; тесты гонок и fake clock без внешнего ИИ.

### T58 — Today и My Plan: единый путь решения и выполнения
- **Model:** GPT-6.1 Sol; review финансовых переходов Astra / Argon · **Status:** todo · **Depends on:** T57, T55, T53
- **Scope:** apps/mobile/src/app/(tabs)/{index.tsx,plan.tsx}, apps/mobile/src/app/{adjust.tsx,debts.tsx,snapshot.tsx}, apps/mobile/src/components/GoalCard.tsx, apps/mobile/src/lib/{api.ts,state.tsx}, services/api/vela/{domain.py,main.py,store.py}, services/api/tests/test_action_lifecycle.py (новый)
- **Steps:** Показать опубликованное действие, пользу, причину/альтернативу/допущения; цели/приоритеты и долги в My Plan. Поддержать accept/adjust/postpone/decline/complete по типам каталога; реализацию с большим scope разбить на подзадачи backend/UI до старта. Запись выполнения связать с операцией/аллокацией; исправления сохраняют историю.
- **Acceptance:** J06–J09: принятие не списывает средства, завершение не удваивается импортом; stale card не actionable; отказ не создаёт скрытую preference; причины и значения совпадают с decision snapshot; три основные вкладки сохранены.
- **Verify:** python -m unittest discover -s services/api/tests -p test_action_lifecycle.py -v; backend/contracts/mobile typecheck; наблюдаемые сценарии интерфейса, расширить проверки в T63.

### T59 — Постоянный ассистент и безопасные what-if
- **Model:** GPT-6.1 Sol; review Astra / Argon · **Status:** todo · **Depends on:** T24b, T51, T57, T55
- **Scope:** services/api/vela/{chat.py,tools.py,main.py,store.py}, services/api/alembic/, services/api/tests/test_assistant_history.py (новый), apps/mobile/src/app/(tabs)/assistant.tsx, apps/mobile/src/lib/api.ts
- **Steps:** Сохранять диалоги по владельцу с удалением, версиями контекста и ограничением передаваемой истории. Объяснять сохранённое решение, вызывать поддержанные сценарии; изменение реальных данных — только отдельная подтверждённая команда. Историю не отправлять безгранично в модель.
- **Acceptance:** J10: перезапуск сохраняет сообщения; другой пользователь не получает их; what-if не меняет полный State; старые суммы не выдаются за текущие; отказ/timeout/квота сохраняют безопасный путь T24b.
- **Verify:** python -m unittest discover -s services/api/tests -p test_assistant_history.py -v; backend/contracts/mobile typecheck; offline evals и mocked model negative cases.

### T60 — Связать уроки с решениями и проверенным знанием
- **Model:** GPT-6.1 Sol; контент D4 · **Status:** todo · **Depends on:** T58, T17, T18
- **Scope:** services/api/vela/{lessons.py,tools.py,chat.py}, content/lessons/, policies/action-catalogue.v1.json (только lesson associations), apps/mobile/src/app/learn/[id].tsx, services/api/tests/test_lessons.py
- **Steps:** Проверить и дополнить путь принцип → интерактивный пример → вопрос/обратная связь; привязать к действию. Reviewed sources с датой/применимостью отдельно от финансовой политики. Не включать embeddings или open-web research без доказанной необходимости.
- **Acceptance:** Урок доброволен; прогресс сохраняется; личные числа только из актуального калькулятора; непроверенный материал не представлен как reviewed; в runtime доступны только подходящие проверенные материалы либо явное отсутствие ответа.
- **Verify:** python -m unittest discover -s services/api/tests -p test_lessons.py -v; backend, mobile typecheck; ручная проверка всего контента с D4/T61.

### T61 — Калибровка предпочтений и проверка финансового содержания
- **Model:** Astra / Argon + человек D4 · **Status:** todo · **Depends on:** T56, T60
- **Scope:** docs/product/policy-calibration.md (новый), policies/scoring.v1.json, content/lessons/ (только согласованные исправления), evals/calibration/ (новый), services/api/tests/test_decision.py
- **Steps:** Подготовить swing-weighting сценарии, проверить scales/overlap/сравнимость горизонтов/чувствительность при изменении финансовых допущений и весов. Получить явные предпочтения; единичный отказ не основание для вывода. Человек проверяет каталог, поддержанные продукты, пороги и уроки; до подписи provisional сохраняется.
- **Acceptance:** Решения по значениям и ограничениям имеют автора/дату/версию; нестабильное решение ведёт к уточнению/сохранению допустимого плана; нет ложной отметки reviewed; отсутствие человека даёт blocked, а не self-signoff.
- **Verify:** Проверка артефактов калибровки, backend/decision regression при изменении политики; подписанная проверка человеком. D4/D6 обязательны до live approval.

### T62 — Полный жизненный цикл данных и восстановление
- **Model:** Astra / Argon; независимое security review · **Status:** todo · **Depends on:** T53, T55, T59, T34, T44
- **Scope:** services/api/vela/{main.py,store.py,storage.py,jobs.py,worker.py}, services/api/tests/test_data_lifecycle.py (новый), docs/playbooks/data-recovery.md (новый), docs/security/data-map.md
- **Steps:** Расширить export/delete на все новые сущности; согласовать retention D5, удаления originals отдельно от transactions, backup lifecycle. Выполнить restore/rollback drill только в выделенной тестовой среде; задачи не воскрешают удалённого пользователя.
- **Acceptance:** J12: A удаляет только свои данные; токены/пути не дают доступ к B; диалоги/файлы/previews/jobs охвачены; повтор удаления безопасен; восстановление сохраняет суммы/связи; остаточные counters/backups честно описаны.
- **Verify:** python -m unittest discover -s services/api/tests -p test_data_lifecycle.py -v; backend/contracts; протокол restore/rollback и isolation tests.

### T63 — Сквозная приёмка видения, качество и расходы
- **Model:** Astra / Argon; подготовка сценариев GPT-6.1 Sol · **Status:** todo · **Depends on:** T58, T59, T60, T61, T62, T41, T42, T45
- **Scope:** tests/e2e/, evals/ (новые acceptance-наборы, не переписывать историю результатов), docs/product/acceptance.md (новый), docs/release-readiness.md, PRODUCT_PLAN.md
- **Steps:** Прогнать J01–J12 и A–E на заявленных устройствах, accessibility, ошибки сети/квот и восстановление; для AI разделить offline, mocks и разрешённые live trials. Добавить свежую независимую выборку после настройки на прежних heldout. Измерить latency/spend по сценарию и согласованному D7 бюджету; не запускать платные/real-data проверки без разрешения.
- **Acceptance:** Каждый сценарий имеет результат/среду/дату/доказательство; лимиты спецификации проверены либо явно blocked; рекомендации/веса/уроки не обходят T61; нет выдуманного общего процента и статуса public-ready.
- **Verify:** Фактические backend/mobile/contract/evals/E2E команды из реализованных конфигов; измерения с объёмом выборки и отказами; незапущенные проверки отмечены BLOCKED.

### UI-01 — Исправления UI по MANUAL-05
- **Model:** Codex · **Status:** review · **Depends on:** пользовательский запрос исправить найденные UI-ошибки.
- **Scope:** `apps/mobile/src/app/(tabs)/plan.tsx`, `apps/mobile/src/app/adjust.tsx`, `apps/mobile/src/app/(tabs)/index.tsx`, `apps/mobile/src/components/StateGate.tsx`, `apps/mobile/src/lib/api.ts`, `scripts/check-ui-regressions.cjs`; эта карточка, HANDOFF и `docs/agents/reports/UI-01.md`.
- **Acceptance:** Cancel доступен при shortfall; ошибки счета понятны и сбрасываются после редактирования/закрытия; Add требует актуального допустимого preview; Learn доступен с Today, отключённый StateGate ведёт к Connect. Без новых зависимостей и изменений финансового API.
- **Verify:** `node scripts/check-ui-regressions.cjs`, `python scripts/check.py`, mobile `npm run typecheck`, полная web-сборка. Ручной UI-прогон только при доступном browser use; ограничения указать отдельно.

## Approved pilot implementation — 2026-10-29

### T64 — Approved specification, uxpeak and project skill cleanup
- **Model:** Codex; independent review required · **Status:** review · **Depends on:** —
- **Scope:** AGENTS.md, PRODUCT_PLAN.md, master specification amendment, docs/product/PILOT_SPEC.md, docs/design-system.md, docs/skills-manifest.md, .agents/skills/, BACKLOG/HANDOFF, report.
- **Acceptance:** Persist approved journeys, preserve history; exactly nine skills, no active dangling Native Core references; no application acceptance claimed.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T65 — Shared mobile UI foundation
- **Model:** Codex; independent review required · **Status:** review · **Depends on:** T64
- **Scope:** apps/mobile/src/theme.ts, apps/mobile/src/components/ui.tsx, report and status files.
- **Acceptance:** Neutral/green light-dark semantic palette; 16 body/48 targets; pending/destructive/icon buttons, helper/errors; typecheck and backend checks; device verification separate.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T66 — Synthetic isolated pilot navigation prototype
- **Model:** Codex; independent review required · **Status:** review · **Depends on:** T65
- **Scope:** apps/mobile/src/app/, apps/mobile/src/components/, synthetic fixtures, report and status files.
- **Follow-up 2026-10-29:** three owner-requested browser findings corrected and rerun; report T66 follow-up. Status remains review pending independent/native acceptance.
- **Owner authorization 2026-10-29:** proceed to T66 on the current T65 foundation; T64/T65 remain review, no independent acceptance implied.
- **Acceptance:** All pilot routes/states demonstrable without real finances; example isolated; Android/iPhone UX evidence required before integrated acceptance.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T67 — Frankfurter v2 EUR/HUF valuations
- **Model:** Codex delegated executor; independent review completed · **Status:** done · **Depends on:** T50, T31
- **Independent acceptance 2026-10-29:** T67-service-independent.md + T67-routes-independent.md;11 service/7 HTTP independently pass, root289 backend/contracts/TS pass. Read-only display valuations; live quote smoke not run.
- **Scope:** services/api/vela/fx.py, tests, v2 schemas/contracts, report and status files.
- **Orchestrator bounded delegation:** first isolated fx.py service/tests + docs/product/fx.md + report; no main/store/schema edits while T32 owns integration. API wiring is a subsequent reviewed delta before task acceptance. No guessed rounding policy; expose missing decision if contract does not specify.
- **Acceptance:** ECB source, Decimal, current/historical cached rates; missing rate incomplete total, no FX affordability; deterministic tests and opt-in live smoke.
- **Owner decision 2026-10-29:** round to nearest output minor unit, ties HALF_UP (EUR1.005→1.01), once after exact Decimal aggregation; no binary float.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T68 — Optional local reminders
- **Model:** Codex; independent review required · **Status:** todo · **Depends on:** T52, T58
- **Scope:** apps/mobile reminder module/settings, v2 preferences, migrations/tests/contracts, report and status files.
- **Acceptance:** Explicit expo-notifications dependency; daily/weekdays/N-days/time; per-device opt-in, neutral text, logout/cancel/timezone handling; native verification.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T69 — Home-screen Add income shortcut
- **Model:** Codex; independent review required · **Status:** todo · **Depends on:** T54, T58
- **Scope:** apps/mobile config/dependency/shortcut module, income route, tests, report and status files.
- **Acceptance:** Explicit expo-quick-actions dependency after SDK compatibility; cold/warm/auth resume opens form without writing; both native platforms.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.

### T70 — Cloud configuration and activation estimate
- **Model:** Codex; independent review required · **Status:** todo · **Depends on:** T30, T32, T33, T34
- **Scope:** deployment templates, operations docs, report and status files.
- **Acceptance:** Render API/worker + Supabase + SMTP configuration without secrets; monthly estimate and activation checklist; no deployment/purchase without owner approval.
- **Verify:** git diff --check; task-relevant checks recorded in report; code changes require python scripts/check.py, mobile typecheck if affected, contract check if API affected.


### T71 — Local saved personal profile/accounts/income slice
- **Model:** GPT-6.1 Sol · **Status:** review · **Depends on:** owner request 2026-10-29 to connect new screens to backend, bounded local-first slice; cloud/security gates unchanged.
- **Scope:** personal.py models/routes, State personal field and legacy-view exclusion, main router registration, personal screen/connect/layout/preview entry, personal tests, generated contracts, docs/task reports.
- **Acceptance:** authenticated local /v2 persistence; optional unknown balance, profile, EUR/HUF accounts, replacement balance and three income modes; retry identity/revision conflict; legacy finances unchanged; export/delete include data. No cloud/auth/FX/recommendation acceptance.
- **Verify:** backend check, targeted personal tests, mobile typecheck, generate-contracts and --check, full web export. Native/UI persistence proof separate.

### UI-TEST-05 — Full workflow verification
- **Model:** GPT-6.1 Sol · **Status:** review · **Depends on:** owner request to exercise the complete user workflow.
- **Scope:** reports/UI-TEST-05.md, HANDOFF/BACKLOG, generated offline eval report. Verification only.
- **Result:** integrated path blocked at personal-to-plan/assistant/import/settings navigation; complete U01-U22/J01-J12 dispositions and prototype-vs-persisted evidence in report. No code acceptance implied.
- **Verify:** actual Chrome persistent/prototype paths, backend217, journeys31, offline60, UI regression6, TS/contracts exit0. Native checks unrun.

### UI-02 — Restore connected navigation and protected-route return
- **Model:** Codex · **Status:** review · **Depends on:** owner request after UI-TEST-05; existing review statuses unchanged.
- **Scope:** mobile src/app/_layout.tsx, connect.tsx, personal.tsx, settings.tsx, (tabs)/index.tsx; src/lib/navigation.ts; scripts/check-navigation.cjs; docs/product/LOCAL_V2.md, BACKLOG/HANDOFF and reports/UI-02.md.
- **Acceptance:** saved accounts expose planning/data/learning; planning has return to accounts; protected direct routes reconnect to intended allowed local route; malicious/external return destinations rejected. Clearly distinguish legacy EUR planning inputs from v2 accounts; no automatic financial copying/summing/mutation. Existing planning workflow becomes testable by normal UI. No claim of completed shared financial-model integration.
- **Verify:** focused navigation regression, current UI regressions, backend suite, mobile typecheck, contract check, full web export; real Chrome entry-to-plan manual P0 and reachable downstream branches, with remaining failures documented.

### PATTERN-01 — Three synthetic statements with predeclared ground truth
- **Model:** Codex · **Status:** review · **Depends on:** owner request to create2-3 statements, determine expected patterns first, then use them in UI tests.
- **Scope:** docs/testing/pattern-statements/, docs/agents/reports/PATTERN-01.md, BACKLOG/HANDOFF. No product code or financial policy changes.
- **Acceptance:** exactly three clearly synthetic EUR statement CSVs, reconciled running balances and integer-minor-unit oracle; predefined recurring/income/price/refund/own-transfer patterns; real UI upload/apply/reimport comparison, known limitations stated. Never mark parser output as the oracle.
- **Verify:** independent Decimal/csv reconciliation; actual Chrome on isolated test DB; compare row counts and money effects, document semantic/pattern gaps. No live AI or paid calls.

### T72 — Local analytical import and cumulative evidence observations
- **Model:** Codex · **Status:** done · **Depends on:** explicit owner request after PATTERN-01; local-only slice, no cloud/security gate bypass.
- **Scope:** services/api/vela/{domain.py,imports.py,main.py,tools.py,observations.py}; tests/test_statement_analytics.py; mobile app/{import.tsx,observations.tsx,personal.tsx,(tabs)/index.tsx,(tabs)/plan.tsx}, lib/{api.ts,navigation.ts}; generated contracts; docs/product/LOCAL_V2.md; task records and report.
- **Acceptance:** new /v2 statement-apply only merges analytics and never creates/changes balance/saved/obligations/debt/actions; original /v1 apply retained for compatibility. Replace import UI balance/recurring-write controls with analytics-only copy and full preview pagination. Labelled refund credits separated from earnings in preview/summary/tools; imported future dates never finance a plan. Cumulative deterministic suggested observations across three source fixtures, dated evidence IDs/version, no invented confidence/financial thresholds or paid AI. Reachable history pagination beyond50. No automatic unification of legacy snapshot with v2 accounts; record as remaining separate migration.
- **Verify:** red/green fixture regressions including import invariants/retry/conflict/no-profile/future rows/refund/own-transfer/cumulative patterns/history; backend, typecheck, generate-contracts and drift, UI/navigation regressions, full web export; real isolated Chrome reimport fixtures.

- **Independent review 2026-10-29:** REWORK R1: summary-backed cash-flow tool omits explicit refund_cents (August oracle2000); raw branch/UI/summary correct. New isolated HTTP+Chrome import/reimport/evidence/history and backend231/targeted6/TS/contracts/UI/nav/web pass. See reports/T72.md Review; T74 remains accepted.
- **R1 execution 2026-10-29:** one-field fix plus frozen August raw/StateView/JSON oracle regression submitted for new-context review. Targeted7/backend238/TS/contracts/UI/nav/web PASS; report distinguishes current automated proof from historical Chrome evidence.
- **Independent R1 acceptance 2026-10-29:** ACCEPT ab6d533 in separate chat; fresh targeted7/backend242/oracle/TS/contracts/UI/navigation/web PASS. See reports/T72-independent-r1.md. Earlier independent import/Chrome evidence plus repaired R1 closes this bounded local task; no cloud/journey promotion.

### T73 — Browser JSON export delivery
- **Model:** Codex · **Status:** review · **Depends on:** owner request after UI-02 export Permission denied.
- **Scope:** apps/mobile/src/app/settings.tsx; reports/T73.md and BACKLOG/HANDOFF.
- **Acceptance:** web Export JSON downloads the authenticated export locally without navigator.share; native sharing remains. Do not claim success before preparing data; errors visible. Verify actual browser download contents against synthetic stored state and no connection token. No financial/backend/API changes.
- **Verify:** actual Chrome download, mobile typecheck, backend suite, full web export; diff check.

### T75 — Frontend integration contract and isolated development kit
- **Model:** Codex · **Status:** done · **Depends on:** T74 done; explicit owner request to prepare backend for the independent frontend prompt. Does not accept pending T72/T73 or cloud gates.
- **Scope:** services/api/vela/{frontend.py,main.py,planning.py}; services/api/tests/test_frontend.py; scripts/frontend-sandbox.py; contracts/frontend-client.mjs; scripts/test-frontend-client.mjs; generated OpenAPI/TypeScript; docs/product/FRONTEND_INTEGRATION.md; BACKLOG/HANDOFF and reports/T75.md.
- **Acceptance:** authenticated same-revision bootstrap for Today/My Plan/Assistant/settings; canonical read-only assistant context and what-if; explicit resume command with revision/idempotency; exact allowlisted CORS for separately hosted frontends; dependency-free client preserving retry identity; one-command synthetic development server on OS-selected free loopback port, unique database and AI disabled, never demo.db/API8000–8003; screen/control mapping and honest unsupported cloud/persistence features. Existing HTML remains disconnected. No financial policy changes or new dependencies.
- **Verify:** isolated API tests for unknown/no-goal/current-context/40+100 sequence/retry/conflict/what-if/erase/CORS/auth/restart; client tests; real loopback HTTP launch probe; backend suite; contracts generation and drift; mobile typecheck. Independent review required.
- **Independent acceptance 2026-10-29:** ACCEPT source458ecac in new chat; focused7/backend242/client/TS/contracts and separate actual launcher/native JS HTTP oracle pass on free55922, unique synthetic DB; stopped only owned child. See reports/T75-independent.md. Local integration kit only; no connected HTML/cloud claim.

### T74 — Canonical local EUR account plan and explicit legacy adoption
- **Model:** Codex · **Status:** done · **Depends on:** owner authorization to unify saved finances; bounded local-first slice after T72/T73, cloud gates unchanged.
- **Scope:** vela/planning.py, personal.py, main.py, lessons.py; tests/test_shared_planning.py; mobile app/{personal.tsx,shared-plan.tsx,shared-assistant.tsx,_layout.tsx,(tabs)/_layout.tsx,learn.tsx,debts.tsx}, components/{SharedNavigation.tsx,StateGate.tsx}, lib/{state.tsx,navigation.ts}, generated contracts; LOCAL_V2 and task records.
- **Acceptance:** one explicitly chosen known EUR account is the only current cash source for local plan/Today/local Assistant; no mirrored writable cash. Optional single goal, explicit buffer/bills/debt confirmations, idempotent reserve/cancel/earmark and separately confirmed bill payment, lower real balance blocks unsafe actions without erasing allocations. No goal required for viewing data/import. Explicit legacy adoption only when balances match, preserves original snapshot/history; legacy money writers disabled afterwards. HUF not converted or silently included. No cloud/FX/multi-goal/shared-AI-publication claim.
- **Verify:** API regression for canonical balance/income propagation, stale/retry, shortfall, one-time completion/payment, legacy adoption/preservation/old-writer guard, optional goal/restart; backend, contracts, typecheck, full export, actual isolated Chrome account->plan->income->complete and old data preserved. Review only; no done promotion.
