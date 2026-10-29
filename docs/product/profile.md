# Persisted optional profile — T51

The additive `PersonalState.profile_details` aggregate persists optional discovery inputs without creating balances, received income, goals, debt or confirmed obligations. Existing `personal.focus` and `personal.income_type` remain the only copies of those selectors. Missing `profile_details` in older JSON is accepted as unknown; reads do not rewrite the stored payload. No SQL table/migration is required for this aggregate expansion.

## Installation and owner boundary

Root registers `install_profile(app, store, owner, idempotency, clock)` from `vela.profile` after existing personal routes. The installer reuses the verified owner dependency and current Store revision/idempotency transaction. It does not accept a user ID or another owner's account reference. Parent owns main.py registration, generated OpenAPI/types and full integration evidence.

- GET `/v2/profile/details`: current shared revision, focus, income type, details, per-field freshness and `as_of` server date. Read only; a new owner need not create a profile record.
- PUT `/v2/profile/details`: update or clear explicitly provided focus, income type and/or income estimate. Carries shared `revision`, `preference_version`, `income_input_version` and manual fact evidence.
- PUT `/v2/profile/preferences`: replace/clear explicit preference and restriction text with shared `revision`, current `preference_version` and manual fact evidence.
- PUT `/v2/profile/onboarding`: save current step and explicitly skipped steps with shared `revision`; no financial fields or input versions change.

All writes carry the caller's stable `Idempotency-Key`. Exact body/key replay returns the historical receipt once without another version/effect; changed body/same key or stale shared/input version returns409. Refresh after conflict before reconfirming. Profile views returned by a replay remain historical receipt views, not an assertion of current facts.

## Income expectations and unknowns

An income estimate contains either `amount_minor` or both `minimum_minor` and `maximum_minor`, each an integer from0 through the JS exact safe-integer bound. The minimum cannot exceed the maximum; exact and ranged representations cannot be supplied together. A monetary value requires an explicit EUR/HUF currency. `null` means unknown; zero is an explicit stated zero. Clearing `income_estimate:null` removes the estimate rather than creating a zero-income event.

Optional `frequency` is a nonempty bounded user label and `next_expected_on` is a calendar date. This task stores those stated inputs but interprets no frequency, probability or income-certainty weights. A future or overdue expectation is never a received event and cannot increase any account balance or affordability. T54 owns scenario calculations. Income type can remain unknown even while another optional profile field is filled.

Example PUT `/v2/profile/details` body:

```json
{
  "revision": 0,
  "preference_version": 0,
  "income_input_version": 0,
  "income_type": "mixed",
  "income_estimate": {
    "minimum_minor": 100000,
    "maximum_minor": 180000,
    "currency": "EUR",
    "frequency": "monthly",
    "next_expected_on": "2026-11-15"
  },
  "fact": {"source": "manual", "source_date": "2026-10-25", "confirmed": true}
}
```

## Evidence, freshness and independent versions

Manual fact evidence explicitly provides `source_date` and `confirmed`. A source date cannot be after the server's current date. The server records `recorded_on`; `confirmed_on` is set to the current date only when explicitly confirmed. Historical selectors without metadata are projected as legacy/unconfirmed with no invented dates. Freshness exposes source date, recording/confirmation dates and elapsed `age_days`; no guessed staleness threshold marks an input usable or unusable.

`preference_version` tracks focus/preferences/restrictions and their evidence. `income_input_version` tracks income type/expectation and their evidence. A preferences-only write does not claim changed income or received money. These are scoped profile-input versions, not a claim that all account/debt/goal financial inputs are already governed by a global financial version; T56/T57 own that wider immutable input bundle. Shared Store `revision` remains the command concurrency boundary. Reconfirming evidence on another day changes its appropriate input version; an unchanged read does not.

Preferences/restrictions are explicit user text, never inferred psychological traits, scoring weights or executable policy. Unknown (`null`) differs from an explicitly empty list. Entries are bounded for storage and cannot silently define financial actions or safety thresholds. Future specialists must treat them as untrusted input and still obey financial hard constraints.

## Resume and legacy compatibility

Onboarding stores a current `focus`, `accounts`, `income`, `obligations` or `complete` step plus explicitly skipped steps and server update date. It can be resumed after process restart without requiring a statement or goal. Completing onboarding only sets the existing onboarding marker; no hidden balance, goal, complete-obligations or debt-known default is manufactured.

Existing PUT `/v2/profile` retains its accepted body/behaviour. If it changes a selector after detailed facts exist, it increments the corresponding scoped input version and replaces that selector's confirmation metadata with dated manual/unconfirmed evidence. Thus old→new→old commands cannot keep a contradictory previously confirmed selector. Same-body receipt retries never repeat those effects. The legacy endpoint still marks its old onboarding flag as before; the new detailed `onboarding` resume object is the T52 source for the new path.

The new reader accepts old JSON and preserves raw payload bytes on reads/restart. An actual new profile write additively reserializes the owner aggregate while retaining financial values, original source rows, amounts/currencies, dates, actions and old history. Old strict binaries may reject the expanded optional field after a write: rollback requires a preserved copy and a compatible application/schema pair, not a destructive working-data downgrade. T62 owns full restore evidence.

## Evidence and limits

`test_profile.py` uses new disposable SQLite databases and an installer-level A/B owner seam. It proves optional unknowns, exact integer/range validation, no expected-income cash effect, explicit zero, source/freshness/confirmation, separate versions, conflicts/receipts, old→new→old consistency, skip/resume, restart and legacy read/write preservation. JWT verification is independently covered by T32; this seam is not a second authentication implementation.

No live cloud, account migration/upload, mobile screen, new dependency, financial weight, SQL change or use of working demo.db/API8000–8003 is part of T51. Main registration/contracts/full backend/independent acceptance are root integration gates; native/user journeys remain T52/T63.
