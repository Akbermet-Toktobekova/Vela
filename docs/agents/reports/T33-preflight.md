# T33 implementation preflight —2026-10-29

Specification only; start after independent T34 acceptance. Sources: T33/data-contract/PILOT_SPEC and current imports/store/auth/migrations. No code, dependency, git/status or cloud mutation. Scoped diff check passes.

## Ownership / implementation sequence

1. `jobs.py`: SQLAlchemy durable job repository + request/status schemas + authenticated route installer. Job row can itself serve as transactional dispatch outbox; enqueue and request fingerprint/unique owner+idempotency key commit together. No Redis/BackgroundTasks/in-memory dispatch. `worker.py`: claim/heartbeat/process/finish once with injected clock/parser/storage; separate `scripts/run-worker.py` requires explicit DB/mode/storage, supports `--once`, handles termination. Never default to demo.db or implicitly load .env.
2. `imports.py`: reuse `build_preview`, file_type and existing limits. Add per-call external-AI permission covering every fallback/categorization/raw-document branch; current global enabled()/ALLOW_RAW_DOCUMENT_AI is not per-owner consent. Do not change environment per job. Worker produces a deterministic job-linked ImportPreview only; no apply/balance/reservation writes.
3. Expand authorized scope to `store.py`, `alembic/versions/0003_import_jobs.py`, version-aware validator, docs/product/jobs.md and generated contracts. Confirm actual T34 head/name first; preserve0001/0002. Store needs common-transaction preview publication and erase/jobs/generation coordination; independently committing save_preview is insufficient. Preserve old JSON/legacy guards/storage rows.

## Durable invariants

Job stores owner/job_id, fingerprint/key, file ID/checksum/storage generation, owner input generation, parser/options version, consent purpose/notice/choice, UTC times, status/stage, attempts/next_attempt_at, lease_until/token, result preview ID and safe error code. Never bytes/tokens/raw provider errors in job logs/status. Unique DB constraints handle concurrent enqueue. PostgreSQL claim uses lock/skip-locked or CAS; SQLite tests use conditional updates. Old/expired lease cannot renew/finish after another claim. queued→running→succeeded; transient→retry_wait; permanent→failed; exhausted→dead_letter; explicit cancel→cancelled. Infrastructure lease/backoff/attempt policy is explicit validated configuration, without financial thresholds.

Create owner generation guard on first enqueue. Whole-owner deletion removes guard+jobs in the same data transaction; subsequent enqueue creates fresh generation, so old job/generation/lease cannot publish. No permanent identity tombstone needed. Final publication atomically checks live job/lease/generation AND same-owner active unexpired file metadata (T34 API still pending). Original-only deletion/expiry also invalidates results. Publish preview and success together; preserve originals/confirmed balances. External AI billing cannot be promised exactly once after a crash; reuse persisted extraction when available and report this limit.

## Proposed frontend contract (root approval before implementation)

- `POST /v1/imports/jobs`, Idempotency-Key, JSON `{file_id,processing:{external_ai,notice_version}}` →202 `{job_id,status,stage,status_url}`. Require accepted T34 retention consent and separately authorized external processing; never arbitrary source URLs/body owner. Same fingerprint returns same job; changed fingerprint409. Original must already exist durably; no raw bytes in job rows.
- `GET /v1/jobs/{id}` → owner-scoped `{job_id,status,stage,attempts,next_attempt_at,can_retry,can_cancel,result_preview_id,error}`; foreign/missing404. No lease token, storage URL or fabricated progress percentage. Success links existing `/v1/imports/{preview_id}`; apply stays analytics-only `/v2/imports/{id}/apply`.
- `POST /v1/jobs/{id}/retry` and `/cancel`, stable command key + expected job version. Retry only eligible failures with unchanged/live file+consent; no silent cancelled/deleted/succeeded resurrection. Preserve existing synchronous import response shapes. Listing/cross-device discovery requires explicit extra scope.

## Proof / remaining facts

Focused test_worker: enqueue/retry identity; restart; competing claims/expired lease/stale finish; backoff/dead-letter/permanent errors; AI consent even with global AI enabled; atomic one-preview publication; deleted/expired-file and delete-A-versus-running-worker/same-owner-reenqueue races; A/B isolation. Inject clocks/parser/storage, synthetic SQLite only, no sleep/network/paid AI. Migration preserves existing baseline+T34 records, populated destructive downgrade refused. Root centralizes full backend/contracts.

Need final accepted T34 metadata API/consent notice versions and explicit infrastructure defaults or required CLI config. No declared PostgreSQL driver currently: root must authorize declaration when actual PostgreSQL execution enters scope; SQLite mocks are not PostgreSQL concurrency/deployment proof. No new financial decision is needed. T70 activation/T62 restoration remain separate. demo.db/API8000–8003 untouched.
