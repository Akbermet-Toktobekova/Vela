# Vela product data contract

Version: `product-data-v1`, 2026-10-29. Design contract for T50, not a claim that all entities/endpoints exist. Read with [ADR 0001](../adr/0001-database-and-auth.md), [ADR 0007](../adr/0007-product-data-contract.md), [approved pilot](PILOT_SPEC.md) and [BACKLOG](../agents/BACKLOG.md). PILOT_SPEC supersedes older product wording: statement analytics never update balances, allocations, debt or action completion.

## Ownership, facts and versions

Each private aggregate belongs to one authenticated owner. The server derives that owner from the verified session; body `user_id`, storage path, job payload or client recommendation text cannot establish authority. Child references must resolve within the same owner, including accounts, source rows, goals, executions, receipts, files and publications. Public versioned policies/lesson content are separate from private progress and personal calculator inputs.

Logical records may remain grouped in an owner aggregate; this document does not require one SQL table per entity. Separate storage is justified for atomicity, ownership, independent expiry, queue leases or query needs. T31 retains the existing store tables before subsequent scoped migrations extend them; T32 tests every owner boundary.

- **Confirmed finances:** dated balances, received-income events, explicitly confirmed obligations/debt terms, allocations and executions. A source document or classifier alone is not user confirmation.
- **Historical analytics:** immutable source rows plus corrections, normalized transactions, coverage and suggested observations. These explain history and never fund current affordability.
- **Preferences:** explicit user choices, onboarding progress, restrictions, goal priorities and reminder choices. Refusal/defer is action history, not an inferred psychological preference.
- **Derived results:** calculator scenarios, specialist packages and recommendation publications, tagged with exact input versions. They cannot overwrite facts or preferences.

Every owner-visible mutation retains relevant record ID, event/source date, confirmation state and provenance. Use explicit `null`/unknown for absent values; a confirmed zero is distinct. Unknown debt terms/obligations coverage cannot become zero/complete through model defaults. Historical defaults remain visible as unconfirmed legacy data until reviewed.

Keep the existing shared integer `revision` for optimistic command concurrency and receipt replay. Financial/preference input versions, policy version and calculation/method version identify immutable analysis inputs when T51/T56/T57 add their separate lifecycles; no-op reads and speculative scenarios do not create financial events. Chat/progress storage must not silently claim a changed financial fact. All fields required to interpret a publication remain recoverable with that publication.

## Money, dates and provenance

Amounts are integers in the currency's explicitly declared minor units. Integer JSON fields must remain within the receiving client's exact safe-integer range; existing narrower domain limits remain enforced. Larger values require an explicitly versioned decimal-string contract, not silent precision loss. Original EUR/HUF currency is retained at account/record boundaries; never sum currencies as if interchangeable. Use Decimal FX, source/rate-date and one output rounding under T67; missing FX leaves original values and an incomplete total. A display conversion cannot make another currency available for a plan. New endpoints reject unsupported currencies for dependent calculations rather than silently convert them.

Calendar dates identify balance confirmation, receipt, bill due, planning horizon and source-row date. Operational timestamps identify upload/processing, corrections and sessions; preserve the associated timezone/date meaning. A future expected credit is not a received event. Input freshness and debt/coverage requirements gate only dependent calculations; unknown data does not block reading or optional onboarding.

Provenance links distinguish manual confirmation, original import row, correction, analytical inference, legacy data and synthetic example. Corrections retain original values and their author/date; deleting an original must not orphan the analytical source metadata required to explain a confirmed row. Do not invent provenance or retroactively label old defaults user-confirmed.

## Logical aggregates and command effects

### Profile, accounts and income

Profile owns optional focus, income type/range/frequency/next expected date, explicit restrictions/preferences and resumable onboarding step. A target/name/date can remain incomplete. T51/T52 own this persistence; no hidden goal or statement is required.

Account owns currency and dated balance confirmations/adjustments. Update balance records a replacement observation, not income/expense inferred from its difference. Received income owns stable event ID, account, original currency/amount, received date, optional label and confirmed effect: **add** to a known compatible balance; **included** records only; **replace** records the income and a separately entered current balance. Retry must not apply an effect twice. Existing T71 `ReceivedIncome` inherits currency through its same-owner account; new wire/storage expansion records currency explicitly without breaking the old shape. Expected income stores an estimate/range/frequency/date and stated certainty, separately from received events; it never silently adds cash. T54 defines supported scenarios without guessed probability weights.

### Obligations, debt, goals and allocations

Obligations own amount/currency/due date, status, coverage confirmation and optional evidence link. A detected recurring payment remains suggested until separately confirmed. Bill/debt payment execution explicitly says **subtract** versus **already reflected** in a confirmed balance; linking a statement later does not subtract again.

Debt owns confirmed relevant terms and unknown/unsupported markers. A recurring loan debit is evidence to ask about debt, not an inferred balance/APR. One-off and recurring extra-payment scenarios remain distinct. T54/T56 use the existing supported debt calculator and expose missing terms.

