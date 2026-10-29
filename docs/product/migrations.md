# Store baseline migrations

2026-10-29, T31. This is SQLite baseline/preservation proof, not a cloud migration or PostgreSQL acceptance. Contract: [ADR0007](../adr/0007-product-data-contract.md) and [product-data-v1](data-contract.md). Never use working `demo.db` or API8000–8003 as migration fixtures.

## Environment and connection

Alembic is pinned to1.20.1 in `services/api/requirements.txt`; its [official tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) describes the versioned environment and upgrade/downgrade workflow. This task installs only Alembic and its missing transitive Mako dependency into the ignored project `.venv`, created with `--system-site-packages`. No global installation, database driver, cloud credentials or `.env` loading is involved.

Use `.venv/Scripts/python.exe` for checks and application launch after this change. Other project dependencies remain available through existing system site packages. A fresh development environment should install the declared requirements into its own virtual environment.

Optional PowerShell activation: `. .\.venv\Scripts\Activate.ps1`. The explicit `.venv/Scripts/python.exe` commands below work without activation or changes to execution policy.

CLI intentionally has no default URL: pass `-x database_url=...`. An existing SQLAlchemy connection may instead be supplied through `Config.attributes['connection']`. No environment fallback can accidentally select a working database. Offline SQL generation is rejected because safe legacy adoption needs introspection.

Example on a **new, empty, disposable** synthetic file from the repository root:

```powershell
$taskMigrationDir = Join-Path (Get-Location) ('.local/t31-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskMigrationDir | Out-Null
$taskMigrationUrl = 'sqlite:///' + (Join-Path $taskMigrationDir 'synthetic.db').Replace('\', '/')
.venv/Scripts/python.exe -m alembic -c services/api/alembic.ini -x "database_url=$taskMigrationUrl" upgrade head
.venv/Scripts/python.exe -m alembic -c services/api/alembic.ini -x "database_url=$taskMigrationUrl" current
```

## Baseline and adoption

Revision `0001_initial_schema` freezes the existing `demo_state`, `command_receipt`, `import_preview`, `coordination_run` and `published_recommendation` definitions. It uses explicit `op.create_table` declarations, never current runtime `metadata.create_all` or JSON deserialization/backfill.

`Store` runs the migration bootstrap before any reads/writes. An empty database receives the five tables plus Alembic version bookkeeping. A complete, compatible unversioned database is structurally validated and versioned without rewriting a single existing row. Existing JSON whitespace, Unicode, unknown values, money/dates/provenance/history and receipt fingerprints remain byte-equivalent. Naming `demo_state` is retained for compatibility; this task does not reassign ownership or introduce cloud entities.

Unknown tables/views/triggers/revisions, incomplete tables, unexpected columns/types/nullability/keys/defaults/constraints/indexes fail closed before migration writes. Repair is not guessed; retain a preserved copy and investigate with the matching schema/application version. A future additive migration must supply its own version-specific validation; do not edit the frozen baseline to redefine historical schema.

Bootstrap commands are serialized inside a process because Alembic uses global execution proxies. SQLite starts `BEGIN IMMEDIATE` before inspection/DDL, coordinating separate database starters and rolling back an interrupted initial DDL transaction. Normal command concurrency and idempotency retain the existing store behaviour; this is not a multi-user or multi-host PostgreSQL proof.

## Compatibility and rollback

The sole new schema object is `alembic_version`; old app code ignores that table and its existing payload bytes are untouched by adoption. This does not promise old strict JSON readers can read later expanded product data: use a known-compatible application/schema pair and preserved isolated copy/export. No down-conversion of JSON, ownership mapping or local-to-cloud upload occurs.

`downgrade base` drops the baseline tables only when all five are empty. A populated downgrade raises before dropping anything. The destructive override `Config.attributes['disposable_test_database']=True` (CLI `-x disposable_test=true`) is reserved for explicitly disposable synthetic test fixtures. It is not a supported rollback for working user data. Tests demonstrate it only on a newly created temporary database.

There is no production rollback/restore claim here. T62 must prove restoration plus external-file/job/deleted-owner safety before those flows are accepted.

## Verification

```powershell
$env:PYTHONPATH = 'services/api'
.venv/Scripts/python.exe -m unittest services/api/tests/test_migrations.py -v
.venv/Scripts/python.exe scripts/generate-contracts.py --check
```

Tests use an independent literal pre-migration schema and two populated synthetic owners: snapshot-only historical JSON and expanded personal/planning JSON (EUR balance, unknown HUF, income, bill, completed allocation). All five tables are compared exactly before/after adoption, including original payload formatting and receipt fingerprints. Additional checks cover receipt replay without applying/rendering, restart/new-command retry, empty upgrade/downgrade/upgrade, populated refusal/explicit test override, schema/revision mismatch, concurrent bootstrap, interrupted DDL rollback and explicit-URL CLI behaviour. Root orchestrator runs the complete backend suite after parallel work stabilizes. PostgreSQL upgrade/rollback and real cloud data remain unrun.
