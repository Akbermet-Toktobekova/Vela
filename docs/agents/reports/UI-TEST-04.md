# UI-TEST-04 — T71 browser continuation

Date: 2026-10-29. Model: GPT-6.1 Sol. Status: partial verification; T71 remains review.
Build: a7cb37d, clean working tree at start. Windows, real Chrome extension browser, localhost:8081/personal, local API on 8000. No AI/cloud calls, dependencies or product-code changes.

## Scope and environment

Continued the interrupted T71 browser test. Entry: Connect -> Your Today. Exit: saved account with verified balance and income count after reload/reconnect. Existing explicitly synthetic account UI verification 2026-10-29 was the only financial record targeted. Initial EUR1000, income count 0. Existing local API was retained, not restarted; its database path was not independently established in this run. This was NOT a fresh isolated database. No deletion/export or legacy money commands were exercised. Expo was stopped initially (ERR_CONNECTION_REFUSED); started existing Expo CLI on 8081 with logs in .local/ui-continue-web*.log. Token excluded from this report.

## Observed UI results

- PASS: Update balance 950.25 -> Today EUR950.25, income count still 0. Replacement did not create income.
- PASS: Add income 49,75, No — add it -> EUR1000.00, count 1. Comma decimal accepted.
- PASS: Add income 20, Yes — record only -> EUR1000.00, count 2.
- PASS: Add income 30, Not sure — enter current balance, balance 1100 -> EUR1100.00, count 3. No extra 30 added to replacement balance.
- PASS: Save without selecting mode preserves draft and asks Choose an account and how this income affects your balance.
- PASS: With No — add it selected, 12.345 and -1 rejected with Enter an amount with up to two decimal places. Draft stays visible.
- PASS: Correct to 5 clears error. Back to Today without Save, reload, reconnect -> EUR1100.00 and count 3. Unsaved/invalid input did not create records.
- PASS with known limitation: reload requires Connect again. Re-entering existing local connection credentials restores EUR1100.00 and 3 income records. This proves browser reconnect persistence, not cloud session restoration or a fresh server restart.

## Product/UX gaps observed

- Add income shows account/currency/current amount but omits current balance confirmation date; target acceptance explicitly requires balance/date.
- Add income has no received-date or optional label field. Update balance has no date field. Historical-date entry remains unavailable in this UI; backend date capability does not prove UI coverage.
- Negative amount error mentions decimal precision rather than explaining that a negative income is invalid.

These are findings only; no fixes authorized/performed in this validation slice. Persisted test account deliberately retained at EUR1100.00 with 3 income records.

## Evidence and limits

Screenshot: .local/ui-test-04-result.png (ignored local evidence), final Chrome screen with account/date/balance/count. Real interaction evidence recorded above; no native/owner acceptance implied.
Not run: HUF/unknown-account UI, network loss, concurrent revisions, rapid double-submit/idempotent retry, Android/iPhone keyboard, large system font, screen reader, dark theme, remaining legacy U-scenarios. Earlier T71 server restart result remains separate historical evidence.

Commands: git status --short -> clean; git log -1 --oneline -> a7cb37d T71: record partial browser and server restart persistence proof. Pre-task git add -A / git commit -> nothing to commit, working tree clean (exit 1). No backend/TS/contract rerun: no product code changed. Post-task diff check and commit recorded by the session.

Next bounded verification: HUF/unknown balance UI and retry/conflict, then native accessibility when a device is available. Independent T71 acceptance remains pending.
