# Backend feature catalog

Snapshot: **2026-10-31**. Plain-English names for frontend planning. Based on implemented routes/modules and canonical BACKLOG acceptance, not the design reference. Last accepted infrastructure checkpoint:335 backend tests, CHECKPOINT-3 (2026-10-29). This inventory is a source review, not a fresh test run or cloud activation proof.

## Implemented and accepted capabilities

1. **Email OTP & Session Support** — Supabase sign-in/session adapter supports requesting and verifying email codes, refreshing sessions and signing out. The API verifies signed access tokens. Provider responses were mocked in acceptance; real email delivery and deployment configuration remain unverified. Login screens are separate work.
2. **User Data Isolation** — Keeps each authenticated user's accounts, state, receipts, previews, original-file metadata and jobs separate. Client-supplied user IDs cannot grant access. Application isolation tests do not establish deployed database RLS.
3. **Financial Profile** — Saves optional financial focus, income type, expected amount/range, explicit preferences and restrictions. Tracks where facts came from and when they were confirmed. Expected income does not add money.
4. **Resume Onboarding** — Saves the current onboarding step and skipped questions so a frontend can resume the process. A statement or savings goal is not mandatory.
5. **Accounts** — Saves multiple EUR/HUF accounts with a known balance and confirmation date, or an explicitly unknown balance.
6. **Update Balance** — Replaces an account's recorded balance. The difference is not invented income or spending.
7. **Add Received Income** — Records income as add-to-balance, already-included, or income-plus-explicit-balance-replacement. Retry protection prevents recording the same command twice.
8. **Available Money & Plan** — Builds a plan from one selected EUR account, dated facts, protected money, bills and existing earmarks/reservations. Missing/stale/incomplete facts can block dependent actions. HUF is supported for accounts and display conversion, not this affordability calculation.
9. **Single Savings Goal** — Supports one optional named goal, target and earmarked progress in the account-backed plan. Multiple independent goals are not finished.
10. **Amount Preview** — Checks a proposed savings step and shows its effect on available money before accepting it. Preview does not save a financial change.
11. **Reserve / Complete / Cancel a Step** — Reserves money, records earmarking, or releases a reservation. These are records inside the plan; Vela does not transfer money.
12. **Defer / Resume Plan** — Lets the person postpone a suggested step and return to it later.
13. **Upcoming Bills** — Adds/cancels bills and records a payment with an explicit balance effect: subtract it, or mark it already reflected. The app does not pay the bill.
14. **Statement Parsing** — Reads supported CSV/XLSX and supported PDF content. Image/raw-document AI processing is conditional on operator settings and explicit processing permission. Imported records are analytical evidence; they do not change balances or complete actions.
15. **Background Import Jobs** — Durably uploads/enqueues a statement, exposes status, and supports eligible retry/cancel operations. A separate leased worker survives frontend closure and publishes a review preview; stale/deleted-owner jobs cannot publish. Cloud concurrency/deployment and exactly-once external AI billing are not claimed.
16. **Transaction History** — Provides paginated imported transaction history. The accepted legacy analytical projection is EUR; richer currency-aware reconciliation is still under review.
17. **Spending Observations** — Suggests recurring-payment patterns, price changes, income series, category totals, possible refunds and own-transfer evidence, with supporting transaction IDs. Suggestions do not establish motives or change finances.
18. **EUR/HUF Display Conversion** — Uses dated ECB reference quotes through Frankfurter, Decimal arithmetic and owner-approved HALF_UP rounding. Unknown balances/missing quotes produce an incomplete total. Converted money never funds a plan.
19. **Assistant Context** — Provides current plan facts, recorded activity, observations and relevant lessons from one state revision, for a frontend explanation view. This is distinct from persistent conversational chat.
20. **Lessons & Quizzes** — Existing lesson endpoints return educational content, quizzes and saved progress; contextual lesson readers also serve the account-backed plan. Content review/device acceptance remain separate gates.
21. **Private Original Files** — Stores originals privately with owner checks, checksums and30-day expiry. Expired/deleting files cannot be read. Failed physical deletion retains cleanup intent and can return `deletion_pending`.
22. **Export & Delete Data** — Current export returns the user's State JSON. Deletion removes owner state/jobs and attempts original-file cleanup. Export of every auxiliary entity, provider-account removal, backup erasure and full restore guarantees remain unfinished lifecycle work.
23. **Frontend Bootstrap API** — Returns a consistent initial set of personal and assistant data from one revision. Its original local-kit capability flags remain local-scoped; they are not an updated cloud feature registry.
24. **Safe Commands & Persistence** — Revision checks, idempotency keys, durable storage and versioned migrations protect against stale edits, duplicate commands and incompatible schema changes.
25. **Private Request Diagnostics** — Adds correlation IDs and an allowlisted request log without request bodies, raw financial descriptions or tokens. This does not sanitize every external proxy/provider log.
26. **Suggestion Engine / Next Best Step** — The current account-backed plan returns one of clarify, shortfall, planned, maintain, goal reached or a proposed savings amount. It checks confirmed/fresh EUR balance, protected money, bills and debt-payment coverage; existing reservations/progress influence the result. The savings policy remains explicitly provisional. Advanced action ranking exists separately; the fully unified specialist/multi-goal publication flow is unfinished.

