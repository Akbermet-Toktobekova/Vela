# Vela threat model — current bounded backend

2026-10-29, T44. Code inventory: accepted T24b/T32/T33/T34/T35/T51 and migration0003. This records trust assumptions and residual risks, not a penetration test or production approval. Synthetic isolation/mocks do not establish live Supabase/RLS/PostgreSQL/device security. [Data map](data-map.md) inventories current data; future schemas must update both documents before acceptance.

## Assets, adversaries and authority

Protect confirmed money/currency/date/provenance, profile/preferences, analytical statements, originals, owner isolation, credentials, command/lease identities and deletion intent. Expected adversaries include another authenticated user, a client editing IDs/body/versions, malicious document text or model output, stolen sessions, accidental operator misconfiguration, stale/crashed/concurrent workers and an unavailable/incorrect provider. Hosting/database/service-key administrators remain privileged trust actors; application checks cannot constrain an operator with direct database or service-key access.

Confirmed balances and allocations are authoritative server facts. Statements/AI/FX estimates cannot execute payments or overwrite them. Revisions/idempotency govern commands, not consent to new financial rules. No investment/tax/legal policy or financial-confidence threshold is approved by this model.

## Boundary 1 — device/browser ↔ FastAPI

- **Spoofing:** cloud derives owner from trusted asymmetric Supabase JWT, never body user_id or account path; local token only in explicit local/demo mode. Missing/invalid/expired credentials401; unavailable trusted verification503. Residual stolen-device/session and actual provider configuration: R1/R2.
- **Tampering:** strict request models, explicit minor units/currency, expected financial/job versions, receipt fingerprints and same-body/key replay reject altered/stale writes. Account/file/job references stay owner-scoped. Client state/text is never authorization. Residual full UI/cache/refresh behaviour on devices: R2.
- **Repudiation:** stored command receipts/history/job command responses explain accepted identities/versions; correlation IDs trace request outcomes without financial payload. This is not a signed, append-only audit/legal nonrepudiation system: R6.
- **Information disclosure:** generic credential/provider errors; no token in URL/export; fixed-name private attachments/no-store; native refresh token uses deployment-scoped SecureStore and web tokens remain memory-only in the adapter. Real OS backups/rooted-device/XSS/screenshots are not proven safe: R2.
- **Denial of service:** request/file/text/schema limits, bounded network operations and quotas help; CORS is an exact browser-origin allowlist, not rate limiting or authorization. Public API load/abuse limits and mobile offline/retry budgets require R5/R6.
- **Elevation of privilege:** cloud never falls back to DEMO_API_TOKEN; strict owner reference checks apply to every installed route. No service-role/database secret goes to clients. JWT verifier acceptance is not proof of provider RLS: R1.

## Boundary 2 — API/session adapter ↔ Supabase Auth/JWKS

- **S:** configured project issuer/audience/JWKS and ES256/RS256 allowlist establish trust; token jku/x5u/jwk/unsupported critical headers cannot choose keys.
- **T:** signature and required claims/time/subject checks reject modified tokens. Bounded trusted-key refresh handles rotation; failed refresh does not authorize stale expired cache.
- **R:** provider OTP/session events are outside the local journal; no delivered-email/session-revocation evidence is invented.
- **I:** public client configuration is distinct from backend secrets; OTP/access/refresh tokens must not enter diagnostics. Auth transport uses fixed endpoints; JWKS does not send user tokens.
- **D:** timeout/cache/cooldown/single-flight refresh bound some failures; provider outage gives a visible availability path, not a local identity fallback.
- **E:** no symmetric-algorithm fallback or client-supplied trust endpoint. A cached public key/access JWT may remain valid until cache/token expiry; immediate global logout is not promised. Residual operational signing/SMTP/revocation controls: R1/R2.

## Boundary 3 — API/worker ↔ backend database

- **S:** only verified owner enters user-scoped SQL; worker claims owner from durable records, not arbitrary document/model text.
- **T:** eight private tables have owner-containing identities; versioned migrations fail closed on unknown schema, preserve old payloads and reject populated destructive downgrade. CAS/transactions guard revisions, receipts, leases and preview publication.
- **R:** histories/receipts/generation/lease metadata survive intended restarts; privileged SQL rewrites and backup provenance are not prevented by these records alone.
- **I:** database payloads contain PII/financial text; encryption-at-rest, credentials, backups and operator access are hosting controls requiring evidence. SHA256 is not encryption.
- **D:** bounded jobs/retry policy and SQLite write serialization are implemented, but actual Postgres locks/pools/migrations, capacity, queues and cross-host quota controls are unrun operational gates.
- **E:** owner predicates and tests do not equal live RLS. Old local data is never automatically reassigned/uploaded to cloud. Residual infrastructure/restore/export/lifecycle work: R1/R3/R6.

## Boundary 4 — API/worker ↔ originals filesystem/Supabase private Storage

- **S:** owner/file UUID plus owner-scoped durable metadata determine access; no filename/path/body owner grants access. Private retrieval is mediated by API.
- **T:** path/symlink-escape checks, SHA256/size checks, pending→ready CAS and target fingerprint bind bytes to intended root/origin/bucket. Changed storage target fails closed rather than accepting wrong-target404 as deletion.
- **R:** metadata records creation/expiry/checksum/status and cleanup intent, not original filenames. Retention and processing consent are separate client choices; actual presentation/consent UX remains R2/R4.
- **I:** exact30-day expiry denies reads before provider I/O; pending/deleting objects deny. No public or signed URLs. Service credential bypasses RLS, so app owner checks remain mandatory. Private-bucket checks/mock responses do not prove a deployed bucket configuration: R1.
- **D:** physical deletion failures persist denied tombstones and return202 pending; maintenance retries. Outages do not become zero bytes, success or extended read permission.
- **E:** no public erase-all endpoint; privileged cleanup is internal, and destructive local test cleanup requires explicit disposable flag. In-flight provider operations may finish after an earlier deletion response; full generation/backup/restore guarantees remain R3.

