# Release Readiness Checklist (`docs/release-readiness.md`)

Updated: 2026-10-25
Status: **LOCAL PROTOTYPE VERIFIED / PRODUCTION GATES PENDING**

This file tracks the 14 mandatory release gates defined in `FinAgent_Production_Development_Prompt.md` (Section 18).

| # | Gate | Status | Evidence / Current State | Remaining Work |
|---|---|---|---|---|
| 1 | **Automated Test Suites** | 🟡 Partial | `python scripts/check.py` passes **31/31** backend & randomized invariant tests. `npm run typecheck` (0 errors) and `npx expo-doctor` (20/20) pass. | Add Jest/RNTL mobile component tests, PostgreSQL multi-user isolation tests, and Maestro native E2E suite. |
| 2 | **Financial Engine Invariants** | 🟢 Done (Core) / 🟡 Debt Pending | Integer-cent EUR ledger, `liquid_cash` vs `allocated` vs `planned` separation, idempotency, and 500-case randomized property check pass in `services/api/tests/test_journeys.py`. | Add debt APR/amortization invariants (avalanche vs snowball) and full 15-action MCDA sensitivity checks. |
| 3 | **Live Gemini Smoke Check** | 🟢 Done | `python scripts/smoke-gemini.py` verified live connectivity for both `gemini-3.1-flash-lite` and `gemini-3.5-flash-lite` (recorded in `.local/gemini-smoke.json`). Quota ledger enforces 12 RPM / 225K TPM / 450 RPD per model. | Add bounded tool-call numeric verification (`evals/`) before public staging release. |
| 4 | **AI Evaluation Suite (60+ cases)** | 🔴 Pending | Local fallback and live chat tested in `test_journeys.py`. | Build 60-scenario `evals/` harness covering numerical grounding, adversarial prompt injection, scope refusals, and recommendation consistency. |
| 5 | **Native Mobile Journeys A–E** | 🟡 Partial | Journeys A (manual snapshot), B (CSV/XLSX/PDF/Image import via Base64 & multipart), C (plan accept/complete/cancel + bill pay), and D (AI assistant chat) work in Expo Go (`SDK 58`). | Implement Journey E (contextual micro-lessons) and record automated Maestro E2E evidence on iOS/Android. |
| 6 | **UI Quality & Accessibility** | 🟡 Partial | Warm ivory/brown/terracotta Stitch design tokens applied in compact layout (`apps/mobile/src/theme.ts`). | Complete VoiceOver/TalkBack screen-reader audit, dynamic font scaling (`1.5x`) verification, and color-independent error states. |
| 7 | **Security & Tenant Isolation** | 🔴 Pending | Local demo token (`DEMO_API_TOKEN`) in `expo-secure-store`, CORS restricted, optimistic concurrency (`409`) and idempotency (`Idempotency-Key`) active. | Replace single-user SQLite with PostgreSQL + Supabase Auth JWT verification + Row-Level Security (RLS) and cross-user penetration tests. |
| 8 | **Secrets & Git Hygiene** | 🟢 Done | `.gitignore` and `apps/mobile/.gitignore` exclude `.env`, `.local/`, and `node_modules/`. No secrets in tracked source files. | Add automated secret-scanning step in CI. |
| 9 | **Privacy, Export & Account Deletion** | 🟡 Partial | `GET /v1/export` (JSON) and `DELETE /v1/data` (full local wipe of state, receipts, imports, and quota logs) implemented and tested. | Add PII masking before sending statement text to Gemini, formula-safe CSV export escaping, and Paid-tier Gemini DPAs for production user data. |
| 10 | **Graceful AI / Worker Degradation** | 🟢 Done (Sync) / 🟡 Worker Pending | App and imports continue working when Gemini is disabled or quota-exhausted via deterministic parsers (`parse_pdf_lines`, `infer_columns`) and `local_reply`. | Move statement import processing to an asynchronous durable worker queue with dead-letter handling. |
| 11 | **Observability & Correlation IDs** | 🟡 Partial | Quota usage, latency, and error codes logged per model in `.local/quota.db` and exposed in `/v1/ai/status`. | Add structured JSON logging with `X-Correlation-ID` propagation across API and worker. |
| 12 | **Database Migrations** | 🔴 Pending | SQLite schema auto-created via SQLAlchemy `metadata.create_all`. | Add Alembic migrations (`up` / `down` / `up` verified against clean PostgreSQL instance). |
| 13 | **Documentation & Playbooks** | 🟡 Partial | `PROGRESS.md` and `docs/release-readiness.md` created; OpenAPI contracts generated (`contracts/openapi.json`). | Author `AGENTS.md`, `docs/design-system.md`, `docs/ux-decisions.md`, `docs/security/threat-model.md`, ADRs, and the 4 `docs/playbooks/` guides. |
| 14 | **CI/CD & EAS Build Readiness** | 🔴 Pending | Local verification runner `scripts/check.py` and contract generator `scripts/generate-contracts.py` working. | Add `.github/workflows/ci.yml` and `apps/mobile/eas.json` build profiles. |
