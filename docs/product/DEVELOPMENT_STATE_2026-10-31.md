# Vela development state | 31 October 2026

**Vela works today as a local financial planning prototype.** A person can record a balance, add received income, preview an affordable savings step, reserve or cancel it, confirm earmarking, record a bill payment, and inspect imported transactions. The best evidence is for a single EUR account, one optional goal and synthetic statements. The team has also built much of the infrastructure for a private cloud pilot. Staging, a real-data pilot, and public release still lack acceptance. None of the twelve complete product journeys has been signed off.

**Snapshot.** The baseline is commit `a963e3c` on 31 October. Implementation, tests, mobile screens, generated HTTP contract, policies, lessons, migrations, operations files, and dated review records were inspected. Parallel work on recommendation publication was visible in the checkout. Its status is identified separately below. Statements about an absent feature refer to this repository and its recorded evidence.

**How to read the scores.** Each score is my confidence, out of 100, that the stated stage and limits are accurate. A planned feature can score 99. The number does not measure percent complete, test coverage, advice quality or probability of a successful deployment. Scores of 97–99 generally have matching code and independent or directly reproduced evidence. Scores of 90–96 generally rely on bounded tests, historical browser evidence or a clear specification gap. Lower scores signal moving code or an unverified handoff. “Accepted” means the project accepted the named slice. “Review” means implementation exists and formal acceptance is outstanding.

**Evidence dates.** In this audit, the eight debt tests passed, including three hand-calculated cases, 500 randomized trials and the API mutation/retry test. All 17 mobile session tests passed using simulated providers. The navigation check passed for 11 allowed and 15 unsafe or unsupported destinations. The latter is a route check, not a device run. The full-suite evidence below is historical. CHECKPOINT-2 recorded 244 backend tests, 60 offline scenarios, contract and mobile checks on 29 October. CHECKPOINT-3 recorded 335 backend tests, contract and TypeScript checks, and Expo Doctor 20/20 that day. The 31 October specialist report recorded 371 backend tests on a shared working tree. Those runs covered different snapshots. This audit did not repeat the full suite or exercise a live provider, physical phone or deployed database. [Phase 2](../agents/reports/CHECKPOINT-2.md) · [Phase 3](../agents/reports/CHECKPOINT-3.md) · [Specialist run](../agents/reports/T56b.md)

## Accounts, income and planning

