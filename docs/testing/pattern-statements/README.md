# Three synthetic bank statements — ground truth before import

Created2026-10-29 solely for local Vela tests. All persons, merchants, payments and account activity are invented. EUR only, one current account, July–September2026; no bank branding or real identifiers. Do not treat these balances or spending patterns as advice. Source: deliberately authored test scenario, not a bank or AI output.

Exactly three CSVs,56 transactions: July16, August20, September20. Opening balanceEUR2000.00; month-end balancesEUR2727.02 /3384.04 /4198.06. Each running balance reconciles exactly. `expected.json` records amounts in integer cents, semantic transaction kinds and each source row; `SHA256SUMS.txt` freezes the uploaded files.

## Predetermined patterns

- Employer salary on the5th: EUR1500 in July/August, EUR1650 in September. Observed increase150, not a promise of future income.
- Rent600 on the1st, gym25 on the12th, cloud4.99 on the18th and fee3 on the28th every month.
- Streaming subscription9.99 in July/August,12.99 in September: observed price increase3.
- Four grocery purchases each month, total100/120/140. Same cafe5 per visit,2/4/6 visits, totals10/20/30. Do not infer waste, motivation or need to cancel a service.
- Own savings transfer100 out on the23rd and100 back on the24th each month. Net0, neither external income nor consumption. These are movements between owned accounts, not extra cash.
- August Shop Nova purchase60, then partial refund20, with matching REF-AUG-01. Net purchase40; refund is not salary/new external income.

## Exact semantic money expectations

July: external income1500, external debits772.98, refunds0, net spending772.98.
August: external income1500, external debits862.98, refunds20, net spending842.98.
September: external income1650, external debits835.98, refunds0, net spending835.98.
Total: external income4650, gross external debits2471.94, refunds20, net spending2451.94. Change in account balance2198.06, closing4198.06.

Incoming bank credits and semantic income differ in August. A UI showing1520 as income has counted the refund as income; record that gap rather than changing this oracle. Own transfers must be excluded from external spending/income.

## Repeatable UI exercise

Use a fresh isolated local test database with AI disabled. Enter a separate planning cash1000, saved0, buffer100, goal1000, no bills. The historical statements must not set current cash automatically. For each July/August/September CSV: choose file; verify row count/date/currency/closing balance/income/spending; select **Keep existing (EUR1000)**; inspect detected commitments and deselect all; Save. Expected cumulative rows16/36/56, current cash1000/saved0/bills0 throughout. Reimport the same September file: still56 rows and same finances.

Inspect recurring-payment, price-change, refund and income observations against the patterns above. Repetition exists across the files, not twice within an individual month; failure to combine history is a product gap. The current parser's keyword category is not confirmation of ownership/subscription. A56-row history also tests whether every transaction is reachable beyond a50-row latest-only list.

These tests do not cover HUF/FX, overlapping nonidentical statements, different account owners, raw-document consent, ambiguous duplicates, reminders or live AI. They require distinct fixtures and evidence. No result in this file is an observed app result; actual outcomes belong in reports/PATTERN-01.md.
