# Durable statement imports — T33

2026-10-29. Backend/outbox implementation with synthetic SQLite/mocked-provider evidence, pending independent review. No live PostgreSQL/worker deployment/paid extraction or native UX claim. All verification uses `.venv/Scripts/python.exe`, isolated synthetic databases/files and no working API.

## Frontend contract

`POST /v1/imports/jobs`, with authenticated Bearer and `Idempotency-Key`, accepts JSON:

```json
{"filename":"statement.csv","content_type":"text/csv","content_base64":"<strict base64 bytes>","retention_consent":true,"processing":{"external_ai":false,"notice_version":"import-processing-v1"}}
```

Maximum decoded size is the existing parser's15MiB (base64 cap20971520 characters), below storage's16MiB cap. Retention consent must literally be boolean true, not1/string/null; external-AI choice must be an explicit boolean. The notice version identifies this processing-purpose contract and does not itself prove UI/legal acceptance. T52 must show the purpose and separate choices before submitting. No body owner, source URL or client-selected source ID is accepted.

Returns202 owner-scoped job status with `job_id`, `version`, `status`, `stage`, `attempts`, `next_attempt_at`, `result_preview_id`, safe `error`, `can_retry`, `can_cancel`, `status_url`. No raw bytes/filename/provider diagnostics/lease token/storage path enters status. Poll `GET /v1/jobs/{id}`; foreign/missing jobs404. A succeeded job links the unchanged `GET /v1/imports/{preview_id}` preview. Saving reviewed analytics remains the explicit `/v2/imports/{preview_id}/apply` command and never follows automatically.

`POST /v1/jobs/{id}/cancel` or `/retry` uses its own stable `Idempotency-Key` and `{ "version": <current job version> }`. The version is the job's version, not financial revision. Same command identity/payload replays its recorded response; changed/stale commands409. Cancel only active uploading/queued/running/retry_wait jobs; cancelled/succeeded jobs cannot retry. Explicit retry only failed/dead_letter with unchanged active source, resetting the operational attempt cycle; it preserves file ID and processing permission. No implicit cancelled-job/source resurrection.

Identical enqueue key/body returns the same job and creates no second original, including failed/cancelled jobs. Changed body409. A concurrent unique-key winner is reread after rollback and returned when fingerprint matches; other races yield a sanitized409 to retry the same request. Account deletion removes old jobs/generation; a later explicit enqueue is a new job/new generation/fresh random file, never revival of old source/job IDs.

## Outbox and source lifecycle

Revision0003 adds `import_generation` and `import_job` with unique owner+enqueue-key identity. The durable job row is the dispatch outbox; there is no Redis/in-memory dispatch/BackgroundTasks authority. The job records fingerprint, fresh UUID job/source ID, owner generation, permissions/parser version, lease/retry state and small command receipts. Bytes stay in T34 private storage; no source bytes/token are persisted in the job row.

Enqueue first commits the generation/job/source intent, then invokes T34 save with the internally preallocated fresh source UUID. T34 still persists its own pending/checksum/target metadata before provider put. Same-key retries do not re-upload. If a process dies after bytes become ready but before queue activation, an expired uploading lease can recover that same original. If upload never produced an active original, recovery fails explicitly without reupload/resurrection; the user must choose a new enqueue. Upload errors keep durable cleanup intent. Cancel/delete during upload cannot restore an old job.

Lifecycle: uploading→queued→running→succeeded; transient failure→retry_wait; invalid/unsupported source→failed; exhausted attempts→dead_letter; explicit cancel→cancelled. Default operational settings are lease120s, heartbeat30s, maximum3 attempts, backoff5×2^(attempt−1)s. `JobConfig`/CLI allow validated operational overrides. Claim uses conditional version updates and database row locks/skip-locked when supported; SQLite uses BEGIN IMMEDIATE. Old/expired lease tokens cannot renew/finish.

Success inserts the preview and marks the job succeeded in one transaction. It locks/rechecks owner generation, job lease/status and same-owner ready/unexpired/checksum-bound original metadata. Account erase deletes jobs and generation in the same transaction as financial entities before provider cleanup. A deleted owner's old worker cannot publish into a later enqueue/generation; original-only deletion/expiry also invalidates publication. Confirmed balances, allocations and imports are not applied by this worker.

Worker maintenance uses `JobRepository.cleanup()`, not unguarded `storage.cleanup()`: lock job then re-read/lock current metadata, skip a still-live uploading lease or now-ready unexpired source, and mark deletion intent atomically before external cleanup. A stale pending list cannot delete a source that completed meanwhile. This coordinates separate Store instances without holding a database transaction across provider delete I/O.

## Processing permission and reliability limits

Worker passes each persisted external-AI choice directly into `build_preview`; false blocks categorization, text fallback, raw PDF and image processing despite global AI flags. Existing raw-document global privacy restrictions still apply when per-call consent is true. Cloud synchronous `/v1/imports` and `/base64` have no explicit processing-consent contract, so they now parse locally only; local legacy mode keeps compatible behaviour/response shapes. No process-wide consent environment mutation occurs per job.

Heartbeat runs during async parsing. Cancellation/interruption leaves a durable lease for expiry recovery. Failure statuses store only safe error codes; CLI setup/claim/cleanup failures emit a generic message and nonzero exit rather than raw SQL/provider tracebacks. Argparse/help and process interruption semantics remain intact.

Exactly-once external AI billing is not promised after crash: parsing may be repeated after an expired lease when no successful preview exists. Durable success prevents another claim; no stored raw extraction cache is introduced. Full deleted-account generation/backup/restoration and deployment/real PostgreSQL concurrency remain independent T62/activation evidence. PostgreSQL constraint-mirroring index introspection is covered by an official-shape fixture, not a live database migration run.

## Explicit worker launch

No `.env` or default database is loaded. `--database-url`, `--mode`, and `--quota-dir` are required. Local mode also requires `--storage-root` matching the API's target; cloud requires trusted `--project-url`, `--bucket` and backend `SUPABASE_STORAGE_SERVICE_KEY`. The target binding must match T34 metadata. AI defaults disabled; `--enable-ai` is an operator opt-in in addition to per-job permission and existing provider credentials.

```powershell
.venv/Scripts/python.exe scripts/run-worker.py --database-url "sqlite:///C:/explicit/disposable/synthetic.db" --mode local --storage-root "C:/explicit/disposable/storage" --quota-dir "C:/explicit/disposable/quotas" --once
```

Without `--once`, the separate process polls with the configured backoff interval and retries maintenance cleanup. This is not an already-deployed scheduler. Never target demo.db or API8000–8003 as a fixture. No new dependency/driver/service is installed by T33.
