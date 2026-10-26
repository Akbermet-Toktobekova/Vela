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
- **Model:** GPT-6.1 Sol (security review: Astra / Argon) · **Status:** todo · **Depends on:** T24a, T23, T21b · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/chat.py`, `services/api/vela/ai.py`, `services/api/tests/test_chat_tools.py`
- **Steps:**
  1. В `chat.py` формировать контекст чата через вызов детерминированных инструментов из `tools.py` (`collect_all_tool_outputs(state)`) и проверять ответ модели через `verify_reply_numbers(reply, tool_outputs)` + проверку отказа на инвестиционные/налоговые советы.
  2. Если ответ Gemini содержит неподтверждённое число («галлюцинацию») или нарушает границы советов — отклонять ответ, делать максимум 1 повтор с жёстким напоминанием использовать только числа из инструментов, а при повторной неудаче или таймауте (> 20 с) возвращать детерминированный `local_reply`.
  3. Дополнить `services/api/tests/test_chat_tools.py` интеграционным тестом `chat_reply` с замоканным ответом Gemini, содержащим галлюцинированное число (проверить, что он отклоняется и срабатывает фоллбэк).
- **Acceptance:** офлайн-evals (60 сценариев) проходят; тест с галлюцинированным числом в `chat_reply` отклоняется и уходит в безопасный фоллбэк; квоты работают как раньше.
- **Verify:** `python -m unittest services/api/tests/test_chat_tools.py -v`, `python scripts/check.py`, `python evals/run.py --offline`.

### CHECKPOINT-2 — Оркестратор: `Чекпоинт фазы 2`

---

## Фаза 3 — Продакшн-инфраструктура (Приоритет 3)

### T30 — Решение по БД и авторизации (ADR)
- **Model:** Flash (после ответа пользователя) · **Status:** blocked · **Depends on:** CHECKPOINT-2
- **Decision:** (A) локальный PostgreSQL в Docker + Supabase позже; (B) Supabase cloud dev-проект сразу (нужны аккаунт и ключи); (C) пока остаться на SQLite + сделать Alembic-миграции и JWT-изоляцию `user_id` на уровне таблиц.
- **Scope:** `docs/adr/0001-database-and-auth.md` (новый)
- **Steps:** зафиксировать выбранный пользователем вариант в архитектурном решении `docs/adr/0001-database-and-auth.md` (Context, Decision, Consequences, Migration Path).
- **Acceptance:** файл `docs/adr/0001-database-and-auth.md` создан и отражает выбранный вариант.

### T31 — Alembic-миграции
- **Model:** Flash · **Status:** todo · **Depends on:** T30
- **Scope:** `services/api/alembic/`, `services/api/alembic.ini`, `services/api/vela/store.py`, `services/api/tests/test_migrations.py` (новый)
- **Steps:** настроить `alembic.ini` и `services/api/alembic/env.py` + начальную миграцию `0001_initial_schema.py` для всех таблиц `store.py` (`upgrade` создаёт таблицы, `downgrade` удаляет). Добавить тест `test_migrations.py`, проверяющий программный вызов `upgrade` → `downgrade` → `upgrade` на временной SQLite БД.
- **Acceptance:** `upgrade head` → `downgrade base` → `upgrade head` на чистой БД проходит в тесте; все тесты `check.py` зелёные.
- **Verify:** `python -m unittest services/api/tests/test_migrations.py -v`, `python scripts/check.py`.

### T32 — Многопользовательская авторизация JWT + изоляция по `user_id`
- **Model:** Astra GPT 6 (или Argon) · **Status:** todo · **Depends on:** T31 · `[OPUS-REVIEW]`
- **Scope:** `services/api/vela/auth.py` (новый), `services/api/vela/main.py`, `services/api/vela/store.py`, `services/api/alembic/`, `services/api/tests/test_isolation.py` (новый), `apps/mobile/src/lib/api.ts`
- **Acceptance:** изоляция состояния по `user_id` (из проверенного JWT-токена или `DEMO_API_TOKEN` при `APP_ENV=local`); тесты в `test_isolation.py`: пользователь A не читает и не меняет данные пользователя B, подмена `user_id` в теле запроса игнорируется, истёкший/невалидный токен → `401`; `DEMO_API_TOKEN` работает только при `APP_ENV=local`.
- **Verify:** `python -m unittest services/api/tests/test_isolation.py -v`, `python scripts/check.py`.

### T33 — Durable worker + outbox для импорта
- **Model:** Astra GPT 6 (или Argon) · **Status:** todo · **Depends on:** T31
- **Scope:** `services/api/vela/worker.py` (новый), `services/api/vela/jobs.py` (новый), `services/api/vela/imports.py`, `services/api/vela/main.py`, `scripts/run-worker.py` (новый), `services/api/tests/test_worker.py` (новый)
- **Acceptance:** постановка импорта в очередь `POST /v1/imports/jobs` → `202` + `job_id`; статус `GET /v1/jobs/{id}`; ретраи с backoff, dead-letter, возврат зависших задач по `lease_until` (lease timeout); удаление данных (`DELETE /v1/data`) очищает задачи пользователя.
- **Verify:** `python -m unittest services/api/tests/test_worker.py -v`, `python scripts/check.py`.

### T34 — Приватное файловое хранилище (`storage.py`)
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-2 · `[PARALLEL-OK]`
- **Scope:** `services/api/vela/storage.py` (новый), `services/api/vela/main.py`, `services/api/tests/test_storage.py` (новый)
- **Steps:**
  1. Создать `services/api/vela/storage.py` (`PrivateStorage` с корневой папкой `.local/storage/` вне webroot):
     - `save_file(user_id: str, filename: str, data: bytes) -> StoredFile`: сохраняет файл в изолированную папку пользователя `.local/storage/<safe_user_id>/<file_id>`, считает и сохраняет контрольную сумму `sha256` в `.meta.json`. Запрещает path traversal (`..`, `/`, `\`).
     - `read_file(user_id: str, file_id: str) -> bytes`: читает файл и проверяет `sha256` (при несовпадении выбрасывает `ValueError("Integrity check failed")`).
     - `erase_user_files(user_id: str) -> None` и `erase_all() -> None`: полностью удаляет файлы с диска.
  2. Подключить `erase_all()` в `DELETE /v1/data` в `services/api/vela/main.py`.
  3. Написать `services/api/tests/test_storage.py`: сохранение, проверка `sha256`, ошибка при повреждении байтов на диске, защита от path traversal, полное удаление файлов при `DELETE /v1/data`.
- **Acceptance:** файлы хранятся в папке пользователя с проверкой `SHA-256` при чтении; `DELETE /v1/data` удаляет все файлы с диска (проверено тестом).
- **Verify:** `python -m unittest services/api/tests/test_storage.py -v`, `python scripts/check.py`.

### T35 — Структурные логи + X-Correlation-ID
- **Model:** Flash · **Status:** todo · **Depends on:** CHECKPOINT-2 · `[PARALLEL-OK]`
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
- **Model:** Astra GPT 6 (orchestrator) · **Status:** todo · **Depends on:** все выше
- **Steps:** полный прогон проверок; обновить `docs/release-readiness.md` по 4 уровням (`local demo` / `staging` / `pilot` / `public`); перечислить гейты, требующие подписи человека (финансовый, юридический и security-ревью, учётки сторов).

### CHECKPOINT-4 — Оркестратор: `Чекпоинт фазы 4`
