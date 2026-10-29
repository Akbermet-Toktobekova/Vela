# Private originals — T34

2026-10-29. This is a durable storage adapter/lifecycle slice, subject to independent security review. T33 owns resumable raw import/job integration; existing synchronous import routes do not silently retain originals. No live provider, RLS, PostgreSQL, backup or full account-deletion-generation claim follows from mocked tests.

## Consent and private identity

`PrivateStorage.save_file(owner, filename, bytes, retention_consent=True)` requires explicit30-day retention consent before metadata or bytes are written. Default/missing consent rejects. Retention is separate from purpose-specific external-AI processing consent; a retained file is not blanket permission to send it to a model. T33 must collect and enforce that separate permission.

The server uses verified owner identity, never a body owner/path. The service generates a random32-hex file ID and derives a SHA256-owner-prefix/object ID. Filenames are validated against traversal/control characters but are neither persisted nor used in object paths or logs. Local files live outside webroot. Owner/file-ID validation and durable owner predicates prevent cross-owner access; no public or signed-download URLs are generated. SHA256 verifies bytes and size at each read; it is not encryption.

## Durable metadata and migration

`0002_private_originals` adds owner-keyed `private_original` metadata alongside the existing five tables: owner/file_id, backend, opaque object_key, SHA256, byte size, creation/expiry UTC epoch seconds and lifecycle status (`pending`, `ready`, `delete_pending`). Consent is required to create a row; no filename/token is stored. Original metadata intentionally survives financial-state erase while bytes still need physical cleanup. Confirmed analytical rows have a separate lifecycle and deleting an original does not delete them.

The frozen0001 migration is unchanged. Alembic environment chooses version-specific frozen validation for0002, preserves fail-closed unknown-schema checks, and retains exact baseline rows/payloads. Populated original-metadata downgrade refuses without the existing explicit disposable-test flag. All migration tests remain; their expected current head is now0002.

## Adapters and configuration

The metadata `backend` value binds each original to a nonsecret target fingerprint: resolved local root, or Supabase origin plus bucket. Changing roots/buckets/origins cannot turn a404 from the wrong target into successful deletion of metadata for old bytes. A mismatch denies access, retains deletion intent and requires the original target to be restored/reconciled; backend credential rotation alone does not change target identity.

Local mode uses `LocalObjects` under the isolated local directory's `storage/`. Paths use only hashed owner/UUID components, reject symlink escapes and verify checksums. Cloud mode uses `SupabaseObjects` with the trusted project's HTTPS origin, `SUPABASE_STORAGE_BUCKET` and backend-only `SUPABASE_STORAGE_SERVICE_KEY`. Never send the backend key to mobile, output, export or logs. With both storage settings absent, cloud storage is explicitly unavailable; it never falls back to local disk. A partial/invalid configuration fails startup. T70 owns reviewed bucket/service configuration and activation.

Provider wire contract follows [Supabase Storage reference](https://supabase.com/docs/reference/self-hosting-storage/v1/upload-a-new-object): private-bucket metadata check, authenticated object retrieval, new-object upload without upsert and object deletion. Every read/upload verifies the configured bucket currently has `public=false`; retrieval uses `/storage/v1/object/authenticated/...`, never public/signing routes. Backend credentials remain server-side; application owner checks are required even though the service credential bypasses provider RLS. Real bucket/RLS/service-key isolation and provider backups are unrun activation evidence, not proven by `MockTransport`.

Requests use existing httpx with bounded five-second phase timeouts, no redirects/ambient proxies, and16MiB input/response size limits. Provider error details are replaced by generic availability errors. A metadata tombstone written before upload preserves cleanup intent if the provider writes bytes but the response is lost.

## Expiration, cleanup and deletion

Originals expire exactly30days after upload. Reads require `ready` and `now < expires_at`; pending/deleting/exact-expiry originals deny access before provider I/O regardless of physical cleanup failures. Internal `cleanup()` retries all nonready/expired records. T33's worker must schedule that hook; this module alone is not an autonomous scheduler. Actual original-byte deletion removes metadata only after provider/local deletion succeeds.

`erase_file(owner,id)` and `erase_user_files(owner)` leave durable `delete_pending` records when physical deletion fails. Their bytes are then inaccessible. Restart can retry cleanup without restoring financial state. The developer-only `erase_all(disposable=True)` is restricted to explicitly disposable local fixtures and has no public API.

An upload activates only via `pending→ready` compare-and-set. If another Store/process deletes the pending metadata during external upload, the saver refuses success, restores durable cleanup intent before compensating deletion, and preserves that intent if compensation fails. This prevents the demonstrated false-ready/orphan-retry loss. Deletion may finish before in-flight provider upload finishes, so later compensation can still leave pending cleanup after an earlier delete response. Full account-generation/in-flight worker/restore semantics require T33/T62; no immediate globally complete physical erasure is promised here.

## HTTP boundary

- `GET /v2/originals/{file_id}`: authenticated bytes only; fixed attachment filename, octet-stream and `Cache-Control:no-store`. Foreign/missing/expired/invalid originals404; provider unavailable503. Checksums never get bypassed by a URL.
- `DELETE /v2/originals/{file_id}`: authenticated own file only;200 `status:deleted`,202 `status:deletion_pending`, foreign/missing404.
- `DELETE /v1/data`: financial state/receipts/previews/runs/publications are erased as before. Own originals are denied and deletion attempted. If bytes remain,202 `status:deletion_pending` plus pending count and explicit scope; retry can finish cleanup. Normal no-pending200 remains compatible. These status distinctions must be retained in future UI/T62 rather than treating every2xx as proof of complete physical deletion.

No raw upload API is added by T34. T33 calls the storage service with collected retention permission, retains file ID and checksum, and must verify active file/expiry/owner again atomically before committing derived job results. File IDs never reuse; originals cannot make money or silently complete actions.

## Deterministic verification

Frontend ingest/idempotency is deliberately deferred to T33's atomic upload-and-enqueue command. The service always generates fresh random file IDs; it has no deterministic-key ID reuse. A briefly considered standalone upload endpoint was withdrawn before verification/freeze because durable retry receipts and deleted-source guarantees belong to the job lifecycle. Existing read/delete endpoints alone are not a complete frontend upload workflow.

Use `.venv/Scripts/python.exe` (PowerShell activation optional: `. .\.venv\Scripts\Activate.ps1`). Focused tests cover consent, durable SHA256/restart/tampering, traversal, exact expiry, failed/lost upload response, physical deletion/retry, cross-Store blocked-upload/deletion coordination, migration preservation/downgrade safety and A/B JWT API isolation. Provider calls are mocked; no secret/live cloud or working database is needed. Root runs the final shared backend gate after source freezes.