Goal owns stable ID, currency, optional target/date, explicit priority, reserve/known-expense purpose and active/paused/completed state. Allocation owns account/goal references, amount/currency, reserved-versus-earmarked state and originating action/execution. Multiple goal views sum the same allocation records rather than copy money. T55 migrates the existing single goal; unconfirmed legacy saved amounts require provenance. No goal is a valid state.

### Actions and execution evidence

An action references its immutable recommendation ID/version and owner input versions, action type, amount/currency where applicable, timing, explicit status and consequence calculation. The supported lifecycle is proposed/planned/completed/deferred/cancelled/requires-review. Preview/adjustment is read-only until a distinct confirmed command. Accept reserves affordability without changing cash; cancel releases that reservation. A stale or newly unaffordable action cannot execute.

Execution has a stable event identity and an explicit kind: earmarking, own-account transfer, bill/debt payment, or subscription cancellation. The endpoint must distinguish them rather than treating every completion as cash subtraction. Earmarking reclassifies an allocation; own transfer preserves total money and links both owned accounts; payment records the selected balance effect; subscription cancellation does not fabricate refund/savings/income. Unsupported execution kinds remain unavailable until their T58 implementation is accepted.

Manual events and imported transactions connect through evidence links to the existing execution/income/adjustment, not a second monetary event. Exact retries reuse receipt identity; ambiguous matches require user review, with a recorded decision/correction history. T53/T58 enforce this across import and action lifecycles.

### Imports, observations and original files

Import job owns owner, file reference, parser/method version, stage/status, retry/lease metadata and input generation. Original file metadata owns checksum, media type, upload time and expiry; private originals expire30days after upload under T34, with access denied at expiry and physical deletion retries. Queue/outbox transitions under T33 survive restarts and reject stale/deleted-owner results.

Source row owns original row identity/values and source file/job lineage; normalized transaction owns reviewed fields, currency, category, booked/pending status where supplied, source references and reconciliation decision. An absent booking status is unknown, not automatically booked. Opening/closing statement balances are historical evidence only. Exact/overlapping imports retain stable links and do not duplicate analytical rows or confirmed financial effects. Similar date/amount/merchant alone must not erase a genuine repeated purchase. Uncertain overlaps stay unresolved. Preview can be discarded without changing confirmed finances. External AI processing consent records owner, purpose, notice/version and choice before the permitted document processing; an upload alone is not blanket consent.

Observation owns ID, evidence-row IDs, covered period/completeness, calculation/method version, status suggested/confirmed/rejected/insufficient-data and explicit user response history. Current T72 supports suggested deterministic evidence; durable responses and richer coverage arrive in T53/T56. Do not infer motives, diagnoses, unnecessary subscriptions or long-term habits from short/partial history. Confirming an observation is not a financial write.

### Publications, Assistant, learning and reminders

Specialist packages reference one immutable financial/preference/policy input bundle and explain missing inputs. A recommendation publication owns stable ID/version, evaluated alternatives, calculator results, practical benefit, assumptions and eligibility/robustness outcomes. T57 atomically publishes the current primary pointer only when those inputs remain current; preserve an accepted eligible action. Today and Assistant resolve the same publication; stale explanation requests identify changed facts rather than silently substituting old sums. No hidden chain-of-thought is stored.

Conversation/message records belong to the owner with bounded model context and relevant publication/input references. Historical message text stays historical; current facts come from a fresh projection. What-if returns explicit assumptions/results and never mutates full financial State. Any proposed write uses a separate confirmed financial command. T59 owns persistence/export/delete and rejection/fallback through accepted T24b.

Public lesson content owns content/source/review version; private lesson progress owns owner, lesson version and voluntary answer/completion event. Personal figures come from a valid current calculation. T60/T61 never turn unreviewed content into reviewed content automatically.

Reminder preferences belong to the owner and default off; device permission/local schedule state remains per device. T68 syncs explicit preferences, handles timezone/sign-out/action cancellation and neutral content. Enabling a preference is not evidence of OS permission or delivery. Home-screen shortcut opens a form only (T69).

Export/deletion operations cover all private aggregate data, evidence links, files/previews/jobs/outbox, conversations, progress and receipts under T62. Original-only deletion and analytical-data deletion are distinct from whole-account deletion. Deletion invalidates work so old jobs cannot recreate records; backup/counter retention is separately documented and not represented as immediate erasure. Secrets/session tokens are not export fields.

## Current implementation and compatible API evolution

Current `State` contains `revision`, legacy `snapshot/actions/history/income_ids/deferred/transactions/debts`, and expanded `personal`. `PersonalState` contains profile markers, accounts, received incomes and one `PlanningState`; that plan binds one EUR account to protected money, bills, goal, steps and deferred state. There are no persisted multi-goal, expected-income, conversation or reminder aggregates yet.

Store tables currently hold owner-keyed `demo_state` JSON, `command_receipt`, `import_preview`, `coordination_run` and `published_recommendation`. Retain their identities and full payloads during T31 baseline migration. Later migrations may add aggregate fields/tables only when required by the corresponding task; preserve nullable unknowns and existing history.