| Feature and stage | What works and how it was checked | Remaining scope | Certainty |
|---|---|---|---:|
| Financial profile and onboarding checkpoint · accepted backend | Optional focus, income type, ranges, preferences, restrictions, source and confirmation information, skipped questions and resume position persist per owner. Expected income is informational. Independent profile tests. [T51](../agents/reports/T51-independent.md) | Full progressive mobile onboarding, cross-device return and in-context clarification (T52). | 98 |
| Local personal screen · review | Connect opens saved profile, accounts and income. Browser runs exercised optional fields, known EUR and unknown HUF, validation, Back without Save, reconnect, outage/retry and a conflict between tabs. [T71](../agents/reports/T71.md) · [Browser run](../agents/reports/UI-TEST-05.md) | Date entry and the full sign-in-to-Today path need work. Native keyboard and second device remain untested. | 95 |
| Account balances and received income · implemented locally | Multiple EUR/HUF accounts. A dated replacement sets a balance without inventing spending. Income can add to cash, be recorded as already included, or accompany an explicit replacement. Duplicate saves and stale revisions have recorded checks. [Local contract](LOCAL_V2.md) · [Browser run](../agents/reports/UI-TEST-04.md) | Complete dated mobile forms, home-screen shortcut and reconciled statement links. Unknown balances stay unknown. | 97 |
| Legacy snapshot and cash-flow forecast · accepted module | Manual snapshot records cash, buffer, goal and obligations. Dated forecast uses the minimum available balance across the horizon. The §9 fixture proves €100 available, rejects €150, allows €40 and reduces capacity to €20 after an €80 obligation. [Fixture](../../services/api/tests/test_acceptance_fixture.py) · [T11](../agents/reports/T11.md) | Legacy evidence cannot establish the same behavior for uncertain future income, multiple currencies or every new-plan route. | 99 |
| Current-account plan and savings goal · accepted local slice | A selected, freshly confirmed EUR balance funds one optional goal. Available money subtracts earmarks, protected funds, bills in the horizon and reservations once each. Missing balance, stale facts or incomplete coverage can require clarification. HUF, expected money and statement totals cannot fund the plan. [T74](../agents/reports/T74.md) · [Engine contract](engine.md) | Multi-account funding, uncertain-income scenarios (T54), multiple priorities, deadlines and shared allocations (T55). | 98 |
| Preview, reserve, defer, complete and cancel · accepted local slice | Preview leaves state unchanged. Reserve commits capacity. Cancel releases it. Completion records earmarked money. Deferral can be resumed. Independent HTTP/client example reserved €40, retried safely, added €100 income and completed €40 with €1,100 cash, €40 saved and €160 available. [Independent oracle](../agents/reports/T75-independent.md) | Full lifecycle across debt, own transfers, service cancellation, correction history and matching a completed step to a transaction (T53b/T58). | 99 |
| Upcoming bills · accepted local slice | Add or cancel a confirmed obligation. Paying can subtract from cash or record payment already reflected in the balance. Changed commitments can invalidate affordability. Browser evidence covers shortfall and bill payment. [T74](../agents/reports/T74.md) · [Navigation exercise](../agents/reports/UI-02.md) | Broader recurring schedules and the full statement suggestion → separate user confirmation journey. | 97 |
| Legacy adoption and replay protection · accepted | Explicit adoption preserves legacy history. After activation old financial advice and unsafe writes are guarded. Replaying an old receipt cannot resurrect an obsolete recommendation. Independent checks cover race, changed payload and allowed retries. [T74 re-review](../agents/reports/T74.md) | This is local compatibility work. Populated cloud migration and restore remain separate. | 99 |
| Debt register, comparison and simulation · accepted bounded module/UI | Add, list and remove debts. Monthly amortization handles zero APR, capped last and one-off payments, unknown terms and non-amortizing debt. Compare minimum-only, avalanche and snowball. Read-only simulation and retry behavior passed in this audit. [Debt tests](../../services/api/tests/test_debt.py) · [Mobile screen](../../apps/mobile/src/app/debts.tsx) | Statement-discovered debt, confirmed fees and terms, and an integrated affordable one-off versus recurring recommendation for the selected account. Native acceptance open. | 99 |
| Display currency conversion · accepted backend | Dated Frankfurter/ECB quotes, historical lookup, bounded quote cache, Decimal conversion and HALF_UP rounding. Original EUR/HUF amounts survive. Unknown balance or unavailable quote makes the total incomplete. Service and HTTP tests used mocked quotes. [Service review](../agents/reports/T67-service-independent.md) · [Route review](../agents/reports/T67-routes-independent.md) | Live provider, corresponding display on production devices, and pilot outage verification. Conversion gives no spending capacity. | 98 |

## Statements and spending analysis

| Feature and stage | What works and how it was checked | Remaining scope | Certainty |
|---|---|---|---:|
| Local parsing and preview · implemented | Detects file type, text encoding, delimiters, header or inferred columns, decimal and date formats. Parses supported CSV, spreadsheets and text PDFs. Preview can contain warnings, transactions, reported balances and recurring candidates. Parser and API tests include synthetic variants. [Parser](../../services/api/vela/imports.py) · [Journey tests](../../services/api/tests/test_journeys.py) | Layout-dependent. Real bank format coverage and mobile recovery for large, damaged or password-protected files are unproven. | 96 |
| Image or difficult document extraction · conditional adapter | Raw-document AI is separately gated by operator settings and processing permission on the durable path. It can return structured extraction when available. Financial storage uses minor units, but the model extraction schema accepts floating-point amounts before normalization. [Parser](../../services/api/vela/imports.py) · [Job permissions](jobs.md) | Mocked/parser evidence does not establish OCR accuracy, live precision, privacy consent UX or production cost. Cloud launch currently disables external AI. | 95 |
| Apply analytical rows and browse history · accepted T72 | New analytical apply records evidence without changing balances, goal savings, obligations or completions. The three monthly fixtures accumulated 16 → 36 → 56 rows. Repeating September retained 56. Pagination reached the six oldest rows. Refunds stayed separate and imported future credits did not fund a plan. [Re-review](../agents/reports/T72-independent-r1.md) · [Fixtures](../testing/pattern-statements/README.md) | Legacy apply has different compatibility behavior before activation. The accepted analytical projection is EUR. Full correction/overlap workflow has its own task. | 99 |
| Pattern detection and evidence · accepted local subset | Groups recorded rows into recurring debits, changed amounts, observed income series, category/month totals, possible refunds with matching references, and labelled transfers. Each suggestion links amounts, periods and source transaction IDs. Sparse periods limit interpretation. [Logic](../../services/api/vela/observations.py) · [T72](../agents/reports/T72.md) | Confirm/reject lifecycle, fees, repeated small purchases, post-income distribution, matched transfer pairs and broader comparable-period analysis are incomplete. | 98 |
| Currency-aware source review and corrections · T53a review | Review stores originals and effective values separately, including ordinal, checksum, account and append-only correction/decision history. Handles identical purchases, ambiguous overlaps, manual categories and HUF analytical rows. A correction invalidates dependent stale links. Independent source re-review found the fix in both correction and apply paths. [T53a review](../agents/reports/T53a-independent.md) | The final basic-data runtime smoke was pending at this baseline. Parent T53 mobile review/edit flow and T53b manual-income/transfer links are open. | 95 |
| Asynchronous upload, status and recovery · accepted backend | Durable enqueue returns a job. Owner can poll, cancel eligible work or retry eligible failure. Worker claims leases, heartbeats, retries with backoff, dead-letters failures and publishes a preview only for the current owner generation. Local synthetic recovery and isolation passed independent review. [Job contract](jobs.md) · [T33](../agents/reports/T33-independent.md) | Current mobile import still submits the synchronous upload. Polling across app closure, cloud worker concurrency and exactly-once external billing lack end-to-end proof. | 98 |
| Private originals · accepted backend | Owner-scoped keys, checksum and consent, 30-day expiry, denied expired reads, retryable physical deletion and retained cleanup intent. Independent storage/migration checks used isolated or simulated services. [Storage](storage.md) · [T34](../agents/reports/T34-independent.md) | Live bucket access and scheduled cleanup/restore evidence, plus user controls for deleting originals separately from analysis. | 98 |

