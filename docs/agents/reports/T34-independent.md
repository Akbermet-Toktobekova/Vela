# T34 independent security review — 2026-10-29

Verdict: **ACCEPT — bounded private-original adapter, HTTP boundary and SQLite migration**, after R1 target-binding correction. Reviewer is the delegated T32-session/T51 implementation context, not T34's executor. Parent owns canonical status and combined integration acceptance.

## Review scope

storage.py; original metadata methods in store.py; frozen0002 migration/version-aware env; T34 main factory/read/delete integration; storage and migration tests; storage lifecycle documentation. No T51 implementation is self-reviewed here.

## R1 — storage target binding (reported before freeze, corrected in source)

Initial metadata recorded only the generic backend name. Reusing the metadata database after changing a local root or Supabase origin/bucket could let deletion inspect the wrong target, receive missing/404 and erase durable cleanup metadata while bytes remained at the original target. Reported this concrete source gap to root/executor before tests or acceptance.

Current correction records a nonsecret target fingerprint in the existing backend field: resolved local-root hash, or Supabase origin+bucket hash. Reads/deletion compare that fingerprint before provider/file I/O. A target mismatch refuses access, marks deletion pending and retains durable metadata; restoring the original target permits retry. Service-key rotation does not alter the target fingerprint. Executor added changed-root and origin/bucket/key-rotation controls. The final independent16 storage tests passed, including changed-root cleanup preservation and origin/bucket/key-rotation identity controls.

## Source findings and bounded guarantees

Owner comes from the shared verified dependency, not request data. File identity uses hashed owner/random file ID; no original filename enters object paths, metadata, output or diagnostics. Private bucket checks precede remote upload/read; backend-only credentials are confined to httpx headers with HTTPS/no redirects/ambient proxies. Fixed download name/no-store responses and generic unavailable/missing responses avoid provider/detail leakage. Consent is explicit before metadata or byte write;30-day expiry denies reads before provider I/O. Exact bytes/size/SHA256 are verified; SHA256 is not claimed as encryption.

Pending/delete-pending metadata survives financial erase and restart. Upload activation is a pending-only CAS; a separate Store deleting during upload prevents success and restores cleanup intent before compensating deletion. The documented process-level limitation remains: remote upload completion can race earlier delete acknowledgement, and a crash/in-flight job needs T33/T62 generation/restore evidence. Do not infer instant globally complete physical erasure or autonomous cleanup scheduling from this adapter.

Frozen0001 remains unchanged.0002 adds only original metadata; version-specific validation checks all old five tables plus the additive table and refuses mismatches/unknown versions. Populated downgrade remains refused absent an explicit disposable flag. The independent10 migration tests passed after freeze, preserving exact original five-table rows, safe downgrade/rollback/restart behaviour and fail-closed validation.

## Protocol check

Read official [Supabase Storage server single-object delete route](https://github.com/supabase/storage/blob/master/src/http/routes/object/deleteObject.ts) and [authenticated route registration](https://github.com/supabase/storage/blob/master/src/http/routes/object/index.ts): DELETE `/:bucketName/*` is supported. The SDK's separate batch remove endpoint does not invalidate this single-object path. No live provider/storage call was made.

## Independent verification

Root and executor explicitly confirmed final source/docs freeze before these commands:

```text
$env:PYTHONPATH='services/api'
.venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_storage.py -q
Ran16 tests in3.274s
OK
exit0

.venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_migrations.py -q
Ran10 tests in25.687s
OK
exit0
```

Each command ran independently on newly allocated temporary SQLite/filesystem fixtures; the two independent processes were batched to avoid serial waiting. Captured logs: ignored `.local/t34-independent-storage.txt` and `.local/t34-independent-migrations.txt`. No repeated global backend suite was run.

Storage controls directly execute consent-before-write, checksum corruption, owner scope/traversal, exact expiry before provider read, cleanup failure/restart retry, lost upload response, event-coordinated second-Store deletion while upload is blocked, target mismatch and restoration, populated-original downgrade refusal, API202 pending deletion/retry, mock private-bucket/authenticated wire, verified synthetic A/B JWT route access, and cloud unavailable/partial-config no-local-fallback. Migration controls preserve all old raw financial JSON/receipts/previews/runs/publications and cycle the new head on disposable data. Frozen0001 source diff remained empty. The sole existing migration assertion update is the justified current head0002; original migration tests were retained.

Final reviewed SHA256:

- storage.py: `B20D5C651BC82AC8E05D090EFE0870CCF7D619BE2D570EDF560DB9B6724E0FD9`
- store.py: `2BCA5C5899582B5B7D79B5BC996D3A13898BCAE693E061A54D88FCEC64E40205`
- alembic/env.py: `EA4DA1A91A99170157AD74CEA16EC22C7EB970AE74E7DB3473940D7240DF8A7E`
-0002_private_originals.py: `BFDFCAFDE55091A8B1239B863722873CB04AD18A9F6F1A0355FD31A3DC266C89`
- test_storage.py: `0FBD5CB939A47B31ABE7D25E242632F0B94A6CE1728A08FE00A4A0A0344AD4C3`

No remaining actionable defect found within the bounded adapter/migration scope. Root must retain explicit202 deletion status semantics and finish T33 durable upload/job integration plus T62 account-generation/crash/restore evidence. This acceptance is not proof of live Supabase/RLS/PostgreSQL, automatic cleanup scheduling, complete J01–J12, immediate provider-wide physical erasure or production readiness.

No full-backend run, product-source edit, shared-status change, git action, demo.db/ports8000–8003 access, live cloud request or paid activation by this reviewer.
