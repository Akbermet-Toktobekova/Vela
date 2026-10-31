# Statement review and analytical reconciliation — T53a

Backend slice,2026-10-31. This is an analytical workflow; no command changes account balances, received income, bills, debt, savings allocations or action completion. Source originals remain subject to T34 retention, while parsed provenance is separate. T53b manual-event/own-transfer evidence links and mobile review screens are not implemented here.

## Frontend commands

- `POST /v2/imports/{preview_id}/review`: body `{revision, account_id}`, authenticated owner and stable Idempotency-Key. Account must belong to that owner and match the statement currency. Returns the saved review, shared revision, review version, unresolved count and anchor difference. Job-backed previews require a succeeded current-owner job/generation and matching source checksum; a client cannot supply another owner's source metadata.
- `GET /v2/reviews/{review_id}?offset=0&limit=100`: read-only owner-scoped review, up to200 rows per page. `total_rows` describes the full source; unresolved count and anchor difference cover all rows. GET does not create State or alter financial facts.
- `PUT /v2/reviews/{review_id}/rows/{source_id}`: body `{revision, review_version, reason, date?, amount?, category?}`. Validates exact integer minor units, allowed category/date and a nonempty reason; null edits are rejected. Applies only before review application and appends correction history. Original parsed values stay immutable; manual category correction has explicit method provenance.
- `POST /v2/reviews/{review_id}/rows/{source_id}/resolve`: body `{revision, review_version, decision:"new"|"link", linked_id?}`. Explicitly keep a distinct purchase or choose an offered owned candidate. Repeated bank references within the file remain unresolved until this separate choice; correcting another field does not silently resolve them.
- `POST /v2/reviews/{review_id}/apply`: body `{revision, review_version}`. A separate idempotent command atomically adds/links reviewed analytical rows. Unsupported currency, unresolved ambiguity, changed versions or stale/deleted preview/job reject without partial writes. Original-file expiry/deletion alone does not erase parsed facts or block their review.

Every write uses shared revision plus review version where applicable and a stable command key. Identical retry replays its response only while its source guard still passes; changed command fingerprints409. A deleted preview/job cannot bypass the guard through a cached receipt. Read a fresh review after conflict instead of inventing a new revision.

## Provenance, duplicates and currencies

Source identity contains checksum, account, parser/method version and parsed ordinal. This ordinal identifies the parsed result, not a physical raw-file line. Parser/model/version and category method remain recorded with the review. Method changes do not silently reuse an old ordinal identity. Source bytes are not embedded in State.

Correcting a row invalidates any sibling duplicate decision linked to that row and retains the previous link in decision history. Application also revalidates within-review linked date, amount and currency, so a stale saved decision cannot suppress now-conflicting source evidence.

Equal purchases without proof of identity remain separate source rows; they are not collapsed by date/amount/description. An exact same-source retry links existing provenance once. A consistent stable bank reference within the same account/currency can link existing analytical evidence. Conflicting references or similarity without a stable identity require explicit resolution. Legacy EUR rows can be offered as ambiguous candidates; the chosen review account is an explicit association, not retroactive proof of their original account or confirmation.

The reconciliation ledger owns reviewed data; legacy `State.transactions` is its compatible EUR projection. HUF rows remain explicitly HUF and never enter EUR-only summary totals. Once an owner has any canonical review/ledger, both legacy apply endpoints return409 for all preview IDs, including cached old receipts and alias uploads. This owner transition is checked inside the mutation transaction before receipt replay. Noncanonical legacy users retain their original import path.

`anchor_difference = opening_balance + sum(effective source-row amounts) - closing_balance`, when both historical anchors are present. This reports source-row evidence, not current cash or permission to replace a balance. It includes source rows before ledger deduplication; it is not a bank-certified reconstructed balance. Missing anchors remain unknown. Booking status absent from the source remains unknown, not automatically booked.

## Proof and boundaries

Synthetic fixtures preserve both EUR2000 purchases, source retries, explicit overlapping-source decisions and a corrected EUR2500 purchase retaining original EUR2000. Opening10000 + income5000 − purchase2000 − purchase2000 − transfer3000 = closing8000; changing the second purchase by−500 leaves anchor difference−500. Confirmed account cash100000 and the one included manual-income event remain unchanged.

Acceptance commands: targeted `test_import_reconciliation.py` and `test_journeys.ParserTests` under project `.venv`. Full backend/contracts and independent acceptance belong to the orchestrator. No new dependency, SQL migration, live model/provider, deployment, working demo.db or API8000–8003 is required. Export/read compatibility and advanced post-application corrections, evidence linking, complete lifecycle/restore and real UI journeys remain separately scoped work.