## Recommendations, Assistant and learning

| Feature and stage | What works and how it was checked | Remaining scope | Certainty |
|---|---|---|---:|
| Action catalogue · accepted policy module | Fifteen actions have eligibility rules, exclusions, effects and learning links. Maintaining the plan is a baseline. Catalogue entries describe choices, not executable transfers. [Policy](../../policies/action-catalogue.v1.json) · [Tests](../../services/api/tests/test_catalogue.py) | Human policy review and action-specific product integration. | 99 |
| Legacy weighted ranking · accepted module | Hard constraints and urgency precede scoring. Provisional weights are resilience 30%, financial benefit 25%, goal progress 25%, lower complexity 10%, lower execution burden 10%. Unknown material inputs can prevent scoring. Tie-breaking, ±20% weight sensitivity and decision evidence support review. [Ranking](../../services/api/vela/decision.py) · [T15](../agents/reports/T15.md) | No validated personal weights or human financial calibration (T61). | 98 |
| Legacy coordination · accepted module | Tracks specialist dependencies, completion, retries/timeouts, stale revisions, publication identity, dismissal cooldown and recalculation triggers. Tests cover late results, repeat completion, new income and publication races. [T16](../agents/reports/T16.md) · [Tests](../../services/api/tests/test_coordination.py) | Legacy cash-flow/debt/explanation roles differ from the requested spending/debt/savings team. The new service still needs a complete mandatory-result barrier. | 97 |
| Weighted selected-account engine · T56a accepted | Pure calculation ranks supported single-goal EUR candidates, preserves an eligible plan or deferral, and reports score components, reasons, policy and input fingerprints. Independent fixture with €1,000 cash, €800 bills and €100 protected gave €100 available and selected €20. No financial write. [Acceptance](../agents/reports/T56a.md) | Advanced income, multiple goals, confirmed debt terms and model participation remain outside this accepted slice. | 99 |
| Shared recommendation publication · T57a in progress | Accepted baseline has an account-backed plan and Assistant context. During inspection, uncommitted changes began feeding the weighted decision and its ID/summary to the planning view. The implementation is moving. [T57a card](../agents/BACKLOG.md) · [Planning source](../../services/api/vela/planning.py) | No accepted proof at this baseline of stored atomic publication, same-card parity across every reader, or invalidation under concurrent changes. Parent T57/T58 remain open. | 89 |
| Profile-aware AI specialists · T56b review | Cash-flow, debt and savings/goals adapters receive role-specific trusted calculator references and matching versions. They return references, reject invented or wrong-role output, time out separately, and cannot write finances. Eight focused mocked tests recorded. [Contract](specialist-agents.md) · [Report](../agents/reports/T56b.md) | Independent acceptance, live response compatibility, complete calculators, caller-side owner/version checks and integration into ranking. | 97 |
| Conversational Assistant · implemented on legacy route | Legacy chat uses current financial context, read-only snapshot, cash-flow, debt and category tools. Checks model numbers and unsafe claims, permits a bounded correction, and falls back to local text on failure. T24b independent test included 20 outcomes in the actual chat path with generation mocked plus 69 focused tests. [Safety review](../agents/reports/T24b-independent-rework2.md) | Conversation lives in the mobile view. No accepted cross-session history or new-account model-backed chat. Lexical tests do not establish universal factual or safety guarantees. | 98 |
| Account-backed Assistant · accepted local context | Current plan, activity, evidence and lessons come from a consistent revision. Screen provides deterministic explanation and read-only what-if. The integration kit verified bootstrap/Assistant parity. [Client review](../agents/reports/T75-independent.md) · [Screen](../../apps/mobile/src/app/shared-assistant.tsx) | T59 adds persisted owner conversations, contextual recommendation ID/version resolution, changed-facts explanations and distinct confirmation for proposed writes. | 97 |
| AI routing and usage controls · local implementation | Server-side gateway selects configured models, reserves quota, records usage and falls back on unavailable model or quota. Offline safety suite covers missing inputs, grounded numbers, injection, scope and tone. One historical live smoke is recorded, limited to the tested configuration. [Routing](../../policies/model-routing.json) · [Evaluations](../../evals/README.md) · [Gate record](../release-readiness.md) | Held-out live trials, measured cost/latency, preview-model approval and shared API/worker spend controls. | 96 |
| Learn, quizzes and progress · accepted module | Ten English lessons, related-action links, quizzes with feedback, saved progress and contextual readers. Browser maintenance restored access from connected navigation. [Content](../../content/lessons/index.json) · [T18](../agents/reports/T18.md) · [UI repair](../agents/reports/UI-02.md) | All ten content entries await human review. T60/T61 cover linking a reviewed lesson to the current decision and checking the whole learning journey. | 98 |

