---
trigger: always_on
---

# Vela team protocol (always on)

Before any work in this repository:

1. Read `AGENTS.md` (repo root) — canonical rules, roles, statuses, Definition of Done.
2. Read `docs/agents/HANDOFF.md` — current state, current orchestrator, next task.
3. If the user says `Выполни T<NN>` → follow skill `.agents/skills/vela-executor/SKILL.md`.
4. If the user says `Проверь T<NN>`, `Что дальше?`, `Чекпоинт фазы <N>` or `Прими роль оркестратора` → follow skill `.agents/skills/vela-orchestrator/SKILL.md`.

Never keep project state only in chat. Persist it in `docs/agents/` files.
Never fabricate command output. Never touch files outside the task `Scope`.
