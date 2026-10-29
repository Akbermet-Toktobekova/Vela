# Local /v2 personal-data slice

2026-10-29. This is an initial local integration, not completed T30/T50/T31 or cloud pilot.

Open /personal or connect to the local API. Preview welcome also links to saved data. Current local token authentication remains single-user. Web refresh requires reconnecting (credentials intentionally not persisted by the legacy web connector); server data remains. Native connector restores from SecureStore.

GET /v2/personal; PUT /v2/profile; POST /v2/accounts; PUT /v2/accounts/{id}/balance; POST /v2/income. Writes require expected shared revision and Idempotency-Key. A retry with the identical key/payload returns the original result. Conflicts preserve entry; refresh before resubmission. Local dates use device timezone; backend rejects future dates.

Accounts use integer hundredths of EUR or HUF. No conversion or cross-currency total yet. Unknown balance is null. Income add requires a known balance and must not predate its confirmation. Included income leaves balance unchanged. Replace records a current-balance confirmation. Profile contains focus/income type and onboarding marker. No mandatory goal or statement.

Storage expansion: personal is a typed field inside the existing state JSON; old JSON loads with an empty PersonalState. Existing snapshot/actions/transactions are untouched. Global revision invalidates stale v1 commands too. Export includes personal; erase removes the complete owner state and receipts. No cloud transfer, new tables, Alembic dependency or real document handling introduced.

Rollback boundary: older binaries reject the new personal field after a v2 write. Do not downgrade a populated database in place. Preserve a complete export/copy and use a compatibility-aware migration in T31/T50 before any cloud rollout. This slice provides forward compatibility of old data, not a proven zero-loss old-binary downgrade. No existing records are rewritten on startup.

Pending: cloud OTP and owner isolation via JWT, full migration/rollback, monetary action pipeline, goals/debts, persistent chat, analytic import, FX, reminder scheduling and native shortcut. Until then Today shows known accounts and a clarification rather than a fabricated recommendation.

## UI-02 navigation follow-up — 2026-10-29
Saved accounts now link to the existing planning workspace, settings/data and Learn. Planning/settings link back. Protected deep routes retain their allowed destination through Connect. The planning workspace still uses a separate manually entered EUR snapshot; v2 accounts/incomes are not copied or summed into it. Navigation repair is not shared-model integration. See reports/UI-02.md for actual browser results and remaining export/double-confirm findings.

## T72 analytical statements — 2026-10-29
The import screen now applies through /v2/imports/{id}/apply: historical entries only, no balance/default goal/bill/action writes. /v2/observations and /observations show cumulative suggested evidence and full paginated history. Labelled refunds are separate from earnings; imported future credits do not fund a plan. Original /v1 import apply remains legacy-compatible and is not the revised analytical-only contract. Existing v2 accounts and legacy planning still require a separate canonical-model migration. New refunds enum is not old-binary-readable; preserve a copy/export and do not downgrade a populated DB in place. See reports/T72.md for tests and actual Chrome evidence.


## T74 canonical local account plan — 2026-10-29
/v2/planning reads one explicitly selected EUR account; cash is never mirrored into the old snapshot. Shared-plan and shared-assistant use these same facts. Optional single goal, protected amount, confirmed bills/debt coverage and fresh balance gate money steps. Acceptance reserves; completion records earmarking; bill payment separately confirms subtract versus already reflected. Lower actual balance retains allocations and blocks unsafe steps. No account reassignment/FX/multi-goal support in this slice.
Legacy adoption requires matching freshly confirmed balances and explicit review. Original snapshot/actions/history remain exportable. After activation, legacy money writers reject changes; /v1/state returns an empty legacy financial projection with guidance to the shared plan, not historical cash as current facts. Legacy preview/decision/evaluate/chat return409 directing callers to /v2/planning. Lessons use current shared-plan context. Before activation old behaviour remains compatible. This is a local deterministic explanation, not persistent AI chat or stored recommendation ID/version resolution. Preserve export/database before rollback; older binaries cannot safely read expanded personal.planning JSON.