## Mobile experience and design

| Feature and stage | What works and how it was checked | Remaining scope | Certainty |
|---|---|---|---:|
| Connect, restore and navigation · local flow implemented, UI repairs in review | Local URL/token entry restores the requested allowlisted screen, or opens personal data. Connected routes cover the plan, Assistant, settings, import and learning. Legacy Today/Plan/Assistant remain for the snapshot path. Current account-backed screens share a separate plan. Navigation checks passed in this audit. [UI-02](../agents/reports/UI-02.md) · [Navigation](../../apps/mobile/src/lib/navigation.ts) | Owner/native acceptance and polished cloud sign-in. | 97 |
| Today, My Plan and adjustments · locally usable | Legacy Today shows advice, adjustment previews a custom amount, and Plan exposes obligations and action controls. UI repairs addressed cancellation when completion is unsafe, validation feedback and access to Learn. Browser checks exercised the transitions. [UI-01](../agents/reports/UI-01.md) · [UI-02](../agents/reports/UI-02.md) | Unified pilot Today with one published, versioned action and matching Assistant explanation remains T58/T59. | 96 |
| UI foundation and accessibility · T65 review | Shared typography, colors, neutral/green themes, reusable fields, feedback, buttons and target sizing. Web checks include a narrow viewport and measured controls. [Foundation](../agents/reports/T65.md) · [Web evidence](../agents/reports/UI-TEST-05.md) | Dynamic type, contrast in context, selection announcements, dark mode and VoiceOver/TalkBack on both platforms lack full evidence. | 95 |
| Explore example · T66 review | Separate in-memory pilot simulates onboarding, money actions, statement reading, evidence, Assistant, settings and failures. Browser follow-up verified repaired copy and evidence navigation. [Prototype](../agents/reports/T66.md) | Simulated state is discarded. Device and owner UX acceptance and binding to saved user data remain open. | 98 |
| First-page visual direction · reference selected | Owner chose the Soft Glass first-page reference. The original and preview are preserved. Earlier warm editorial samples also exist. [Reference record](../design/references/2026-10-31-soft-glass-first-page/README.md) | Selection applies only to the first page. No released, connected redesign follows from the reference. | 99 |
| Reminders and Add income shortcut · T68/T69 planned | Prototype validates time/interval and on/off preferences. In-app income entry exists. [Pilot spec](PILOT_SPEC.md) · [Prototype exercise](../agents/reports/UI-TEST-05.md) | Actual OS scheduling, permission denial, weekdays/every-N-days, timezone, cancellation, device sign-out and home-screen shortcut with authenticated resume await implementation. | 99 |
| Settings, export and deletion · mixed | Settings exposes export, destructive confirmation and disconnect. A developer browser run verified the UTF-8 exported JSON file against 56 rows and checked token absence. Independent download verification was blocked by browser tooling. Delete cancellation was exercised. [T73](../agents/reports/T73.md) · [UI-02](../agents/reports/UI-02.md) | T73 remains in review. Native sharing, actual device deletion and full account lifecycle lack acceptance. | 96 |

## Platform, privacy and release engineering

