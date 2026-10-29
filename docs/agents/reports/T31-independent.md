# T31 independent baseline migration review — 2026-10-29

**Verdict: ACCEPT for the SQLite baseline/adoption slice.** Independent delegated reviewer: Codex GPT-6. No material defect found within the frozen scope. Root owns integration, full suite, statuses and commits; T35 concurrent changes are excluded.

Reviewed alembic.ini, env.py, frozen0001 revision, store.py diff, all10 migration tests, migrations.md and T31 report against accepted T50 preservation boundaries.

## Evidence

Requested independent command: `$env:PYTHONPATH='services/api'; .venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_migrations.py -q`.

Actual result: **Ran10 tests in10.150s; OK; exit0.** No full backend/browser/eval run.

- Independent literal old DDL supplies both snapshot-only and expanded personal/planning fixtures. Exact complete row-tuple comparisons cover all five tables before/after adoption and bootstrap/read/receipt replay, including original JSON whitespace/Unicode, fingerprints, currencies/unknowns, goal.saved, completed steps, source links and histories. No runtime metadata or reserialization manufactures the comparison oracle.
- Bootstrap replaces create_all with a frozen Alembic revision. Existing compatible rows are not updated; only version bookkeeping is added. Version/table/type/nullability/ordered PK/default/constraint/index/view/trigger mismatches reject before adoption. Unknown revisions retain original version and schema. Negative tests cover structural variants and unchanged rows/schema.
- SQLite BEGIN IMMEDIATE occurs before introspection/version DDL; existing external transactions are respected. Injected interruption after the second create_table rolls back all initial DDL; retry succeeds. Store disposes its engine on initialization failure. Process-local lock protects Alembic module proxies; the three-thread bootstrap test preserves original rows. Cross-process contention is supported by the inspected SQLite lock mechanism but was not independently stress-tested here.
- Populated downgrade checks all five tables before dropping anything and rejects without explicit disposable override. The test proves unchanged rows/schema on refusal and destructive cycle only on its fresh temporary fixture. Empty upgrade/downgrade/upgrade passes. The override is an explicit operator assertion, not automatic detection of disposable data, and documentation does not advertise it for user-data rollback.
- CLI requires an explicit database_url or caller connection, rejects offline adoption and has no .env/default database fallback. Actual CLI subprocess regression verifies missing URL failure and explicit disposable upgrade/downgrade/upgrade.
- Old receipt replay does not invoke apply/render; post-migration new command/restart/retry preserves revision8 and avoids duplicate effects. Existing normal mutation logic is unchanged by this slice.

Scoped git diff --check: exit0; only existing store.py LF/CRLF normalization warning. No code/schema/API change performed by reviewer.

## Exact verified source SHA256

- env.py: 9A1F2A8FA901068898ABB564D9BEDC1E213F81C52C48A3A5ADB2AE0DF6E4A806
- versions/0001_initial_schema.py: B0A2F6C6FCA2C7E9C695143298357CDBBA1C315789048EF1EFFF253911E8ABE2
- store.py: A9D3C160C0138A74B9E6FE1C1EFB2D7AD7DD683E72EB2085448B3FB618CB5716
- test_migrations.py: 69AFEF2A1F8AF9F8B6B21978035CE9E3F380636A9D0FD13D3E1A15DDA4CC2709

## Limits

Accepted baseline is deliberately strict and recognizes only0001. A later additive revision must extend env-level version-aware validation without rewriting this frozen baseline; current code is not a promise that future schema versions already work. PostgreSQL, multi-host/cloud ownership and restoration of external jobs/files remain separate tasks. A populated working downgrade is not accepted recovery; compatible isolated copy/export proof remains required. Only new TemporaryDirectory databases were exercised; no demo.db, ports8000–8003, real data/cloud/paid/deploy action. No unresolved blocker for this bounded T31 acceptance.
