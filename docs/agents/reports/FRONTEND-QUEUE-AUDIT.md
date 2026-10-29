# Frontend/backend queue dependency audit — 2026-10-29

Status: audit complete; no implementation or release acceptance implied. Reviewer: independent delegated Codex audit agent. Baseline: db5b78a, with concurrent disjoint T72/T75 working changes. This file records repository facts and an executable order for the root orchestrator, not new financial decisions.

## Approved choices already present

- PILOT_SPEC Product decisions and HANDOFF D2 resolve infrastructure: Supabase Postgres/Auth/private Storage, email OTP; FastAPI and separate worker on Render; Postgres jobs/outbox without Redis. T30's legacy blocked/choice text is stale. Do not ask the owner to choose SQLite versus Supabase again. T30 still depends on CHECKPOINT-2 and must write the actual ADR.
- PILOT_SPEC Reliability explicitly sets original-file expiry30days after upload, access denial at expiry and retry of physical deletion. Analytical rows have a separate lifecycle. D5 is therefore partially resolved: original retention is fixed; provider backup lifecycle/erasure evidence remains to document. HANDOFF/PRODUCT_PLAN stale broad D5-open wording must be reconciled.
- Android and iPhone plus English UI are approved. D6's language is resolved; exact market/country-specific applicability and human content review remain unconfirmed where needed.
- No deployment/purchases are approved; cloud costs, SMTP and credentials remain gated before activation. T70 is todo, its report does not exist. `docs/adr/` was absent at initial audit. User's implementation authorization permits drafting code/config and synthetic checks, not paid activation or using real cloud data before T24b/CHECKPOINT-2.
- D1 provisional weights stay provisional. D3 actual Android/iPhone test devices, D4 human financial reviewer, country-specific D6 and D7 cost/quality budget still need external evidence/decisions at their gates; agents cannot self-sign them.

## Current verified starting point

T74 is accepted canonical local EUR plan. T71 local personal-data path and T72 analytics are bounded slices, not completion of T51/T53 or multi-user cloud ownership. T75 adds local frontend contract and kit; it does not substitute for T32/T57/T59. No auth.py, worker.py, jobs.py, storage.py, migration/isolation test modules existed at initial file inventory. Requirements contain no Alembic/Postgres driver yet; add only dependencies explicitly authorized by scoped task/approved ADR, never global packages.

T24b independent review in this session is REWORK: ordinary-English fabricated settled-rent claim and buy-a-gilt investment directive escape output checks.64 chat/tools tests and60offline evals pass, but adversarial mock demonstrates returned unsafe model output. See T24b report. CHECKPOINT-2 cannot be passed merely because those suites are green.

## Safe implementation and review order

