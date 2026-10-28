# MANUAL-05 — доступные проверки UI и backend

Дата: 2026-10-28. Исполнитель: Codex (GPT-6). Статус: проверка завершена в доступной среде; есть дефекты и непроверенные UI-ветки.
Исходная версия продукта: 4a4e598; checkpoint 30ee0f3 меняет только время eval-отчёта. Продуктовый код и зависимости не менялись.
Основание: docs/USER_MANUAL.md, docs/TEST_RUNBOOK.md, docs/testing/sample-statement.csv, MANUAL-02–04.
Среда: Windows, Chrome, Expo web; AI выключен. Релизные гейты и T-задачи не принимались.

## Главное

Доступный frontend отвечает HTTP 200; backend отвергает запрос без токена (401), с токеном возвращает 200 и CORS для http://localhost:8081. Полная web-сборка и typecheck проходят. Это подтверждает техническую возможность подключения, но не заменяет все UI-сценарии.

Реальные UI-проверки выполнены до отключения browser use: отмена допустимого плана, суммы, ошибки счетов, неполные данные. При продолжении инструмент вернул «Local browser use is disabled in Work settings». Ограничение не обходилось; оставшиеся проверки выполнены только на API и явно не засчитаны как UI PASS.

## Данные и сохранность

UI использовал отдельную .local/manual-04-20261028.db. Перед изменениями создан SQLite backup .local/manual-05-before.db, сохраняющий воспроизведение U06. Постоянная demo.db не изменялась.
В UI удалён тестовый Extra 80, затем отменён Planned 40. Итог: cash 1000, saved 0, buffer 100, bills 800, planned 0, free 100, одна запись Cancelled 40. Последний HTTP GET подтвердил эти значения, revision 9. Открытая форма Test bill 80 не сохранена; исправленная дата 2026-10-29.
Дополнительные API-пробы использовали временную отдельную SQLite с фиксированной датой 2026-10-28 и синтетическим токеном. Удаление проверялось только там.

## Новые фактические проверки UI

### U04 — PASS для отмены допустимого плана
После Remove Extra вернулись Mark done и Cancel step. Cancel step показал No active step и History Cancelled 40. Today: cash 1000, saved 0, bills 800, free 100. Последующий GET backend подтвердил отсутствие резерва.

### U07 — PARTIAL
Remove Extra 80 выполнен через UI; cash остался 1000, bills вернулись к 800. Полный независимый UI-прогон добавления и оплаты 80 не завершён. API-проверка оплаты и повтора успешна, но не закрывает UI.

### U16 — проверки отклонения PASS, UX FAIL
Choose amount: 12.34 и отдельно повторённые 12,34 дали goal 12.34 / still free 87.66. Попытки Add для -1, abc, 12.345 показали Enter an amount with up to two decimal places; состояние осталось cash 1000 / saved 0 / free 100, нового плана нет.
Add bill: имя Test bill; Save для 0 показал Enter an amount above zero; -1, abc, 12.345 отклонены. При amount 80 даты 2026-02-30 и 2026-12-01 отклонены, новых счетов нет.
После исправления даты на 2026-10-29 осталась ошибка предыдущего запроса: «1 validation error for Snapshot ... input_value=... input_type=dict ... errors.pydantic.dev». Это техническое сообщение вместо пользовательского текста. Close скрывает форму, но ошибка остаётся; повторное открытие сохраняет черновик. Выход Close без Save не записал Test bill — подтверждено GET backend.
Первый быстрый пакет проверок Check amount давал промежуточные снимки до ответа; выводы сделаны по отдельным повторным действиям и итоговым состояниям, а не по этим промежуточным снимкам.

### U17 — PASS (web)
All bills included выключено → Save → Quick check before planning и вопрос о счетах, обычной кнопки Add нет. Yes, all included возвращает предложение 20 и free 100.
Debts checked выключено → Save → вопрос о required debt payments. Yes, all included возвращает предложение 20 и free 100. Неизвестность долгов не считается их отсутствием.

## Дополнительные проверки API: 17/17 PASS

Команда: python .local/manual-05-probes.py. Exit 0; TOTAL 17 / 17. Машинный результат: .local/manual-05-probes.json. Временные данные изолированы от UI-базы.

1. Нет токена → 401.
2. Неверный токен → 401.
3. CORS preflight с Origin http://localhost:8081 → 200 с ожидаемым заголовком.
4. P0: breakdown cash 100000, saved 0, protected 10000, bills 80000, planned 0; available 10000 (центы).
5. Предоставленный sample-statement.csv → local parser, 3 операции, income 60000, spending 3500.
6. До применения CSV финансовое состояние полностью совпадает с исходным.
7. Keep existing: cash 100000, 3 операции.
8. Повторная загрузка/применение: cash 100000, 3 операции, spending 3500.
9. Синтетический broken.csv отклонён 422; состояние прежнее.
10. Planned 4000 + Extra 8000 → available -2000, can_complete false.
11. Попытка complete → 422.
12. API cancel при shortfall работает: available 2000, cash 100000, saved 0. Это локализует U06 в UI.
13. Оплата Extra с повтором того же Idempotency-Key: одинаковый ответ, cash 92000, available 2000, единственное списание.
14. Export: cash 92000, attachment header; тестовый токен и GEMINI_API_KEY отсутствуют. Не является проверкой механизма Share.
15. Пересоздание приложения с той же SQLite сохраняет полное финансовое состояние.
16. DELETE /v1/data → 200.
17. После нового запуска snapshot отсутствует, actions/debts пусты, transaction_count 0. Не является проверкой Cancel в UI-диалоге.

