# Vela — approved pilot specification

Approved by the owner on 2026-10-29. This document records the approved replacement product behaviour. Historical reports and USER_VISION.md remain intact. Implementation status is exclusively in BACKLOG.md; requirements here are not claims of completion.

## Product decisions

Personal cloud pilot for Android and iPhone, English UI, progressive discovery of the user's finances. Three tabs: Today, My Plan, Assistant. No mandatory statement or goal. No daily expense bookkeeping. No investments, money movement, bank connection, pet or floating assistant in this pilot.

Supabase Postgres/Auth/private Storage; email OTP; FastAPI and a separate worker on Render; Postgres jobs/outbox without Redis. Frankfurter v2, ECB provider, EUR/HUF first, EUR display total. Cloud costs, SMTP and credentials must be reviewed before paid activation. No deployment or purchases are authorized by this specification.

## User journeys

### Welcome and sign-in
“Understand your money. Choose your next step.” Get started enters email OTP; Explore an example opens explicitly isolated synthetic data. Support resend cooldown, expired/invalid codes, changing email, session refresh, sign-out and account-specific cache clearing. Returning users resume their saved onboarding step. Example data never becomes personal data.

### Progressive onboarding
1. “What would you like help with?” Spending, cushion, debt, a goal, or Not sure yet. Optional goal name; target and date may follow later.
2. Account name (Main account initially), currency, known balance and date. More accounts can be added. Missing balance is unknown, not zero.
3. Income regular/irregular/mixed, approximate amount or range, frequency and optional next date. Expected income does not add cash.
4. Ask about obligations, essential expenses and debt when needed for a decision. Allow Not sure/Add later. Do not manufacture complete-obligations flags or hidden demo defaults.
Each step persists and can be resumed. No statement required to reach Today.

### Today
Known balances with dates; one next step or material clarification; optional goal progress; Add income/Update balance; settings icon. An action shows action, practical benefit, amount/date when justified, one primary CTA, adjust/defer and an accessible information icon. The icon opens Assistant with recommendation ID and version. Preserve an accepted eligible action instead of producing a new task on each visit. Maintaining the plan is a valid outcome.

### Money updates
Update balance replaces the known account balance and records a dated adjustment; its difference is not invented income or expense.
Add income captures account, currency, amount, received date and optional label. Show current balance/date and ask whether already included: add to balance, record only, or replace with a current balance when unsure. Idempotent commands prevent retries adding income twice. Prior-day account data requires confirmation/update before accepting a money action. Expected and received income remain distinct.

### Statements
Optional entry from settings/data, Assistant or a contextual suggestion. Explain purpose and external AI processing before consent. Show upload/read/review stages, resumable job status, unsupported/password-protected/partial-file errors. Review currency, account, period, questionable rows, and all transactions with pagination. Corrections retain originals and provenance.
**Import, reimport and analytics never change balances, saved money, debt or action completion.** A detected obligation requires a separate confirmation command. Historical statement balances are analytical evidence only. Deduplicate exact and overlapping imports; ambiguous matches require review. Matching a manual income/action to an imported row links evidence and does not apply the event again.

### Behaviour analysis
Categories/payees, recurring payments, possible subscriptions, price changes, fees, repeated small payments, comparable-period changes, income regularity, within-period/post-income distribution, possible duplicates/refunds/own transfers. Each observation records period/coverage, evidence transaction IDs, calculation method, version, user response and status (suggested/confirmed/rejected/insufficient data). Short or partial periods cannot establish long-term habits. Never infer motives, diagnoses or that a subscription is unnecessary without asking the person.
Keep analysis in the background. Assistant offers Review my spending/Check recurring payments; relevant observations can support a single next step. No Insights tab or mandatory long report.

### My Plan and execution
Accepted step, goals, upcoming confirmed obligations, compact debt summary, separate history. Multiple goals have currency, target, saved amount, optional date, explicit priority and pause/completion states. The same money cannot fund multiple allocations. User confirms reserve and contribution preferences; literacy changes explanations, not saving percentages.
Debt calculations require confirmed relevant terms; missing terms block only dependent calculations. One-off and recurring extra payments are separate scenarios.
Actions: proposed/planned/completed/deferred/cancelled/requires review. Acceptance reserves affordability without changing cash. Adjustment is a preview until confirmed; cancellation releases reservation. Completion distinguishes earmarking, own-account transfer, bill/debt payment and subscription cancellation. Own transfers preserve total money. Future savings are not current income. Payments already reflected in a balance are not subtracted again. New facts invalidate unsafe actions before execution.

