# ADR 0001 — Pilot database, authentication and hosting

Date: 2026-10-29. Decision: approved by the product owner in [PILOT_SPEC](../product/PILOT_SPEC.md#product-decisions). Implementation status: see [T30 and dependent tasks](../agents/BACKLOG.md); this record is not a claim that cloud infrastructure or authentication is implemented.

## Context

Vela needs persistent, isolated personal accounts, statements, plans and conversations across Android/iPhone sessions. The approved pilot requires email OTP, private originals, a durable worker and owner-authenticated commands. Its financial contract uses integer minor units and explicit currency; analytical imports cannot change confirmed balances or execute actions.

The current [API factory](../../services/api/vela/main.py) implements only local single-user mode, accepts one local bearer token and resolves it to `local-demo`. The [store](../../services/api/vela/store.py) holds JSON state and separate receipts, import previews, coordination runs and published recommendations with owner keys. Owner-keyed tables are not proof of verified multi-user authorization. Automatic schema creation is not a versioned production migration system. Local SQLite and quota storage remain the current implementation; a database URL alone does not enable a safe cloud pilot.

## Decision

- Use **Supabase Postgres** for the pilot database, **Supabase Auth with email OTP** for user sessions, and **Supabase private Storage** for originals. Do not introduce a custom password system or a second identity provider.
- Run **FastAPI and a separate worker on Render**. Use **Postgres jobs/outbox without Redis** for durable background work. A frontend visit must not be the durable job scheduler.
- Resolve ownership on the server from a verified authenticated session. Every owner-scoped state, preview, receipt, run, publication, file, job and conversation must respect that identity. A request body or object path cannot grant ownership. Supabase/browser access and backend access must have explicitly tested authorization boundaries; no claim of RLS completion is made here.
- Support OTP send/verify, resend cooldown, invalid/expired codes, session refresh and sign-out through the approved provider. T32 owns verified backend identity and isolation; T52 owns the session-aware mobile path and account-specific cache clearing. Exact provider configuration belongs to those implementations, not a guessed authentication protocol in this ADR.
- Retain **local synthetic SQLite as an explicit compatibility/test mode**. It must not silently fall back into cloud authentication or use the local demo token in a nonlocal environment. Align the T32 implementation with the actual `APP_MODE` setting rather than creating a parallel `APP_ENV` bypass.
- Private originals expire **30 days after upload**: deny access when expired and retry physical deletion after failure. Confirmed analytical rows have a separate lifecycle. Account deletion covers associated user records, jobs, conversations and files; stale jobs cannot restore deleted data. Provider backup lifecycle and restoration limits must be documented honestly.

These choices trace directly to [Product decisions](../product/PILOT_SPEC.md#product-decisions), [Welcome and sign-in](../product/PILOT_SPEC.md#welcome-and-sign-in), [Data and API](../product/PILOT_SPEC.md#data-and-api) and [Reliability, privacy and migration](../product/PILOT_SPEC.md#reliability-privacy-and-migration). No pricing, region, service tier, SMTP vendor, signing algorithm or secret value is selected by this record.

## Consequences and safety boundaries

The local single-user token is useful for isolated development but does not satisfy cross-user or cross-device acceptance. T32 must prove invalid/expired-token rejection and two-owner isolation; T34 must prove private-file ownership, expiry and deletion; T33 must prove restart/retry/outbox and deleted-owner safety. SQL owner keys and a private bucket label alone are insufficient evidence.

Cloud OTP delivery depends on reviewed SMTP/provider configuration. Credentials, costs and operational settings are handled by [T70](../agents/BACKLOG.md#t70--cloud-configuration-and-activation-estimate). This ADR authorizes no service creation, deployment, paid activation, real-data upload, purchase or credential publication. Real cloud data still requires independent T24b acceptance and CHECKPOINT-2. Actual pilot acceptance additionally requires the release checks and human decisions stated in PILOT_SPEC.

Documentation can be recorded before CHECKPOINT-2 under the updated T30 task. This does not waive that gate for real cloud data. Development and review here use new synthetic fixtures/databases and free loopback ports; existing `demo.db` and API8000–8003 remain untouched.

## Migration path and task ownership

1. **T50** maps the existing snapshot, personal accounts/planning and analytical records to the new contract. Specify ownership, compatibility, provenance, versions and rollback before schema changes. No automatic account merging, demo-default confirmation or inferred financial events.
2. **T31** introduces versioned migrations. Prove upgrade/downgrade cycles on disposable empty databases and preservation on populated synthetic legacy fixtures. Verify exact amounts, currency, dates, source records, receipts and history; automatic `create_all` is not that proof.
3. **T32** adds provider-authenticated ownership and local-mode separation, followed by **T51/T52** for persistent profile and session-aware onboarding. Existing `/v1` compatibility and `/v2` transitions must be explicit in T50, not silently replaced.
4. **T34**, then **T33**, implement the private-original lifecycle and durable import processing against the approved architecture. Reconcile legacy filesystem-only task wording with this approved Supabase Storage decision before extending implementation scope. Local synthetic adapters/mocks are test facilities, not cloud acceptance.
5. **T70** prepares secret-free configuration and a reviewed estimate/activation checklist. Cloud transfer of existing local data is a separate explicit owner action after gates; no startup process may upload it automatically.

## Rollback and restoration

Never downgrade a populated working database in place on an assumption that older binaries can read expanded JSON/schema. Preserve an explicit export and an isolated backup/copy before a supported migration; T50 defines version compatibility, T31 proves migration preservation and T62 proves lifecycle/restore drills. Destructive `downgrade base` is confined to disposable test databases. Restore tests compare financial facts and provenance, not merely successful startup.

Rolling back an application build does not undo externally delivered emails, uploaded objects or cloud data changes. Record the deployed schema/application compatibility boundary and a tested restoration procedure before activation. This ADR promises neither zero-loss rollback nor instant backup erasure without that evidence.

## Outstanding activation evidence

No architecture choice is waiting for another SQLite-versus-Supabase vote. Remaining activation work is provider/SMTP credentials and configuration, the T70 cost/operational estimate, independent security and migration evidence, and explicit owner activation approval. Financial-policy, device and human-content gates remain governed by their existing tasks; this ADR does not decide them.