| Feature and stage | What works and how it was checked | Remaining scope | Certainty |
|---|---|---|---:|
| Email OTP/session adapter · T32 accepted | Request/verify email code, rotate refresh credentials, restore native sessions, single refresh on concurrent 401s, sign-out and clear old-account responses. Web adapter keeps cloud credentials in memory. Retry preserves the financial request body/key. 17 mocked tests passed here. [Session tests](../../apps/mobile/src/lib/session.test.cjs) | Current Connect screen asks for a demo token. Actual OTP screens, delivery/resend, second device and live provider session require integration/proof. | 99 |
| Authentication and owner isolation · accepted application layer | Local token mode is explicit. Cloud validates asymmetric signature, trusted key source, issuer, audience and expiry. Authenticated subject selects state, receipts, previews, originals and jobs. Foreign IDs cannot confer access. Isolated provider and API tests. [T32 review](../agents/reports/T32-independent.md) | Live direct database access denial, deployed RLS, real credentials and cloud cross-user tests. | 98 |
| Persistence, concurrency and schema migration · accepted bounded modules | SQLite state, expected revisions, command fingerprints/receipts, conflict responses. Alembic freezes the legacy baseline and adds original/job tables. Adoption checks preserve populated rows and guard dangerous downgrades. [Migration review](../agents/reports/T31-independent.md) · [Store](../../services/api/vela/store.py) | Disposable PostgreSQL upgrade/restore, concurrent workers and rollout rehearsal. | 98 |
| Data contract and frontend integration kit · accepted | Versioned split between analytical history and confirmed finances. Generated OpenAPI/mobile types, bootstrap data at one revision, a JavaScript client, prepared commands, exact-origin checks and isolated synthetic launcher. Independent real HTTP/client exercise. [Data contract](data-contract.md) · [T75](../agents/reports/T75-independent.md) | Launching the kit does not wire a standalone design to real data. The bootstrap capability flags describe the local kit. | 99 |
| PII masking and spreadsheet-formula escaping · accepted modules | Masks supported identifiers in outbound text. Raw original documents have a separate explicit processing gate. Formula escape helper handles dangerous prefixes while preserving numeric cells. JSON is the existing export format. [PII integration](../agents/reports/T21b.md) · [CSV utility](../agents/reports/T20.md) | No universal anonymization guarantee or shipped CSV export. Real provider/privacy review is open. | 97 |
| Private diagnostics and threat inventory · accepted | Allowlisted structured request logs and correlation IDs, including error responses. Threat model and data map address six trust boundaries and eight private tables at review. [T35](../agents/reports/T35-independent.md) · [T44](../agents/reports/T44.md) | External provider/proxy logs and updated inventories after new entities are separate responsibilities. CI security scanning is planned. | 98 |
| Export, erase and retained data · bounded backend implementation | Export serializes owner State. Deletion clears owner financial state and jobs, invalidates stale worker publication and attempts private original removal. Failed physical cleanup remains pending. Anonymous operational quota counters can remain. [Data map](../security/data-map.md) · [Storage](storage.md) | All-entity inventory/export, future chats, identity-provider deletion, backups and independently verified restore are T62. | 97 |
| Operations and launch budget · T70 accepted offline | Render API/worker templates, Supabase configuration, separate migration role, TLS checks, client-denial SQL and cost scenarios documented. Ten config tests independently passed. AI disabled for this deployment configuration. [Operations](CLOUD_OPERATIONS.md) · [T70](../agents/reports/T70.md) | No provisioned service established. Actual TLS, SQL permissions, private bucket, SMTP, distributed AI quota, measured capacity and owner activation remain open. | 99 |
| Development tooling and QA · mixed | Git baseline/phase tags, local startup/smoke, contract generator and drift check, backend runner, JS session/navigation/UI checks, synthetic fixtures, web build, eval harness, test runbook and user manual exist. [Local setup](../local-testing.md) · [Runbook](../TEST_RUNBOOK.md) · [User manual](../USER_MANUAL.md) | Launcher DEV-01 remains in review. Jest/RNTL setup, component coverage, Maestro on both platforms, CI/secret scanning, missing playbooks and final audit are tracked by T40–T46. | 98 |

## End-to-end acceptance

Each row rates confidence in the journey disposition. All twelve boxes remain open in the product plan. Browser checks used synthetic local data. A mobile screen, passing API test and approved cloud architecture can each supply evidence for different parts of the same journey. [Journey definitions](../../PRODUCT_PLAN.md) · [Browser checklist](../agents/reports/UI-TEST-05.md) · [Later account-plan review](../agents/reports/T74.md)

