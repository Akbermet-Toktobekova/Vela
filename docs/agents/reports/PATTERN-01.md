# PATTERN-01 — Three statements with predetermined patterns

Status: review (test-fixture/verification slice, no product acceptance). Model: GPT-6.1 Sol. Date:2026-10-29. Owner requested2-3 bank statements, independently determine patterns first, then test the application with them. Starting product revision2be97c0 (UI-02).

## Delivered

Exactly three clearly synthetic EUR CSVs for July/August/September2026 in docs/testing/pattern-statements;16/20/20 transactions. expected.json is a predeclared oracle with integer cents and source-row semantics. README gives patterns, totals, limitations and repeatable UI instructions; SHA256SUMS freezes all three uploaded files. Authored using bundled spreadsheet runtime; no production dependencies or financial-policy changes. No personal data, bank branding or real account identifiers.

Ground truth was written and independently reconciled BEFORE any of these files were uploaded. Starting account2000.00; closing2727.02/3384.04/4198.06. External salary1500/1500/1650; gross external debits772.98/862.98/835.98; August refund20; own-transfer net0 in every month. Three-month income4650, gross debits2471.94, refund20, net spending2451.94, net account increase2198.06. All intermediate running balances reconcile.

Patterns fixed in advance: monthly rent600, gym25, cloud4.99, account fee3; salary on5th; streaming9.99/9.99/12.99 (observed increase3); grocery totals100/120/140; cafe visits2/4/6 at5 each; own-account100 out/back every month; August purchase60/refund20 sharing reference. These observations do not establish motive, unnecessary spending or future income certainty.

## Actual UI exercise

Windows, real Chrome extension, Expo58 development web8081, isolated API8001 with .local/pattern-01.db and separate token, Gemini disabled. Existing API8000 untouched. UI-02 test API stopped before reusing8001. Only synthetic records. No paid AI, real documents, cloud or native tests.

Direct /snapshot -> Connect with returnTo -> correct login returns snapshot, additionally verifying the repaired protected-route return. Via UI created baseline current cash1000/saved0/buffer100/goal1000/no bills. Uploaded July, August, September using the actual file chooser. Selected Keep existing1000 before each Apply; no recurring bills were suggested in any monthly preview. Reuploaded September and applied once more with Keep existing.

- PASS parsing/accounting: July16rows/income1500/spending772.98/closing2727.02; September20/income1650/spending835.98/closing4198.06. Row dates and amounts match oracle.
- SEMANTIC FAIL August: UI Total income1520 instead of external income1500 plus separate refund20. UI gross spending862.98 matches outgoing debits; it does not show net-of-refund842.98 or link the partial refund to its original purchase. History labels refund as income.
- PASS exact deduplication: stored row counts16 ->36 ->56 ->56 after repeatSeptember. No cash/income added by reimport when Keep existing selected.
- PASS known own-transfer example: six transfer rows categorized transfers, net0, excluded from external income/spending totals. Keyword classification does not prove general own-account recognition or matching.
- PASS guarded manual choice: current cash1000/saved0/obligations0 throughout. HOWEVER all three previews default to Update current cash with historical statement closing balance prefilled. This remains a revised-pilot contract violation risk; the test explicitly chose Keep existing and does NOT establish analytical-only import by default.
- GAP multi-file patterns: no recurring/subscription/price-change observation screen or suggestions appeared across the three separate month imports. Rent/gym/cloud/fee recurrence, salary change, grocery/cafe trends and streaming increase were not surfaced as persisted observations. Source inspection confirms current recurring detection receives only one uploaded file, not combined saved history. Absence of local analysis is not a test of live AI capability.
- GAP subscription categorization: named synthetic streaming/cloud subscription rows categorized other; gym classified subscriptions. Totals still reconcile; semantic identification is incomplete.
- GAP complete history: My Plan Imported transactions56 ->Show latest exposes50 transaction labels, no pagination/full-history control. Oldest six entries cannot be reviewed through that list. All56 are present in the read-only export.
- GAP Assistant analysis: request to identify recurring payments/price changes/refunds/own transfers gives the honest AI-disabled fallback with cash1000/bills0/free900, not pattern analysis. No live model called or accepted.

Latest Today summary is explicitly a30-day window ending at the latest imported date, not all three months. ItsSeptember1650/835.98 numbers match that window; do not mistake transaction_count56 for a three-month monetary total.

## Verification and evidence

Independent Python csv/Decimal validation before upload:56rows, all3 statements PASS, each intermediate balance checked, final419806cents. Post-UI read-only /v1/export comparison:56/56 unique source references match dates/integer amounts exactly; six own-transfer rows net0; refund category income; cash100000/saved0/obligations0. All fixture SHA256 checks PASS after import. No product-code change in this slice, so no redundant full backend/typecheck run; UI-02 same-code217tests/typecheck/contracts/full web export are separate preceding evidence.

Ignored local evidence: .local/pattern-01-browser.txt, pattern-01-export.json, pattern-01-result.png, API logs and retained pattern-01.db. Raw tokens omitted from committed records. The builder is local support, not a product dependency. Dedicated API stopped at end; test database/files preserved.

## Scope and next work

Scope limited to three source fixtures, independent expected-data manifest, documentation and comparison. No parser/AI/policy fixes. New inputs expose concrete requirements for T53/T54/T56/T59: refund linkage, cumulative evidence-based pattern observations, price changes, analytical-only import and full transaction review. This does not accept those tasks or the full user workflow. UI-02 navigation is repaired but v1 planning and v2 accounts remain separate. Export delivery, final deletion, native accessibility, HUF/FX, overlap/ambiguous duplicates and live AI remain outside this fixture run.
