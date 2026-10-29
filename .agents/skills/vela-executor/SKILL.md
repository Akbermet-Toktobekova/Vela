---
name: vela-executor
description: Execute exactly one Vela backlog task (T<NN>) as Gemini Flash 3.8, Astra GPT 6, or Gemini 4 Argon. Use when the user says "Выполни T<NN>" or asks to implement a backlog item. Covers scope control, verification, report writing and escalation.
---

# Vela executor — выполнение одной задачи

## Шаг 0. Проверка роли
- Найди задачу `T<NN>` в `docs/agents/BACKLOG.md`. Сверь поле `Model` со своей моделью.
  - Задача для Heavy-модели (`Astra GPT 6` / `Argon`), а ты `Flash` → **не выполняй**. Ответь: «Эта задача для Astra GPT 6 / Argon, переключи модель».
  - Задача для `Flash`, а ты `Astra GPT 6` или `Argon` → можно выполнять (Heavy-модели — резерв Flash).
  - Задачи `Astra GPT 6` и `Argon` взаимозаменяемы (Astra GPT 6 заменяет Argon при нехватке кредитов).
- Проверь `Depends on`: все зависимости должны быть `done`. Иначе остановись и сообщи пользователю.
- Статус должен быть `todo`, `rework` или `escalated`. Если `rework`, сначала прочитай замечания в `docs/agents/reports/T<NN>.md` (раздел `Review`).

## Шаг 1. Старт
1. Поставь статус задачи `in_progress` в BACKLOG.
2. Обнови `docs/agents/HANDOFF.md`: `Current task: T<NN> (in_progress, <модель>)`.
3. Если репозиторий уже под git: `git status` должен быть чистым. Если нет, закоммить чужие изменения отдельно: `git add -A; git commit -m "wip: before T<NN>"`.
4. Прочитай файлы из `Context` и `Scope`. Читай только нужное.

## Шаг 2. Работа
- Меняй только файлы из `Scope`. Новые файлы создавай только внутри указанных путей.
- Сначала тест/фикстура из `Acceptance`, потом реализация (для логики).
- Финансы: только целые центы, без `float`, без новых правил «от себя».
- Для мелкого фикса используй `surgical-patch`, для новой фичи `lean-build`, для схемы/БД `migration`.
- Нужно выйти за scope, добавить зависимость или решить продуктовый вопрос → статус `blocked`, вопрос в отчёте, стоп.

## Шаг 3. Проверка
Запусти **все** команды из `Verify` задачи и базовые проверки из `AGENTS.md` §6. Сохрани реальный вывод (хвост, итоговые строки).
Если проверка красная, чини. Flash: не больше 2 попыток, потом `escalated`.

## Шаг 4. Отчёт и сдача
1. Создай/обнови `docs/agents/reports/T<NN>.md` по шаблону `docs/agents/reports/_TEMPLATE.md`.
2. Поставь статус `review` (или `blocked` / `escalated`) в BACKLOG.
3. Обнови `docs/agents/HANDOFF.md`: текущая задача, статус, следующий шаг: «Оркестратор: `Проверь T<NN>`».
4. Коммит (если есть git): `git add -A; git commit -m "T<NN>: <кратко>"`.
5. Ответ пользователю, 3–5 строк: статус, что сделано, итоги проверок, какую модель включить дальше.

## Запрещено
- Менять статус на `done`.
- Править `PROGRESS.md` и `docs/release-readiness.md` (это делает оркестратор), если задача прямо этого не требует.
- Выполнять больше одной задачи за сессию.
- Писать в отчёт результаты команд, которые не запускались.

## Approved pilot revision
Read docs/product/PILOT_SPEC.md for revised behaviour. UI work must use uxpeak and shared design-system tokens. Review the complete user journey, not only module existence; distinguish automated, real-device and owner acceptance. The owner may explicitly authorize sequential bounded tasks in one session; record each separately.