| Journey | Evidence available | What would complete the journey | Certainty |
|---|---|---|---:|
| J01 First visit · partial | Optional profile, unknown balance, no-goal plan, stored onboarding checkpoint. | Complete progressive entry/resume on the pilot UI. | 97 |
| J02 Return and isolation · partial | Local restart/reconnect recovered saved data. Session and owner isolation tested with mocked identity. | Real sign-in on a second device and isolated second account. | 98 |
| J03 Statement · partial | Parsing, durable job, preview and analytical apply work separately. Source corrections in review. | Actual mobile job resume, corrections and separate obligation confirmation in one run. | 97 |
| J04 Repeat/overlap · partial | Reimport of three statements preserves 56 rows and cash. Source review covers ambiguous overlap. | Accepted overlap decisions, manual-income/own-transfer evidence matching on one account. | 98 |
| J05 Delayed irregular income · open | Expected income stays distinct and cannot fund the current plan. | Multi-period delay/uncertainty scenarios and assumptions through recommendation. | 98 |
| J06 Two goals · open | One optional goal and one set of earmarks. | Priorities, deadlines and competing allocations without double counting. | 99 |
| J07 Debt decision · partial | Unknown terms prompt needs-input. Calculator compares supported repayment scenarios. | Current-account affordability, term clarification and distinct recurring vs one-off outcomes through UI. | 98 |
| J08 Action lifecycle · partial | Preview, reserve, complete/cancel, retry and stale revision guards proven locally. | Reconcile executed action to a transaction and cover all supported action types. | 99 |
| J09 Change during calculation · partial | Stale results and material changes tested in legacy coordination and bounded engine fixtures. | Same guarantee across stored new-plan publication, late specialist and Today. | 95 |
| J10 Assistant and lesson · partial | Read-only what-if, local explanation, quizzes and saved lesson progress. | Persistent conversation and reviewed lesson tied to the exact published decision. | 98 |
| J11 Failure/recovery · partial | Browser outage and conflict, local AI fallback, mocked FX failure, worker retry/lease recovery. | Integrated device/cloud run covering these failures and unsafe-action suppression. | 97 |
| J12 Export/delete/restore · partial | State export, owner erase, pending file cleanup, stale job guards. | Complete lifecycle and restore drill including provider/backups on a separate environment. | 98 |

## Pilot boundary and release decisions

**Local demo — demonstrated (99/100).** The strongest combined evidence is for EUR planning, retry-safe commands and the synthetic statement workflow. **Staging — blocked (99/100)** on deployed service and security evidence. **Real-data pilot — blocked (99/100)** on complete journeys, physical iOS/Android verification, measured reliability/cost, privacy and human financial review. **Public release — blocked (99/100)** on those prerequisites plus release signing, store disclosures and owner authorization. EAS profiles and an engineering checkpoint are preparation, not a signed build or a release decision. The older 14-gate matrix predates several accepted modules. [Release register](../release-readiness.md) · [Phase 3 evidence](../agents/reports/CHECKPOINT-3.md)

**Approved work still ahead (98/100).** T52–T63 cover connected onboarding, analytical corrections and evidence matching, uncertain income, multiple goals, full specialist coordination/publication, action execution, persistent conversations, reviewed education and preferences, full data lifecycle and journey/cost acceptance. T68/T69 add real local reminders and shortcut entry. T40–T46 cover mobile automation, operations documentation, CI and final release proof. The approved pilot excludes bank connections, executing money transfers or trades, daily expense bookkeeping, investments and a floating assistant/pet. [Approved scope](PILOT_SPEC.md) · [Backlog](../agents/BACKLOG.md)

**Ideas outside committed scope (98/100).** The plan separately proposes an inline source/correction affordance, a “what changed?” explanation, a single data center, broader gentle reminders and general draft resumption. The narrower local reminders feature is approved in T68. The proposal list alone authorizes none of the other extensions. [Product plan, section 8](../../PRODUCT_PLAN.md)


## Task register

The 70 status-bearing backlog cards break down into 12 review, 36 done, 21 todo, 1 in progress. These counts include documentation, fixtures and reviews as well as product features. They cannot be used as a completion percentage. Confidence in each transcribed status is 99/100 at the pinned revision. A parent marked todo can contain accepted child work. [Canonical backlog](../agents/BACKLOG.md)