### Assistant and learning
Persist conversations across sessions/devices. Explain my next step/Review my spending/Check recurring payments. Information-icon entry resolves server recommendation ID/version, labels changed facts, and gives brief explanation before detail. What-if is read-only. Any proposed write requires a distinct confirmation with consequences. Optional reviewed lessons are contextual and also reachable through Learn inside Assistant.

### Reminders and shortcuts
Off until explicitly enabled. Daily, selected weekdays or every N days; user time; plan/balance reminder and optional action reminder. Ask OS permission after choosing; denial does not block use. Neutral notification text without amounts/debt names. Open current state, cancel action reminder when action cancelled. First pilot uses expo-notifications local schedules; account preferences sync, reception is enabled per device. Handle timezone changes, sign-out and permissions revocation. Home-screen Add income opens the form, never writes; resume intended form after sign-in.

### Settings and failures
Profile, accounts, income, preferences, documents, reminders, export/delete. Loading/empty/error/offline/stale/conflict/AI-unavailable/background-processing states are part of every affected flow. Offline reading is limited to cached current-session data; drafts remain editable, commands cannot appear successful before server acknowledgement.

## Data and API
Separate confirmed finances, historical observations, preferences, and derived calculations/publications. Every record has ownership and relevant source/date/version. New contract uses /v2; keep /v1 compatibility explicit. Financial commands carry expected revision and idempotency identity. Use server-authenticated owner, not request user_id. Recommendation explanations reference stored IDs/versions, not client assertions.
Contract groups: profile/preferences; accounts/balance confirmations; expected/received income; obligations/debts/goals/allocations; import jobs/rows/observations; recommendations/actions/executions; conversations/explanations; reminder preferences; export/deletion jobs.
Integer minor units with currency; Decimal FX, no binary float. EUR/HUF originals preserved; other currencies explicitly unsupported for calculation. Latest published ECB rate for present overview; historical transaction date or last preceding published rate for analytics. Cache rate/source/date; round once at output currency minor unit. Missing rate gives original amounts and incomplete total, never zero. Estimated conversion does not make funds available in another currency.
One immutable financial/preference version feeds spending/debt/goals specialists, calculator consequences, hard constraints, ranking, robustness and atomic publication. Today and Assistant share that publication. Remove competing legacy recommendation generation from the new path. Existing scoring remains explicitly provisional; no invented percentages or income certainty weights. Human calibration precedes expansion beyond private pilot.

## Reliability, privacy and migration
Worker jobs/outbox survive restarts; retries idempotent, stale results rejected. AI failure cannot hide confirmed financial data. Run analysis on data changes, not visits; avoid repeated paid extraction, share structured evidence instead of entire documents, measure cost/latency by operation without financial payloads in logs.
Migrate a copy of populated local DB first; preserve dates, amounts, provenance and history. Mark demo defaults unconfirmed; classify historical rows as analytics. Uploading local data to cloud is a separate owner action. Check compatibility and restoration without deleting working DB.
Private originals expire 30 days after upload; deny access at expiration, retry physical deletion on failure. Confirmed analytical rows persist separately. Distinguish delete original from delete analysis; account deletion covers all user data/jobs/chat. Deleted users cannot be resurrected by jobs. Document provider backup lifecycle; do not promise instant backup erasure.

## Delivery and acceptance
A: product records/skills/backlog. B: isolated synthetic Expo navigation prototype. C: T24b independent review + CHECKPOINT-2 before real cloud data; T30/T50 then T31/T32/T51/T33/T34. D: onboarding/accounts/income/goals/manual path. E: analytical import/patterns/FX. F: shared recommendation/actions/chat/lessons. G: reminders/shortcut/operations and pilot verification.
Test: no goal/statement; skip/resume; second device; both income modes; retry; balance replacement; HUF import without financial mutation; overlap import; corrections; short-period limits; reserve/cancel/complete; concurrent revision; contextual explanation; what-if; AI/FX outage; reminders; cold-start shortcut; document/account deletion; deleted-user worker race. Record date/build/device and distinguish automation, real UI and owner acceptance.
Pilot requires both mobile platforms, isolation/persistence/export/delete/restore evidence, measured cost/latency, reviewed financial policy, agreed deployment estimate. No completion percentage or done status without evidence.

## Sources
- https://frankfurter.dev/
- https://supabase.com/docs/guides/auth/auth-email-passwordless
- https://supabase.com/docs/guides/storage/buckets/fundamentals
- https://docs.expo.dev/versions/v58.0.0/sdk/notifications/
- https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum
