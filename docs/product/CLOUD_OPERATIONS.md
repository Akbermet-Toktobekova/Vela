# Cloud launch preparation — T70

Prepared2026-10-31. This is an offline-reviewed configuration contract, **not deployment approval**. No account, database, bucket, SMTP service or bill was changed. The owner-approved topology remains Render API + separate worker, Supabase Postgres/Auth/private Storage, email OTP and no Redis.

## Supplied files and configuration

- `deployment/render.yaml`: manual web/worker Blueprint, automatic deployment off. Both use the repository's requirements and cloud launcher. No migration is run from a build hook. Applying a Blueprint can create billable resources/initial deployments; the automatic-deployment setting does not authorize that action. Review the final runtime, migration head, region and actual account before activation.
- `deployment/cloud.env.example`: names and obvious placeholders only; do not load this as a working `.env` or put real credentials in source control.
- `scripts/run-cloud.py api|worker`: requires `APP_MODE=cloud` and an explicit PostgreSQL URL. It never loads dotenv, selects demo.db or chooses a local API port. `--check-config` validates configuration shape without opening a server, database or provider connection. An actual API port comes from `PORT`; the worker never listens.
- `scripts/run-cloud-migrations.py`: requires a separate `MIGRATION_DATABASE_URL`, uses a PostgreSQL advisory transaction lock, then runs Alembic. `--check-config` is offline. A runtime DSN cannot silently substitute for the migration DSN. Actual migration and rollback require separately approved disposable PostgreSQL proof.
- `deployment/deny-client-data.sql`: manual transaction for the eight current private tables and Alembic marker. It checks migration0003, revokes client-role privileges, enables RLS and rejects remaining inherited client table grants. It is not a migration and was not executed. Audit existing security-definer RPCs, role inheritance, schema exposure and future tables separately. Direct backend SQL owner checks are still required; this is not an auth.uid()-based end-user RLS implementation.

Use `.venv/Scripts/python.exe` locally; the explicitly declared driver is `psycopg[binary]==3.3.6`. Both distributions were confirmed inside the project `.venv`. No global install was performed. Backend and worker environments need reproducible compatible Python/dependencies before activation; a template is not evidence of a successful Render build.

## Required settings and boundaries

`DATABASE_URL` must use `postgresql+psycopg://` with an explicit host/database/credentials, `sslmode=verify-full` and an absolute installed `sslrootcert` path. URL-encode credentials and query values. The shape validator requires the CA file to exist; it does **not** validate a certificate chain, hostname or actual connection. Obtain the actual project certificate and direct/session-pooler settings securely. [Supabase connection guidance](https://supabase.com/docs/guides/database/connecting-to-postgres) and [SQLAlchemy psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg) explain the provider/driver boundary.

Trusted auth settings are `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWT_AUDIENCE`, `SUPABASE_JWKS_URL` and explicit `SUPABASE_JWT_ALGORITHMS`. They must match the actual project's asymmetric signing configuration. Storage requires `SUPABASE_STORAGE_BUCKET` and backend-only `SUPABASE_STORAGE_SERVICE_KEY`; the actual bucket must be private. The service credential must never be delivered to the frontend. Public frontend configuration is only API URL, Auth URL and public publishable/anon key. See [authentication](authentication.md) and [storage](storage.md).

API `FRONTEND_ORIGINS` is a JSON list of exact HTTPS origins, without paths/wildcards; `[]` is suitable for a native-only deployment. `CLOUD_STATE_DIR` is an explicit absolute operational directory. Its current temporary location holds local quota bookkeeping, not financial state or original bytes. It is ephemeral and not a shared API/worker quota authority.

`JOB_LEASE_SECONDS`, `JOB_HEARTBEAT_SECONDS`, `JOB_MAX_ATTEMPTS` and `JOB_BACKOFF_SECONDS` default to120/30/3/5. The launcher applies them to the API enqueue repository and worker. Configure the same values on both services. The API upload lease and worker processing/recovery semantics remain the [jobs contract](jobs.md); these timings are infrastructure controls, not financial rules.

Cloud launch rejects `ENABLE_GEMINI=true` or `ALLOW_RAW_DOCUMENT_AI=true` and forces both false during dispatch. This is deliberate: separate process-local SQLite quotas do not prove a shared spending cap. Enabling paid/external AI requires a separately implemented and independently accepted shared quota/spend path plus owner activation approval. Per-job processing permission remains required even after operator activation is permitted.

Supabase SMTP configuration is provider-side. Before testing delivery, obtain an approved sender/domain and SMTP account securely, verify DNS and allowed destinations/rate limits, and configure an email-code template using `{{ .Token }}`. Never paste SMTP passwords or service/database keys into chat. No SMTP vendor is selected by the sample estimate. [Supabase email templates](https://supabase.com/docs/guides/auth/auth-email-templates) and [Render Blueprint reference](https://render.com/docs/blueprint-spec) are the relevant setup references.

## Dated operating-cost estimate

USD/month, checked2026-10-31, before taxes and usage overages. This is arithmetic under stated assumptions, not an account quote or approval to buy:

- Render API `0.5c-512mb`: $7; separate worker on the same size: $7. Assumes Hobby workspace at $0 plus compute, one instance each, no paid disk/workspace add-ons. These are minimum template sizes, not a measured capacity guarantee. [Render pricing](https://render.com/pricing), [plan IDs](https://render.com/docs/compute-plans).
- One new Supabase Pro organization/project on included Micro compute: $25 base, assuming included compute credit and no excess usage/add-ons. [Supabase pricing](https://supabase.com/pricing).
- Illustrative SMTP: Resend Free is $0 within3,000 emails/month and100/day; its Pro example is $20/month for50,000. Eligibility, delivery configuration and vendor choice remain owner decisions. [Resend pricing](https://resend.com/pricing).

Thus the stated base scenario is **$39/month** with eligible free SMTP, or **$59/month** with that paid-SMTP example. Both assume AI off and usage within included storage/egress/auth allowances. Existing account subscriptions/projects can change incremental cost. Domain registration, tax, extra projects/compute, storage/egress overages, monitoring, backups/PITR and future AI calls are excluded; actual volume and limits must be reviewed before an activation budget is approved. Do not infer production suitability from these prices.

## Activation evidence still required

Before any owner activation decision, provide an exact version/region/service configuration and reviewed estimate for actual expected usage. Then independently prove disposable PostgreSQL upgrade/restart/concurrent claims, backend role permissions and direct client Data API/RLS denial; actual certificate/TLS, private-bucket read/deletion and expiry; OTP delivery/refresh/logout; cross-service shared quota controls if AI is desired; backup/restore/deleted-owner/in-flight guarantees under T62; privacy/content/device and T63 gates. The current SQL inventory must be updated after every new table, including future persistent conversations.

Manual activation is outside T70 execution. No secrets were inspected. No original local data was uploaded, cloud resource provisioned or paid service activated by this task.
