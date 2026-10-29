# Local /v2 personal-data slice

2026-10-29. This is an initial local integration, not completed T30/T50/T31 or cloud pilot.

Open /personal or connect to the local API. Preview welcome also links to saved data. Current local token authentication remains single-user. Web refresh requires reconnecting (credentials intentionally not persisted by the legacy web connector); server data remains. Native connector restores from SecureStore.

GET /v2/personal; PUT /v2/profile; POST /v2/accounts; PUT /v2/accounts/{id}/balance; POST /v2/income. Writes require expected shared revision and Idempotency-Key. A retry with the identical key/payload returns the original result. Conflicts preserve entry; refresh before resubmission. Local dates use device timezone; backend rejects future dates.

Accounts use integer hundredths of EUR or HUF. No conversion or cross-currency total yet. Unknown balance is null. Income add requires a known balance and must not predate its confirmation. Included income leaves balance unchanged. Replace records a current-balance confirmation. Profile contains focus/income type and onboarding marker. No mandatory goal or statement.

Storage expansion: personal is a typed field inside the existing state JSON; old JSON loads with an empty PersonalState. Existing snapshot/actions/transactions are untouched. Global revision invalidates stale v1 commands too. Export includes personal; erase removes the complete owner state and receipts. No cloud transfer, new tables, Alembic dependency or real document handling introduced.

Rollback boundary: older binaries reject the new personal field after a v2 write. Do not downgrade a populated database in place. Preserve a complete export/copy and use a compatibility-aware migration in T31/T50 before any cloud rollout. This slice provides forward compatibility of old data, not a proven zero-loss old-binary downgrade. No existing records are rewritten on startup.

Pending: cloud OTP and owner isolation via JWT, full migration/rollback, monetary action pipeline, goals/debts, persistent chat, analytic import, FX, reminder scheduling and native shortcut. Until then Today shows known accounts and a clarification rather than a fabricated recommendation.