## Boundary 5 — API/outbox ↔ separate worker ↔ parser

- **S:** job source and generation are committed before external upload; source UUIDs are fresh, owner-keyed and not selected by the client. Same enqueue identity cannot select another owner's source.
- **T:** unique enqueue fingerprints, versioned retry/cancel, expiring lease/token/CAS and final generation/source/status/expiry/checksum guards reject stale publication. Preview insert and success commit together; no automatic analytical apply.
- **R:** attempts/status/safe error codes and command receipts provide bounded operational evidence; crashes may repeat external extraction before durable success, so no exactly-once billing claim.
- **I:** status omits bytes/raw filename/key/token/provider diagnostics; worker CLI failures are sanitized. Private job payload still contains filename/purpose/processing choice and needs database protection.
- **D:** lease120s/heartbeat30s/attempts3/backoff5×2^(attempt−1) are configurable infrastructure defaults, not financial policy. Maintenance atomically protects live-upload and newly-ready sources. Deployment availability/throughput and provider spend remain R5/R6.
- **E:** delete removes owner jobs/generation in the same financial erase transaction; old workers cannot publish into a new generation. Wider restored-backup/deleted-owner lifecycle is not accepted solely from that guard: R3.

## Boundary 6 — untrusted statements/user text ↔ Gemini ↔ verified response

- **S:** statement instructions are data, never system authority. Provider output cannot choose owner, permissions, financial state, endpoint or hidden tool credentials.
- **T:** deterministic parsing/calculators ground amounts; T24b verifies reply numbers and rejects supported completed-payment claims/restricted advice/shaming, with at most one bounded retry then safe local fallback. Imported rows remain analytical-only. Model language filters do not prove arbitrary-language semantic safety: R4.
- **R:** model source/version and stored decision evidence must remain distinguishable from confirmed user facts. Persistent conversation/publication linkage in T59 is planned, not implemented here.
- **I:** pii.py and generate-level masking reduce PII in text/context; original-retention consent alone is not external-AI permission. Jobs persist a separate explicit choice/notice; false blocks all AI import branches even when global flags enable AI. Cloud synchronous imports without per-request consent parse locally only. Unrecognized PII/raw-document opt-in/provider retention remain R4.
- **D:** quota reservations/cooldowns/timeout/fallback bound this app's configured ledger; separate quota directories/hosts or other clients using the same provider project are not a shared spend gateway. Crash retry may bill again: R5.
- **E:** model answers cannot move money; acceptance/completion/payment effects require separate authenticated commands. Statement prompt injection cannot bypass hardcoded owner/financial constraints. Human policy/content calibration remains R4.

## Residual risks and accountable gates

- **R1 — live infrastructure/credential trust.** Owner: infrastructure/security executor plus product owner. Gate: T70 configuration/activation and T63 measured acceptance. Verify actual Supabase issuer/audience/signing key rotation, SMTP/provider settings, TLS, private bucket/service access, PostgreSQL driver/migrations/RLS and secrets/access controls before live use. No live proof is supplied by local mocks.
- **R2 — session/device/consent UX.** Owner: T52/mobile executor and product owner. Gates: T52 and T63. Prove native SecureStore behaviour/backup/logout, web session/XSS controls, per-account cache clearing, refresh races, visible retention/processing choices and device accessibility/offline flow; adapter unit tests alone are insufficient.
- **R3 — full data lifecycle/restore.** Owner: T62 lifecycle/security executor with operator/product owner. Gates: T62 then T63. Complete export of every new entity, provider backup retention, deletion202 progress, restored/deleted-owner in-flight races and isolated restore drills. Current State export is not a complete dump of all eight private tables/original bytes.
- **R4 — AI/privacy/content reliability.** Owner: financial-content reviewer/product owner with AI executor. Gates: T61 human policy/content review and T63; external processing/retention activation also T70. Masking/filter regressions do not prove universal de-identification, prompt-injection immunity, financial suitability or provider data-retention assurances.
- **R5 — shared cost/availability.** Owner: AI/infrastructure operator and product owner. Gates: T70 service/budget decision and T63 measured latency/spend. Local quota ledgers are not cross-host/project-wide enforcement; external extraction may repeat after crash. Do not infer paid activation from implemented flags.
- **R6 — operational abuse/audit boundaries.** Owner: backend/security operator with orchestrator. Gates: T63 capacity/error/security acceptance and T62 restore evidence. Confirm edge rate limiting/body limits/log retention, privileged operator access, lock/capacity behaviour and operational alerting. Correlation IDs are not forensic nonrepudiation.

## Review/update discipline

Evidence pointers: [T24b re-review](../agents/reports/T24b-independent-rework2.md), [T32 review](../agents/reports/T32-independent.md), [T33 review](../agents/reports/T33-independent.md), [T34 review](../agents/reports/T34-independent.md), [CHECKPOINT-3](../agents/reports/CHECKPOINT-3.md). These are prior recorded evidence, not tests rerun by T44.

For future review on new disposable fixtures, existing commands include `.venv/Scripts/python.exe scripts/check.py` and focused unittest modules `test_isolation`, `test_storage`, `test_worker`, `test_chat_tools`; generating/checking contracts follows repository rules. Never use demo.db/API8000–8003 as a security fixture. T53a reconciliation entities and T59 persistent conversations are planned and must update this inventory at implementation; their future controls cannot be credited now.