## Existing calculation/AI modules with integration limits

- **Debt Calculator** — Existing debt/payoff simulation endpoints calculate supported repayment scenarios and identify missing terms. Legacy financial routes are guarded after the new account-backed plan is activated; do not present this as fully integrated new-plan debt management.
- **Recommendation Engine** — Existing cash-flow, debt, action-ranking and coordination modules calculate and preserve decision evidence. The expanded multi-goal/same-version specialist and unified publication flow is not finished.
- **Weighted Decision Engine (MCDA)** — Scores eligible actions using configured weights: resilience30%, net financial benefit25%, goal progress25%, reduced management complexity10%, lower execution burden10%. It calculates criterion utilities and weighted scores; it does not automatically learn or derive personal weights. Hard constraints and urgency take precedence. Missing material criteria prevent a numeric score; sensitivity tests vary weights by20% and flag unstable choices. All current weights/anchors remain provisional pending human calibration; full integration with the new suggestion flow is unfinished.
- **Conversational AI & Guardrails** — Existing Gemini chat tools, output checks, quotas and deterministic fallback support the legacy chat path. Canonical account-backed context is available separately; persistent owner chat and the fully integrated new Assistant are not finished. Cloud AI activation is not implied.

## Implemented work awaiting acceptance

- **Statement Review, Corrections & Reconciliation — T53a** — New review/correction/apply code is present and under review. It is intended to retain source rows and correction history, preserve identical purchases, and require decisions for ambiguous overlap. Do not count this as accepted yet.
- **Cloud Launch Configuration — T70** — Templates, PostgreSQL driver/configuration and operating-cost preparation are in progress. No live deployment, provider/RLS verification or paid activation is established.

## Not finished / not supported as a completed backend feature

- Explicit links between imported rows, manual received income and own-transfer pairs (T53b).
- Expanded uncertain-income and multi-period scenario API (T54).
- Multiple goals and shared allocation accounting (T55).
- Expanded same-version specialists and stable unified recommendation publication (T56/T57).
- Complete new recommendation/action lifecycle (T58).
- Persistent owner-isolated Assistant conversations (T59).
- Full all-entity export/deletion/restore lifecycle (T62).
- Bank connections, actual payments/transfers and investment execution are outside this pilot.
- Server-delivered reminders and a completed native reminder workflow are not backend capabilities here.

## Source references

[Canonical backlog](../agents/BACKLOG.md), [checkpoint](../agents/reports/CHECKPOINT-3.md), [frontend integration](FRONTEND_INTEGRATION.md), [authentication](authentication.md), [profile](profile.md), [storage](storage.md), [jobs](jobs.md), [FX](fx.md). Routes/modules: services/api/vela/main.py, personal.py, profile.py, planning.py, frontend.py, jobs.py, observations.py, fx_routes.py, storage.py, debt.py, decision.py, coordination.py, chat.py and lessons.py.
