# MANUAL-03 — дополнительные проверки и runbook

Дата: 2026-10-28. Модель: GPT-6 Astra. Статус: частичная проверка, инструкция готова.

## Фактические результаты

- `python scripts/generate-contracts.py --check`: Contract check passed, exit 0.
- `python evals/run.py --offline`: 60/60 PASS, exit 0, 0.973 s. Отчёт evals/reports/latest.json обновлён запуском.
- Из services/api: `python -m unittest discover -s tests -p test_journeys.py -v`: 31 tests in 5.096s, OK, exit 0. Покрывает среди прочего shortfall, paid/remove bill, concurrency, retry, import errors и delete на тестовых базах.
- Первый запуск unittest из корня завершился ModuleNotFoundError: vela; исправлена рабочая директория, продуктовый код не менялся.
- Launcher web с отдельной `.local/manual-03-20261028-1430.db`: backend ready, Web Bundled 3496ms (1004 modules), открыт Connect Vela.

## Что не принято

Дополнительные ручные U06/U07/U14–U22 в этой сессии не выполнены. Автоматические тесты не закрывают их UI-критерии. Живой Gemini и телефон не запускались. Предыдущие U04/U05 не доказывают отмену плана или быстрый двойной клик — эти ветки явно выделены в runbook.

## Артефакты и продолжение

`docs/TEST_RUNBOOK.md`: воспроизводимый запуск новой базы, команды автоматических проверок, отдельные ветки U04/U06/U07/U14–U22, ожидаемые суммы и формат отчёта. Следующий ручной прогон начать с P0 и U06. Исходники и зависимости не менялись; релизные статусы не повышались.
