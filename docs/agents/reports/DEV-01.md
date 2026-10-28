# DEV-01 — Удобный локальный запуск

- **Status:** review (самоприёмка не выполнялась).
- **Date:** 2026-10-28.
- **Model:** Codex, текущая сессия.
- **Request:** пользователь просит скрипт запуска Expo и backend для ручной проверки UI и функций, удобный также агенту.

## Что сделано

`scripts/start-dev.py` использует существующий `run-api.py` и установленный Expo CLI. `start-vela.cmd` — запуск двойным щелчком/из PowerShell с выбором `.venv`, если она существует. Флаги: `--web`, `--dev-client`, `--lan-ip`, `--ai`, `--check`, `--smoke`.

Проверка зависимостей и занятых IPv4/IPv6 портов, авторизованная проверка `/v1/state`, ожидание Metro `/status`, остановка своих process trees при ошибке/Ctrl+C/smoke. Существующая `.env` сохраняется, новый токен создаётся только существующим setup-local при отсутствии файла. Данные не сбрасываются. Токен записан в игнорируемый `.local/dev-connection.txt`, не выводится в tool output и не передаётся через EXPO_PUBLIC. Gemini выключен по умолчанию для дочернего API; включается явно `--ai`.

## Файлы

- `scripts/start-dev.py`, `start-vela.cmd`, `docs/local-testing.md` — новые.
- `PRODUCT_PLAN.md`, `docs/agents/HANDOFF.md` — ссылка на запуск.
- `docs/agents/BACKLOG.md` — отдельная карточка DEV-01.
- Этот отчёт.

## Проверки

- `python scripts/start-dev.py --check`: exit 0, `PASS: Python/backend imports, Node, installed Expo CLI, ports 8000/8081.`
- Первый `--smoke`: обнаружен timeout проверки Metro через 127.0.0.1. Независимые HTTP-пробы: 127.0.0.1:8081 refused; localhost:8081/status → 200, `packager-status:running`. Проверка исправлена на localhost, дополнена проверкой IPv6-порта.
- Повторный `--smoke`: exit 0, `PASS: authenticated API and Expo /status. Stopping smoke session.`
- После smoke повторный `--check`: exit 0; оба порта освобождены.
- Обычный `start-vela.cmd` запущен в отдельном интерактивном терминале для пользователя. Независимые HTTP-проверки `/health` и Metro `/status`: `PASS: interactive Expo and API are running`. Сервисы намеренно оставлены для ручной проверки; останавливаются Ctrl+C в этом терминале.
- Целевая проверка занятого случайного порта: `PASS: occupied port rejected without stopping its owner`.
- Неверный `--lan-ip`: exit 2, `PASS: invalid LAN IP rejected`.
- `python scripts/check.py`: exit 0. Вывод тестов включает ожидаемые FAIL отдельных искусственно неверных eval-сценариев; итоговый unittest runner завершился успешно. Количество не переписано из старого отчёта.
- `git diff --check`: exit 0 перед добавлением документации.

## Отклонения, риски и вопросы

Новых зависимостей, изменений API/mobile/финансового кода нет. Не выполнялись сброс БД, импорт настоящих выписок, внешние вызовы Gemini, установка пакетов или деплой. Smoke подтверждает готовность сервисов, не все экраны и не совместимость Expo Go на конкретном телефоне. Web CORS требует адрес localhost:8081; при другом сетевом адаптере пользователь задаёт --lan-ip. Закрытие терминала крестиком не обещает контролируемую очистку — использовать Ctrl+C.

Независимое ревью DEV-01 можно выполнить отдельно. Основная очередь T24b остаётся без изменения статуса.
