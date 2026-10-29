# T33 independent security/concurrency review — 2026-10-29

Verdict: **ACCEPT — bounded durable import worker/outbox after R1–R3 corrections.** This is a separate review context from T33's executor; only this report is reviewer-owned. Root owns canonical acceptance and combined integration.

## Scope and initial findings

Reviewed jobs.py, worker.py, run-worker.py, owner-data erase/new job tables in store.py, migration0003/version-aware env, internal storage file-ID seam, per-call AI permission in imports/main and current worker tests. No product source/status/git mutation, existing database/process, live cloud/AI or broad suite.

### R1 — cleanup must not cancel a live upload

The initial CLI loop invokes `storage.cleanup()` before claim. Existing cleanup treats every pending original as removable, while enqueue commits an uploading job and storage persists pending metadata before external put completes. A second worker can therefore delete a normal live-upload source before its upload lease expires, causing activation CAS to fail and compensating deletion. Requested a cross-Store-safe live-upload lease exclusion in maintenance plus event-coordinated pending-upload/worker-maintenance proof. This was source-confirmed before any reviewer runtime probe.

### R2 — accept only the required PostgreSQL unique-constraint mirror

Initial0003 validation rejects all `Inspector.get_indexes()` entries. PostgreSQL reports a UNIQUE constraint's implicit index there with `duplicates_constraint`, so the new owner/key constraint would make a valid migrated schema fail restart validation. [SQLAlchemy's PostgreSQL reflection documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#postgresql-index-reflection) directly confirms that representation. Requested narrowly allowing the exact unique owner/key constraint-mirroring index while retaining fail-closed unrelated-index checks, with a deterministic PostgreSQL-shaped inspector fixture. This does not substitute for real PostgreSQL migration/concurrency evidence under T70.

### R3 — sanitize the worker-process failure boundary

The initial CLI catches only KeyboardInterrupt. Cleanup/claim/startup exceptions outside the parser try can terminate with raw traceback/SQL/provider diagnostics in stderr, despite sanitized parser job-status errors. Requested a generic nonzero-exit CLI exception boundary without swallowing SystemExit/BaseException/cancellation, plus a negative private-diagnostic regression. No global logging redesign is required.

## Other reviewed boundaries

Enqueue uses owner-scoped unique key/fingerprint and durable uploading intent before external bytes. Missing bytes after process interruption fail explicitly rather than silently reuploading on the same key. Leased running jobs use conditional status/token/version and owner generation; final preview/status publication shares a database transaction and rechecks same-owner ready/unexpired source digest. Whole-owner erase removes jobs/generation before external file cleanup, so old completion cannot recreate a deleted owner's data. Cancel/stale leases and deleted/expired sources cannot publish. Exactly-once external-AI billing is not promised after crashes.

Cloud synchronous legacy imports explicitly disable AI egress without per-job permission; new jobs persist separate processing/retention consent. Local compatibility retains prior behaviour; no environment variable mutation per job. The internal file-ID seam validates identity and refuses reuse; status responses omit filename/raw source/lease token/provider details. CLI requires explicit DB/mode/storage/quota config and does not load a local .env or default to demo.db. Final independent worker/migration tests passed after explicit root source/docs freeze, as recorded below.


## Corrected-source review

**R1 resolved:** worker CLI now invokes `JobRepository.cleanup()`. Its transaction locks matching source jobs before current original metadata, skips live uploading leases, re-reads the source rather than trusting the initial listing, preserves ready/unexpired sources and marks eligible sources delete_pending before external deletion. Existing source IDs cannot later attach to another new job. The event-coordinated cross-Store pending-put test and stale-listed-pending→ready/queued test both pass. This fixes active-upload cancellation and stale maintenance snapshots without weakening explicit owner deletion/expiry.

**R2 resolved:**0003 allows only the exact named unique owner/key constraint's PostgreSQL index mirror, requiring matching unique flag, columns, name and duplicates_constraint. Its independent fixture accepts that official-shaped representation and rejects altered/unrelated indexes; other strict schema checks remain. No live PostgreSQL evidence is inferred from that fixture.

**R3 resolved:** the CLI entrypoint catches ordinary operational exceptions and returns1 with one generic stderr message; setup/claim/cleanup errors no longer print provider/SQL diagnostics. argparse/SystemExit and BaseException/cancellation are not broadly swallowed. Negative fixtures check setup, claim and cleanup private diagnostics. KeyboardInterrupt retains deliberate termination behaviour.

Concurrent enqueue uniqueness collisions now reread a matching owner/key/fingerprint winner after rollback instead of creating another source; changed/unresolved conflicts remain sanitized409. The initial source rows and raw documents are never embedded in job status. New default internal file IDs stay random, validated and nonreusable. Whole-owner deletion removes generation/jobs before external cleanup; lock/token/generation/source checks and transactional preview publication prevent stale/cancelled/deleted/expired completions. Per-job explicit AI permission reaches local-table categorization, unusual-layout fallback, PDF/text/raw and image branches; cloud legacy sync routes cannot bypass it.

## Actual independent verification

Root and executor explicitly confirmed final source/docs freeze before these two narrowly scoped commands:

```text
$env:PYTHONPATH='services/api'
.venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_worker.py -q
Ran20 tests in18.584s
OK
exit0

.venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_migrations.py -q
Ran10 tests in16.365s
OK
exit0
```

Commands ran as independent processes with new temporary synthetic SQLite/files and injected parser/provider/clock dependencies. Logs: ignored `.local/t33-independent-worker.txt`, `.local/t33-independent-migrations.txt`. Tests include real local worker `--once` subprocess with an explicit disposable DB/storage root, not any running API. Existing migration controls retain exact five-table raw payload/receipt/history preservation, add head0003 and exercise upgrade/downgrade/restart/rollback/unknown-schema refusal. Frozen0001/0002 were not edited by this task; unrelated full-backend/mobile/evals were not repeated by the reviewer.

Final reviewed SHA256:

- jobs.py: `829D5A34546F39C61B7765264DA438F919BE9E8EC14F798A990226C0F608A705`
- worker.py: `AE020E4400FDA19F33921214710DEFBBE3343C4CD216CCE02468C919046334C4`
- scripts/run-worker.py: `B0F0359A4079006DB08183A50BADB117DA0068CFAE59FDA74F8543183634DBE6`
-0003_import_jobs.py: `07718F7FDD4A9E5CEEBE4EAAF25439DB9E1FAAEF1523F82418FD23F7FF5CACA8`

## Acceptance limits

No remaining actionable defect found within this bounded implementation. Root still owns the combined full-backend and generated-contract gate and canonical task status. SQLite/file mocks demonstrate these transitions; actual PostgreSQL driver/server concurrent processes, provider/RLS/SMTP, complete export/restore, device/UI and paid-AI activation remain separate T70/T62/T63 evidence. Exactly-once external-AI billing after process loss is not promised; a reclaimed source can require parsing again. The guarded preview is analytical only and never applies balances, received income, reservations, debt or completion automatically. Processing notice presentation/UI remains integration work.

No reviewer product-source edit, status/git action, demo.db/API8000–8003 access, live provider/cloud/AI call, paid activation or existing process control occurred.