## Автоматические команды и фактический вывод

- python scripts/check.py: Ran 215 tests in 15.505s; OK. Полный вывод .local/manual-05-backend.log. Печатаемые FAIL внутри негативных eval-тестов ожидаемы при итоговом unittest OK. В оболочке после команды читался лог, поэтому итог берётся именно из unittest, а не только exit составной команды.
- apps/mobile: npm run typecheck → tsc --noEmit, exit 0.
- python scripts/generate-contracts.py --check → Contract check passed.
- python evals/run.py --offline → Summary: 60/60 PASS (100.0%) in 1.854s, exit 0.
- apps/mobile: npx --no-install expo export --platform web --output-dir ../../.local/manual-05-web-build → Web Bundled 6126ms (951 modules), 44 assets, 16 web bundles, Exported; exit 0. Это локальная сборка, не публикация.
- node scripts/check-mobile-syntax.cjs → MODULE_NOT_FOUND: ../.local/typescript/lib/typescript.js. Вспомогательный скрипт недоступен из-за отсутствующего локального пути; стандартный tsc и полная Expo-сборка проходят. Новые зависимости не устанавливались.
- python .local/manual-05-live.py → web HTTP 200; unauthenticated API HTTP 401; authenticated API HTTP 200, CORS http://localhost:8081. GET: cash 100000, saved 0, protected 10000, bills 80000, planned 0, available 10000, revision 9, cancelled 4000.

## Полнота U01–U22

- U01–U03: предыдущие UI-доказательства MANUAL-02/04 сохраняются; в этом прогоне добавлены HTTP auth/CORS и проверки дробных сумм. Старое замечание Choose amount не закрыто.
- U04: отмена допустимого плана дополнительно PASS через UI.
- U05: прежнее одиночное выполнение MANUAL-02; быстрый двойной клик не принят.
- U06: FAIL из MANUAL-04; Cancel step скрыт при shortfall, исправление не выполнялось.
- U07: UI PARTIAL; API оплата с повтором PASS.
- U08/U09: предыдущий UI PASS MANUAL-02; повторная проверка предоставленного CSV через API PASS.
- U10: предыдущий UI PASS MANUAL-02; новые ручные действия не выполнялись.
- U11: local проверен ранее и offline 60/60 сейчас; живой Gemini NOT RUN.
- U12: предыдущий UI PASS; дополнительное сохранение при пересоздании backend PASS.
- U13: ранее BLOCKED (нет перехода Learn; прямой web-route теряет подключение). Не исправлено, повторно UI не проверялся.
- U14: API export PASS; UI Share BLOCKED текущим запретом browser use.
- U15: API delete/restart PASS; UI Cancel/подтверждение BLOCKED.
- U16: отклонение проверенных значений PASS; UX FAIL из-за внутренней и устаревшей ошибки. Back со страницы Balance отдельно не проверялся; Close формы счёта проверен.
- U17: PASS web для обоих признаков полноты.
- U18: UI двойные клики NOT RUN; backend retry/concurrency покрыты тестами, оплата с retry проверена дополнительно.
- U19: NOT RUN на телефоне; отключение сети и восстановление интерфейса не проверены.
- U20: PARTIAL только Close без сохранения; маленький экран и нативная клавиатура NOT RUN.
- U21: NOT RUN — системный шрифт, темы, TalkBack/VoiceOver требуют доступного устройства/интерфейса.
- U22: повреждённый CSV на API PASS; видимость Reading statement и защита долгого импорта в UI NOT RUN.

## Дефекты и следующий шаг

1. Блокер U06: Cancel step должен оставаться доступным при can_complete=false; см. MANUAL-04 и apps/mobile/src/app/(tabs)/plan.tsx:65–76.
2. UX формы Add bill: внутренний текст ошибки Snapshot показывается пользователю и остаётся после исправления/закрытия. Нужна нормализация ошибки и управление её актуальностью.
3. Старые проблемы MANUAL-02: недоступность Learn, обратная связь Choose amount, недостаточность smoke для проверки полной сборки — не закрыты этим прогоном.
4. Вспомогательный check-mobile-syntax.cjs зависит от отсутствующего .local/typescript; стандартные проверки работают.

Для продолжения UI необходим доступ к управлению браузером; для U19–U21 — телефон/эмулятор с нужными возможностями. Техническая доступность backend подтверждена, полная приёмка UI не объявляется. Исправления кода в эту проверку не входили.