| ID | Work item | Recorded stage |
|---|---|---|
| [DEV-01](../agents/reports/DEV-01.md) | Local launcher and smoke check | review |
| [T00](../agents/reports/T00.md) | Version control baseline | done |
| [T01](../agents/reports/T01.md) | Release gate register | done |
| [T02](../agents/reports/T02.md) | Project skill inventory | done |
| [T10](../agents/reports/T10.md) | Independent cash-flow acceptance fixture | done |
| [T11](../agents/reports/T11.md) | Minimum-balance forecast and invariants | done |
| [T12](../agents/reports/T12.md) | Debt engine | done |
| [T13](../agents/reports/T13.md) | Debt UI | done |
| [T14](../agents/reports/T14.md) | Eligible action catalogue | done |
| [T15](../agents/reports/T15.md) | Weighted ranking, sensitivity and evaluation evidence | done |
| [T16](../agents/reports/T16.md) | Coordination, cooldown and recalculation | done |
| [T17](../agents/reports/T17.md) | Lesson content | done |
| [T18](../agents/reports/T18.md) | Learning API, screen and progress | done |
| [T20](../agents/reports/T20.md) | Formula-safe CSV utility | done |
| [T21a](../agents/reports/T21a.md) | Personal identifier masking | done |
| [T21b](../agents/reports/T21b.md) | Masking before model calls | done |
| [T22](../agents/reports/T22.md) | Evaluation harness and scenario schema | done |
| [T22b](../agents/reports/T22b.md) | Safe local chat refusal | done |
| [T23](../agents/reports/T23.md) | Evaluation scenarios | done |
| [T24a](../agents/reports/T24a.md) | Financial explanation tools and number verification | done |
| [T24b](../agents/reports/T24b.md) | Guarded chat integration | done |
| [CP2-ENV](../agents/reports/CP2-ENV.md) | Expo patch alignment | done |
| [T30](../agents/reports/T30.md) | Cloud architecture decision | done |
| [T31](../agents/reports/T31.md) | Database migrations | done |
| T32 | Verified identity and session adapters | done |
| [T33](../agents/reports/T33.md) | Durable import queue and worker | done |
| [T34](../agents/reports/T34.md) | Private original-file lifecycle | done |
| [T35](../agents/reports/T35.md) | Correlation IDs and restricted diagnostics | done |
| T40 | Mobile component testing setup | todo |
| T41 | Mobile component test coverage | todo |
| T42 | Native Maestro journey suite | todo |
| T43 | Remaining design decisions and operational playbooks | todo |
| [T44](../agents/reports/T44.md) | Threat model and data map | done |
| T45 | Continuous integration and secret scanning | todo |
| T46 | Final readiness audit | todo |
| [T50](../agents/reports/T50.md) | Product data and migration contract | done |
| [T51](../agents/reports/T51.md) | Persisted financial profile and provenance | done |
| T52 | Progressive onboarding and profile editing | todo |
| T53 | End-to-end statement review and correction | todo |
| T54 | Uncertain income and multi-period scenarios | todo |
| [T53a](../agents/reports/T53a.md) | Source corrections and analytical reconciliation backend | review |
| T53b | Link imported rows to manual events and own transfers | todo |
| T55 | Multiple goals and allocation calculator | todo |
| T56 | Complete same-version specialist pipeline | todo |
| T57 | Shared publication and recalculation | todo |
| [T56a](../agents/reports/T56a.md) | Weighted current-account calculator | done |
| T57a | Publication and shared API for current-account engine | in_progress |
| [T56b](../agents/reports/T56b.md) | Profile-aware Gemini specialist adapters | review |
| T58 | Today and My Plan execution flow | todo |
| T59 | Persistent Assistant and safe what-if | todo |
| T60 | Reviewed contextual learning | todo |
| T61 | Preference calibration and human financial review | todo |
| T62 | Complete data lifecycle and recovery | todo |
| T63 | End-to-end vision, quality and cost verification | todo |
| [UI-01](../agents/reports/UI-01.md) | Browser findings and UI repairs | review |
| [T64](../agents/reports/T64.md) | Pilot specification, design guidance and skill cleanup | review |
| [T65](../agents/reports/T65.md) | Shared mobile UI foundation | review |
| [T66](../agents/reports/T66.md) | Isolated pilot navigation prototype | review |
| [T67](../agents/reports/T67.md) | EUR/HUF display valuation | done |
| T68 | Local reminders | todo |
| T69 | Home-screen Add income shortcut | todo |
| [T70](../agents/reports/T70.md) | Offline cloud configuration and cost estimate | done |
| [T71](../agents/reports/T71.md) | Local saved profile, accounts and income | review |
| [UI-TEST-05](../agents/reports/UI-TEST-05.md) | Full-workflow verification attempt | review |
| [UI-02](../agents/reports/UI-02.md) | Connected navigation and protected-route return | review |
| [PATTERN-01](../agents/reports/PATTERN-01.md) | Three monthly statements and expected results | review |
| [T72](../agents/reports/T72.md) | Analytical import and cumulative observations | done |
| [T73](../agents/reports/T73.md) | Browser JSON download | review |
| [T75](../agents/reports/T75.md) | Frontend contract, client and synthetic launcher | done |
| [T74](../agents/reports/T74.md) | Local EUR account-backed plan and explicit legacy adoption | done |

## Policy and learning inventory