1. Finish/review T75; finish/review T72 R1; independently review T73. These may overlap only with disjoint file ownership and centralized commits. Keep uncommitted T75 work rather than resetting it.
2. Execute bounded T24b R1/R2 rework, then independent security review in clean context. Only after acceptance perform actual CHECKPOINT-2 checks and reconcile PROGRESS/release-readiness. No phase label or tag before real checks.
3. T30: write ADR from the approved Supabase/Render/OTP choices, local synthetic testing strategy and gated activation. T50 follows T30: document full compatible records/ownership/provenance, current legacy+personal+planning migration and rollback, all A–J ownership and API groups. Both are documentation tasks and need independent review.
4. T31 follows accepted T30+T50: Alembic migrations, populated **synthetic** legacy fixture preservation, money/date/source/history comparisons and isolated restore proof; upgrade/downgrade destructive cycles only on disposable test databases. Never read demo.db for a fixture. Extend scope explicitly if requirements/dependency declarations need changes.
5. T32 follows accepted T31: verified provider JWT owner, invalid/expired tokens401, owner isolation across state/previews/receipts/runs/publications, local token only under actual APP_MODE=local. Before execution align old APP_ENV wording and approved OTP/session provider with ADR; no invented password system. Test two owners locally with synthetic signed/mocked tokens before cloud use.
6. After T32, T51 profile/provenance and T34 private storage can be delegated with disjoint file ownership or separate checkouts. T34's old filesystem-only scope must be reconciled with approved Supabase private Storage and30day expiry; preserve local synthetic testing support without claiming cloud proof. T35 logging may run after CHECKPOINT-2 but conflicts on main.py must be serialized.
7. T33 follows T31/T32/T34: durable jobs/outbox, lease/retry/dead-letter, restart/race/deleted-owner safety. T52 follows T51 for actual session-aware progressive onboarding. T70 configuration/estimate follows T30/T32/T33/T34; preparing templates is allowed, activation remains a separate owner decision.
8. T53 follows T51/T33/T34 for analytical reconciliation/corrections/overlaps/manual-income links. T54 follows T51/T53 for received versus expected income and explicit multi-period scenarios. T55 follows T51/T54 for multiple goals/allocations, no duplicate euros. No invented thresholds/weights/probabilities.
9. T56 follows T54/T55/T24b for same-version specialists. T57 follows T56/T33/T35 for atomic stable recommendations/stale-worker rejection. T58 follows T57/T55/T53; split backend/action lifecycle and UI into narrow child tasks before work, without connecting the independent HTML automatically.
10. T59 follows T24b/T51/T57/T55 for owner-isolated persistent conversations/read-only scenarios/current recommendation explanations. T60 follows T58/T17/T18 for contextual lessons, with reviewed-content evidence or honest absence. These touch shared chat/tools and must not run overlapping mutations blindly.
11. T61 follows T56/T60 and needs human D4 plus explicit preferences/market applicability. Preparation is executable; human reviewed status is not automatable. T62 follows T53/T55/T59/T34/T44 for complete export/delete/files/jobs/chat/restore races. T63 follows T58/T59/T60/T61/T62/T41/T42/T45 for actual J01–J12 evidence, devices and cost/latency budget. T46 follows all required accepted tasks; audit never authorizes deployment.

Existing T40–T45 dependency cards remain authoritative. T42 live-device evidence cannot be fabricated from YAML validation; T44 security/data map is required by T62. No formal dependency is bypassed just to increase parallelism. In a shared checkout root owns BACKLOG/HANDOFF/generated coordination/commits; executors own assigned files and reports only.

## Independent checks executed during audit

- Targeted chat/tools:64 tests,12.048s, OK; full log returned by tool.
- Offline evals:60/60 PASS,2.205s; ignored report `.local/independent-audit-20261029/evals.json`.
- Full backend on current concurrent tree:238 tests,46.607s, OK; `.local/independent-audit-20261029/backend.txt`. Test count may grow as executors finish; this is the captured run, not a frozen final-tree certification.
- Fresh full Expo web export:958 modules,21 bundles, exit0; `.local/independent-audit-20261029/web`.
- `git diff --check`:exit0 (line-ending warning for planning.py only).
- T73 source inspected at18d34b8; no current settings.tsx working diff. Real browser export is assigned to root using new synthetic API64131/web64130 and56Unicode rows; no acceptance inferred from the old executor's artifact.

## Boundaries

No demo.db read/write, no access to or management of API8000–8003, no paid provider call, no cloud activation, no deletion of user data, no change to independent HTML. A dedicated Chrome launch command was blocked by automatic command policy; it was not retried through an equivalent shell workaround. Browser verification can continue through root's approved browser connector. Only audit-owned synthetic servers were started and their private token remains in ignored connection.json.


### T73 browser outcome

Independent actual download remains blocked by browser-tool availability: root CDP attach timed out, then Windows Computer Use stopped because it could not confidently determine current browser URL. No UI fallback bypass or auth automation attempted. Keep review/pending; no export defect or acceptance asserted. Audit-owned API64131/web64130 stopped via their sentinel after the attempt.
