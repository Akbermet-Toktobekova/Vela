# MANUAL-04 — продолжение ручного теста

Дата: 2026-10-28. Модель: GPT-6. Статус: U06 FAIL.
Версия: 2916825. Среда: Windows, Chrome, web, AI local fallback.
База: .local/manual-04-20261028.db (отдельная, создана этим запуском).

## Действия и факты

Прежний localhost:8081 отвечал ERR_CONNECTION_REFUSED. Запущен python scripts/start-dev.py --web с DATABASE_URL отдельной базы. Backend authenticated state check passed; READY API + Expo; реально открыт Connect Vela и выполнено подключение.

Через интерфейс создан P0: Test User, cash 1000, buffer 100, Test reserve target 1000/saved 0, horizon 2026-11-27; Rent 600/2026-11-04, Living 150/2026-11-11, Required debt payment 50/2026-11-18. Today: bills 800, free 100.

Change amount → 40 → Check amount: goal after 40, still free 60. Add to my plan: Planned 40, присутствуют Mark done и Cancel step.
My Plan → Add bill: Extra 80, 2026-10-29, other → Save bill.
Today: cash 1000, saved 0, buffer 100, bills 880, planned 40, free -20 — PASS.
My Plan: Mark done отсутствует, виден текст «Your snapshot needs confirmation or free funds dropped below this amount. Check Today first.» — блокировка PASS.
Но Cancel step также отсутствует. Возврат Today → My Plan подтверждает проблему. Финальный шаг U06 (отменить резерв, получить free 20) невыполним — FAIL.

## Локализация

apps/mobile/src/app/(tabs)/plan.tsx:65–76: Cancel step находится в разрешённой ветке action.can_complete вместе с Mark done. Нужен отдельный фикс, сохраняющий возможность отмены недоступного к выполнению шага.

## Проверки и ограничения

git status --short: пусто перед началом. git add -A / git commit перед тестом: nothing to commit, working tree clean.
UI-доказательство получено деревом доступности Chrome. Попытка screenshot завершилась Page.captureScreenshot timeout 5000ms; снимок не получен.
Автоматические тесты повторно не запускались; исходники и зависимости не менялись. Остальные U-сценарии этим отчётом не принимаются. База и вкладка сохранены для продолжения; launcher оставлен работающим.

## Вопросы и следующий шаг

Исправить расположение Cancel step и повторить U06 на сохранённой базе; затем U07. Релизные статусы не менялись.