Each action below is a defined catalogue entry (99/100). The first sections identify which calculations and controls people can actually use. [Action policy](../../policies/action-catalogue.v1.json)

1. Reserve money for an upcoming necessary expense.
2. Preserve available cash until a known payment.
3. Prepare a required debt payment.
4. Make an affordable one-off extra debt payment.
5. Propose a recurring extra payment with future affordability checks.
6. Compare supported repayment strategies.
7. Start/add to/rebuild a reserve.
8. Contribute to a savings goal.
9. Adjust a contribution.
10. Adjust a goal deadline or priority.
11. Review a recurring discretionary charge.
12. Pause an optional allocation.
13. Maintain the current plan.
14. Clarify a material unknown.
15. Suggest appropriate external assistance for an unresolved shortfall.

All ten lessons have a content entry and an outstanding human-review flag (99/100). [Lesson index](../../content/lessons/index.json)

- Building an Emergency Cushion
- Liquidity Buffer vs Long-Term Savings
- APR and the True Cost of Minimum Payments
- Debt Payoff: Avalanche vs Snowball
- Budgeting with Irregular or Variable Income
- Auditing Subscriptions and Recurring Charges
- Structuring Realistic Savings Goals
- Navigating a Cash Shortfall and Seeking Help
- How to Read and Reconcile Bank Statements
- Planned Steps vs Real Transfers

## HTTP surface at the audited commit

The committed API contract declares 64 distinct paths. The inventory below lists every documented method by path. Confidence in contract membership is 99/100. Runtime and release evidence for each family is given above. [OpenAPI contract](../../contracts/openapi.json)

| Path | Methods |
|---|---|
| `/health` | GET |
| `/v1/actions` | POST |
| `/v1/actions/{action_id}/cancel` | POST |
| `/v1/actions/{action_id}/complete` | POST |
| `/v1/ai/status` | GET |
| `/v1/chat` | POST |
| `/v1/confirm` | POST |
| `/v1/data` | DELETE |
| `/v1/debts` | GET, POST |
| `/v1/debts/simulate` | POST |
| `/v1/debts/{debt_id}` | DELETE |
| `/v1/decision` | GET |
| `/v1/decision/evaluate` | POST |
| `/v1/defer` | POST |
| `/v1/demo` | POST |
| `/v1/export` | GET |
| `/v1/imports` | POST |
| `/v1/imports/base64` | POST |
| `/v1/imports/jobs` | POST |
| `/v1/imports/{preview_id}` | GET |
| `/v1/imports/{preview_id}/apply` | POST |
| `/v1/income` | POST |
| `/v1/jobs/{job_id}` | GET |
| `/v1/jobs/{job_id}/cancel` | POST |
| `/v1/jobs/{job_id}/retry` | POST |
| `/v1/lessons` | GET |
| `/v1/lessons/{lesson_id}` | GET |
| `/v1/lessons/{lesson_id}/progress` | POST |
| `/v1/obligations` | POST |
| `/v1/obligations/{obligation_id}/done` | POST |
| `/v1/preview` | POST |
| `/v1/snapshot` | PUT |
| `/v1/state` | GET |
| `/v1/transactions` | GET |
| `/v2/accounts` | POST |
| `/v2/accounts/{account_id}/balance` | PUT |
| `/v2/assistant/context` | GET |
| `/v2/frontend` | GET |
| `/v2/imports/{preview_id}/apply` | POST |
| `/v2/imports/{preview_id}/review` | POST |
| `/v2/income` | POST |
| `/v2/observations` | GET |
| `/v2/originals/{file_id}` | DELETE, GET |
| `/v2/personal` | GET |
| `/v2/planning` | GET, PUT |
| `/v2/planning/adopt-legacy` | POST |
| `/v2/planning/bills` | POST |
| `/v2/planning/bills/{bill_id}/cancel` | POST |
| `/v2/planning/bills/{bill_id}/pay` | POST |
| `/v2/planning/defer` | POST |
| `/v2/planning/preview` | POST |
| `/v2/planning/resume` | POST |
| `/v2/planning/steps` | POST |
| `/v2/planning/steps/{step_id}/cancel` | POST |
| `/v2/planning/steps/{step_id}/complete` | POST |
| `/v2/profile` | PUT |
| `/v2/profile/details` | GET, PUT |
| `/v2/profile/onboarding` | PUT |
| `/v2/profile/preferences` | PUT |
| `/v2/reviews/{review_id}` | GET |
| `/v2/reviews/{review_id}/apply` | POST |
| `/v2/reviews/{review_id}/rows/{source_id}` | PUT |
| `/v2/reviews/{review_id}/rows/{source_id}/resolve` | POST |
| `/v2/valuations/accounts` | GET |
