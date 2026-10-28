# MANUAL-02 — ручной web-прогон USER_MANUAL

- Дата: 2026-10-28
- Среда: Windows, Expo web `http://localhost:8081`, local fallback без Gemini
- Данные: изолированная SQLite `.local/manual-u01-u22-20261028.db`; постоянная `.local/demo.db` не изменялась
- Реализация продукта: не менялась

## Итог

Фактически пройдены 10 сценариев: U01–U05, U08–U12 (U11 только local). U13 заблокирован пользовательской навигацией. U06, U07 и U14–U22 в этой сессии не принимались.

| ID | Статус | Фактический результат |
|---|---|---|
| U01 | PASS (web/local) | Неверный токен оставил пользователя на Connect с отказом; корректный открыл Today. |
| U02 | PASS | P0 сохранён через UI: cash €1 000, buffer €100, bills €800, free €100, предложение €20. |
| U03 | PASS с UX-замечанием | €150 не сохранились; €40 дали goal €40 / still free €60; preview не изменил состояние. После редактирования проверенных €40 на €150 preview исчез, но кнопка Add кратко осталась активной; сервер отклонил запрос и деньги не изменились. Ошибка появилась только после нажатия и не очистилась после следующей успешной проверки. |
| U04 | PASS | Planned €40: cash €1 000, saved €0, planned €40, free €60. |
| U05 | PASS | Back не выполнил шаг; Confirm done дал saved €40, cash €1 000, free €60, 4%, history Completed. Повторная кнопка выполнения отсутствует. |
| U06 | NOT RUN | Нужна отдельная ветка до Confirm done. |
| U07 | NOT RUN | Нужна отдельная чистая ветка P0 без completed action. |
| U08 | PASS | Preview: 3 transactions, income €600, spending €35, Local parser. Keep existing сохранил cash €1 000; после Save — 3 rows. |
| U09 | PASS | Повторный импорт того же CSV оставил 3 rows, income €600, spending €35. |
| U10 | PASS | Долг €100, APR 0%, min €50: baseline/Avalanche/Snowball = 2 mo, interest €0. Preview one-off €25 не изменил debt balance €100. |
| U11 | PASS (local); AI NOT RUN | Local fallback подтвердил free €60, не принял €5 000, отказался заявлять перевод и давать совет по акциям; state не изменился. Gemini не включался. |
| U12 | PASS (web) | После полного перезапуска и после Disconnect/reconnect сохранились cash €1 000, saved €40, bills €800, 3 transactions и debt €100. |
| U13 | BLOCKED | Из Today/My Plan/Assistant нет перехода к Learn. Прямой `/learn` после полной web-навигации остаётся на Loading из-за утраты in-memory подключения и не возвращает к Connect. |
| U14–U22 | NOT RUN | Экспорт/удаление, отдельные ветки ошибок, телефон, малый экран и accessibility не принимались. |

## Запуск и проверки

- `python scripts/start-dev.py --check` → PASS.
- `python scripts/start-dev.py --smoke` → PASS для authenticated API и Expo `/status`.
- Первый реальный web bundle упал: отсутствовал уже зафиксированный в lockfile optional package `lightningcss-win32-x64-msvc`.
- `npm ci` → восстановлены 551 package по существующему lockfile; исходники/lockfile не изменились. npm сообщил 9 известных audit findings (5 low, 4 high); `npm audit fix` не запускался.
- После восстановления полный web bundle → PASS, 1019 modules.
- `cd apps/mobile; npm run typecheck` → exit 0.
- `python scripts/check.py` → 215 tests, OK, exit 0. Печатавшиеся FAIL-примеры внутри негативных regression-тестов ожидаемы; итог unittest — OK.

## Найденные проблемы

1. Smoke launcher даёт PASS до полной web-сборки и не поймал отсутствующий native optional module; готовность `/status` не доказывает готовность web UI.
2. На Choose amount кнопка Add to my plan не отключается сразу после изменения ранее проверенной суммы. Backend сохраняет инвариант, но UI допускает бессмысленную отправку и показывает запоздалую/устаревшую ошибку.
3. Learn недоступен из обычной навигации; прямой web-route в неподключённом состоянии зависает на Loading вместо возврата к Connect.

## Ограничения приёмки

Телефон, Gemini, экспорт, удаление и U06/U07/U14–U22 не проверялись. Этот прогон не закрывает J01–J12, T24b, CHECKPOINT-2 или release readiness.
