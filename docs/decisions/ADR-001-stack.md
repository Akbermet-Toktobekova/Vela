# ADR-001 — Local thesis application

Status: accepted implementation decision.

The provided workspace was an empty Git checkout; the skeleton mentioned in the brief was not present. Preserve the requested Python 3.12/FastAPI/Pydantic v2/SQLModel/SQLite backend and React/TypeScript/Vite frontend. Create the prescribed package boundaries from scratch. A pure dataclass domain keeps frameworks and I/O out of calculations.

Serve the production frontend from FastAPI on loopback. This is a local single-user application, not a hosted Sites/Worker application; replacing SQLite/Python with a Worker stack would depart from the brief. The Sites skill was consulted for interface workflow and local-preview rules. No Site was registered or published.

Direct dependencies are pinned in `pyproject.toml` and `frontend/package.json`; npm transitive resolution is tracked in `package-lock.json`, and Python transitive versions are recorded in `requirements.lock`. Vite/Vitest were moved to patched releases after npm audit findings. The final npm installation reported zero vulnerabilities.

The initial SQLite schema uses SQLModel `Record` (versioned application snapshots keyed by name) and `HistoryEvent` (append-only through the application). Domain records are JSON inside snapshots, avoiding ORM dependencies in the domain. No preexisting schema needed migration. Future relational/schema changes require an Alembic migration; Alembic is not installed for an unused migration workflow. The tradeoff is weaker database-level referential validation; the service validates relationships.

SQLite `BEGIN IMMEDIATE` serializes write units of work across processes. Recommendation issuance, decisions, ledger entries, and account changes commit atomically. There is no API for updating history records. Explicit demo reset/data deletion removes history as a user-controlled exception.
