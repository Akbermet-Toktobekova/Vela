# T53a independent source review —2026-10-31

Reviewer: cloud-config recovery context, not the T53a executor. **Final verdict: conditional ACCEPT of the corrected source; root's basic API smoke/acceptance remains separate.** Initial R1 finding and its source-only correction are preserved below. No independent test collection was run: the owner narrowed verification to basic-data operation while this review was in progress. Executor-reported15 reconciliation tests in9.347s and ParserTests6 in0.055s are cited as executor evidence only, not independently reproduced results; they precede the final R1 follow-up.

## R1 — dependent duplicate decision survives a material correction

Source-confirmed, not a runtime-probe claim. In reconciliation.py, create() marks a repeated in-file bank-reference row unresolved and offers the preceding source row as a link candidate. resolve() can explicitly link that later row to the preceding source. correct() subsequently recalculates only the edited row's decision and its own preceding-reference relationship. It does not invalidate/revalidate later rows linked to that edited source. apply_review() resolves such a source link through prior.applied_id without checking whether the linked rows' current effective date/amount still support that decision.

Concrete sequence: create two same-reference rows with the same date/amount; explicitly link the second to the first; correct the **first** amount or date; apply. The second retains its prior resolved link although the original matching basis now conflicts. Its parsed original remains stored, but its separate analytical amount can be suppressed by a stale reconciliation choice. The existing correction regression covers editing the repeated second row, not editing a row on which another explicit decision depends.

Expected bounded correction: when an edited source materially changes a linked decision's basis, invalidate/revalidate the dependent decision and require explicit resolution, or reject applying incompatible stale source links. Preserve original facts and decision/correction history. A single targeted/basic API sequence is sufficient to prove this case; no broader collection is requested by this review.

### Source-only re-review after correction

The executor froze the bounded follow-up. Independent inspection confirms correct() now invalidates dependent sibling source links, clears their selected target, retains the previous link in decision history and offers the source again only when the current date/amount match. apply_review() independently rejects in-review source links whose current date/amount/currency differ, including stale records saved before the invalidation fix. Parsed originals and prior correction/decision history remain unchanged. This addresses the reported source path. No post-fix runtime result or repeated collection is claimed; the parent owns the owner's requested basic-data smoke and final canonical status.

## Positive source findings

- Amounts use strict integer bounds; imported source values remain separate from effective fields and append-only correction/decision history. Method/checksum/account/parsed-ordinal identity preserves same-content purchase multiplicity. Category correction records manual provenance without rewriting originals.
- Same-owner account/currency checks precede review creation; HUF stays in the canonical ledger and never enters EUR-only State.transactions. Apply changes analytical state/history/revision, not personal balances, received-income records or planning allocations.
- Guarded Store.mutate enters the transaction before receipt replay; legacy v1/v2 apply uses the current owner aggregate, including alias previews, and fails after canonical activation. SQLite write serialization and PostgreSQL row-lock intent are explicit. Actual PostgreSQL execution is not established here.
- Job-backed mutations check succeeded owner job/current generation/result-preview identity and source checksum while holding the transaction. Parsed review reads do not require original bytes to remain available after original expiry. Deleted previews/jobs cannot replay guarded mutation receipts.
- Domain legacy StateView excludes the internal aggregate; export preserves State. Source/documentation distinguish parsed ordinal from physical file line, unsupported currencies, pre-application corrections, legacy account association and unfinished T53b/UI/lifecycle work.

Reviewed reconciliation.py, relevant domain/imports/main/store changes, focused test source, docs/product/reconciliation.md and reports/T53a.md after the explicit freeze. Only this report was written. No product/status/git changes, demo.db/API8000–8003 access, provider/AI/cloud calls or full/backend/worker test runs.