T75 `/v2/frontend` is a read-once, same-revision projection of `personal` plus deterministic Assistant plan/activity/observations/lessons and capability flags. `/v2/assistant/context` and planning preview are read-only. `local-frontend-v1` is a projection contract version, not persisted data schema version or immutable recommendation publication. Current local capability flags correctly deny cloud OTP, multi-user, persistent chat, multi-goal and server reminders; only completed future implementations may enable them.

Retain existing `/v1` endpoints and response shapes for explicit legacy compatibility; keep accepted T74 post-adoption legacy-write/read guards. Original snapshot/history remain exportable but cannot become a second writable current balance. New product endpoints evolve under `/v2` by scoped tasks, generated OpenAPI/types and regression tests; do not rename or silently repurpose existing money fields. `/v2/imports/{id}/apply` is analytics-only. `/v1/imports/{id}/apply` retains documented legacy semantics and is not the target product contract. Clients use capabilities and the canonical plan path rather than assuming every legacy operation is supported after adoption.

Financial commands require expected current `revision` and a stable `Idempotency-Key` for each confirmed action. Replay the exact payload/key after lost responses; changed payload/same key or stale revision produces conflict without partial effects. After conflict refresh current facts and ask the user to reconfirm changed consequences. A receipt's historical result does not authorize bypassing current mode/safety gates or present old facts as current. Keep owner-scoped receipt fingerprints and tested T74 guard semantics.

Future route groups are profile/preferences, accounts/balances, received/expected income, obligations/debts/goals/allocations, imports/jobs/rows/observations, recommendations/actions/executions, conversations/explanations, reminders and export/deletion. Their task must publish exact wire schemas before clients depend on them; this contract deliberately creates no unimplemented route promise. Provider auth/session contracts follow ADR0001/T32/T52.

## A–J ownership and implementation trace

- **A — Progressive profile:** owner profile/preferences, onboarding and account facts; T32/T51/T52/T54.
- **B — Import/reconciliation:** owner files, jobs, source/corrected rows and reconciliation links; T33/T34/T53/T62.
- **C — Cash flow/spending:** owner confirmed dated inputs and analytical evidence; versioned derived scenarios/observations; T54/T56.
- **D — Debt:** owner debt terms/obligations/executions; derived supported debt scenarios; T54/T56/T58.
- **E — Savings/goals:** owner goals/priorities/allocations; derived contribution scenarios; T55/T56.
- **F — One recommendation:** owner-scoped immutable input bundle, specialist results and publication/current pointer; shared versioned policy; T56/T57/T61.
- **G — Plan/actions:** owner action/reservation/execution/evidence history; T53/T58.
- **H — Assistant:** owner conversations and explanation/scenario references; verified calculations and output boundary; T24b/T59/T63.
- **I — Learning:** shared reviewed content/version and owner progress; T60/T61.
- **J — Reliability/privacy:** verified owner/session, schema versions, receipts/jobs/files, deletion/export and recovery evidence; T30–T35/T40–T46/T62/T63. Reminders/shortcut preferences add T68/T69.

## Migration, preservation and rollback acceptance

T31 starts from disposable populated **synthetic** legacy fixtures, including old snapshot-only JSON, expanded personal/planning data, receipts, previews, runs and publications. Never read or mutate working `demo.db` or API8000–8003 as migration fixtures. T50/T31 do not authorize local-to-cloud upload or automatic ownership reassignment. Cloud migration requires an explicit owner action and verified target identity after applicable gates.

Use additive, versioned expansion with a documented reader/writer compatibility boundary. Preserve old raw payload/provenance alongside normalized records where required; map a source identity once and retain references. Backfill absent new optional fields as unknown/empty where semantically valid, never as financial zero, complete obligations, confirmed goal or received income. Current strict JSON readers may reject added fields: no claim of old-binary compatibility without a passing reader test. Keep legacy `/v1` projection/adoption rules under regression while new `/v2` records become canonical.

Before accepted migration, compare exact minor-unit amounts/currencies, dates, unknowns, account/goal/action links, full history, receipts/fingerprints and analytical source lineage. Prove restart and owner isolation, export equivalence of preserved facts, no duplicate retry/import effects and deleted-owner worker races at their tasks. Destructive downgrade cycles run only on disposable databases. Restoration uses a preserved isolated copy/export and supported schema/application pair; never downgrade a populated working database in place. T62 records actual restore evidence and external-storage/backup limits.

## Explicit decisions and unsupported policy

Existing provisional scoring, protected balance and saving-policy values remain provisional/user-confirmed as already implemented. This contract supplies no new saving percentages, thresholds, certainty probabilities, fee assumptions, debt-product support, confidence scores or calendar horizon rules. Missing parameters give clarification/unavailable dependent calculations. T54/T55/T56 must expose scenario assumptions; T61 requires explicit preference calibration and human content/policy review. Paid activation, provider backup promises, region/market-specific financial rules, device acceptance and operational budget remain their existing gates, not implicit decisions by a schema author.
