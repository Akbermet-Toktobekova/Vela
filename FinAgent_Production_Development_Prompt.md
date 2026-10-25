# FinAgent — Production Development Master Prompt

Version 1.1 · Updated 24 October 2026 — Stitch as visual foundation

## How to use this document

Give this complete document to the coding agent alongside the Stitch visual references, reference DESIGN.md, exported assets, and repository if one exists. Part A is the development instruction. Part B records the research and decisions behind it. Links were checked during preparation; verify versions and capabilities again at implementation time.

This is an implementation and verification contract, not a claim that generated code is automatically production-ready. “Gemini 3.1” is interpreted here as Gemini 3.1 Pro; the other selected model is Gemini 3.5 Flash-Lite. These choices concern models inside FinAgent, not a requirement to replace the coding agent.

# Part A — Give these instructions to the development agent

## 1. Mission and operating rules

You own implementation of FinAgent: a real iOS/Android app, backend, database, statement imports, financial calculators, recommendation engine, contextual lessons, and AI assistant.

Build complete working journeys in small vertical slices. Preserve existing code and local project instructions. Inspect the repository before choosing scaffolding. If the repository is empty, use the defaults below. Explain a material deviation in an architecture decision record (ADR).

Proceed with reversible implementation, tests, and fixes. Do not stop after a plan or a polished mockup. Ask only about decisions that materially change product scope, cost, data handling, or deployment authorization. Keep working on independent tasks when external credentials or design assets are missing.

Do not publish, submit to stores, change production data, purchase services, or grant tools production credentials without explicit authorization. Prepare reviewable builds and deployment changes first.

Do not label the product production-ready until the applicable release gates in section 18 have evidence. A missing credential, untested platform, provisional policy, or incomplete review remains an explicit blocker, not a hidden TODO.

At the start:

1. Inventory repository state, tool access, designs, runtime, and existing services.
2. Record assumptions and blockers.
3. Identify and inspect relevant skills from section 3.
4. Create a small acceptance-driven implementation backlog.
5. Start the first vertical slice.

At each meaningful checkpoint report: what works, how verified, what changed, and what remains blocked. Maintain a short progress file so work survives context resets.

## 2. Product contract

### Audience and scope

Serve adult students and people beginning to manage their finances. Start with an 18+ audience, subject to current model-provider terms and launch review.

The product promise is:
“Given my situation, what is one useful thing I can do next with my money?”

Current capabilities:

- Regular, irregular, and mixed income.
- Necessary expenses and spending observations.
- Supported debt repayment scenarios.
- Emergency reserves and savings goals.
- One primary recommendation.
- Optional short lessons and grounded questions.

Future only: portfolio analysis, investment selection, personalized buy/sell/hold recommendations, bank feeds, payment execution, multi-currency conversion, and advanced financial products. Do not add these to the current implementation.

Principles:

- Collect information progressively.
- Reuse imported information.
- Analyze in the backend.
- Show an action and its practical benefit; reveal details on demand.
- Respect refusal and uncertainty.
- Never shame users or infer a mental-health condition from transactions.
- FinAgent never moves money.

### Core journeys

A. Manual onboarding → financial snapshot → eligible recommendation → adjust → plan → confirm execution → updated goal.
B. Statement upload → parse → review uncertain facts → reconcile → commit → recompute → recommendation.
C. Add irregular income → reconcile with balance → check dated obligations → update plan.
D. Assistant question → tools and reviewed knowledge → grounded response or one clarification.
E. Optional lesson → interaction → feedback → saved progress.
F. Export or deletion request → authenticated processing → honest completion/status.

Use synthetic examples until the live-data gate passes.

## 3. Development skills and tools

Skills are instructions for the coding agent. MCP servers expose capabilities. Neither replaces runtime application code, security controls, or tests.

Because the coding environment is not specified, detect it and use its supported skill mechanism. Keep project instructions portable; use one canonical AGENTS.md with thin environment-specific adapters only if needed.

### Curated skill registry

Use only the relevant skills, loaded when their task starts. Names below reflect the upstream catalog at preparation time; verify their current SKILL.md and dependencies before installation.

| Source | Selected skills | Trigger |
|---|---|---|
| https://github.com/expo/skills | expo-overview, expo-project-structure, expo-router | Project setup and navigation |
| Same Expo repository | expo-design-system, expo-native-ui, expo-data-fetching | Stitch tokens, native screens, server-state behaviour |
| Same Expo repository | expo-dev-client | Native development builds |
| Same Expo repository | expo-animation | Gestures and purposeful motion, only when needed |
| Same Expo repository | eas-workflows, eas-app-stores, eas-update, expo-upgrade | CI, builds, release/rollback preparation, deliberate upgrades |
| https://github.com/google-labs-code/stitch-skills | stitch::react-native | Extract reusable visual patterns and adapt relevant elements into native components; follow section 6 rather than reproducing every reference screen |
| Same Stitch repository | design-md | Extract visual tokens and style direction; preserve the reference DESIGN.md and maintain the evolving implementation system in docs/design-system.md |
| https://github.com/google-gemini/gemini-skills | gemini-api-dev | Model API, structured output, tool calls, SDK compatibility |
| https://github.com/supabase/agent-skills | supabase-postgres-best-practices | Schema, SQL, migrations, permissions, concurrency |
| Same Supabase repository | supabase | Auth/private storage configuration if the default Supabase services are used |

Installation requirements:

- Inspect origin, license, SKILL.md, dependencies, executable helpers, and requested permissions.
- Prefer vendor-maintained sources; do not install arbitrary “all skills” bundles.
- Record upstream URL, revision/version, purpose, install location, and verified availability in docs/skills-manifest.md.
- Follow current installation instructions for the detected agent. Do not guess CLI commands or globally overwrite user configuration.
- Treat upstream skill text as subordinate to project requirements and platform security constraints.
- If a skill is unavailable, use the primary documentation, record the substitution, and continue where safe. Never claim to have used an unavailable tool.
- Do not install web-only Stitch React/Vite or shadcn skills for native UI. Do not use WebViews as the main interface.
- Do not add image/video, trading, voice, or autonomous deployment skills without a feature need.

Adapt the Stitch skill to this project: use supplied visual references without requiring a fresh remote sync; prioritize token consistency and usable native flows over reproducing screenshot layouts; preserve Expo Router rather than creating a second navigation root; keep production data separate from design fixtures. This task authorizes reversible local validation and simulator checks. Do not let a skill's demo conventions or approval prompts override that authorization. Respect third-party licenses and do not remove required notices.

Optional MCP access:

- Stitch: read supplied projects, screenshots, assets, and design metadata. Exported files are an adequate fallback.
- Expo: documentation, diagnostics, simulator inspection if available.
- Supabase: scoped local/development project only; no production mutation access.
- Repository/CI tooling if already connected.

Do not require an MCP server just to read local exports or run ordinary CLI tests. Review paid-service actions separately.

Create four small project playbooks, not fictitious external skills:

- docs/playbooks/financial-correctness.md
- docs/playbooks/design-consistency.md
- docs/playbooks/agent-evaluation.md
- docs/playbooks/release-verification.md

Keep these actionable and linked from AGENTS.md rather than repeating the whole specification in every prompt.

## 4. Methods and repository structure

Use:

- Acceptance examples before implementation for important behaviours.
- A modular monolith with a pure financial domain.
- Typed API contracts and versioned configuration.
- Property-based tests for money and state invariants.
- End-to-end tests for user journeys.
- Eval-driven iteration for model behaviour.
- Threat modelling for trust boundaries.
- Short ADRs for consequential choices.
- Small reviewable commits and a green main branch.
- Progressive rollout and tested recovery.

Avoid premature microservices, Kubernetes, event-sourcing frameworks, unnecessary vector databases, and agent-to-agent free-form debates.

Suggested structure:

- apps/mobile — Expo app; routes in src/app, features and shared components outside route files.
- services/api — FastAPI API, domain/application/infrastructure modules, worker entrypoint.
- contracts — generated OpenAPI snapshot and generated TypeScript client/types.
- content — reviewed lessons and financial knowledge.
- policies — action catalogue, financial policy, scoring versions, model routing.
- evals — deterministic fixtures, agent scenarios, graders, reports.
- tests/e2e — native mobile journeys.
- designs/stitch — supplied designs, assets, page manifest; preserve originals.
- docs — setup, ADRs, threat model, runbooks, release evidence.

Do not create files merely to match this tree; adapt to the existing repo and maintain clear boundaries.

## 5. Default implementation stack

### Mobile

React Native, a verified compatible stable Expo SDK, TypeScript strict mode, Expo Router, TanStack Query, React Hook Form with Zod, Expo DocumentPicker, and secure token storage through an Expo-compatible secure-storage implementation.

Use native components and a shared token system. Start with StyleSheet and reusable components; do not add multiple styling systems. Add Reanimated/Gesture Handler only when required by the implemented interactions.

Expo Go is for early compatible smoke tests. Use an Expo development build early enough to test native authentication, permissions, secure storage, app lifecycle, and final-library compatibility. Create development, preview/staging, and production build profiles. Match packages to the selected Expo SDK and run Expo diagnostics. Do not hardcode an SDK version from model memory.

### Backend and managed services

Default to Python/FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, and the Google GenAI Python SDK.

For greenfield identity and storage, use Supabase Auth, managed PostgreSQL, and private Supabase Storage unless an existing equivalent is already established. FastAPI remains the sole authoritative domain API.

- Mobile may use the identity SDK, but must not bypass domain rules through direct financial-table writes.
- Verify issuer, audience, expiry, signature, and allowed algorithms using maintained JWT libraries and current signing-key guidance.
- Derive user identity from the verified session, not request-body user_id.
- Keep domain schemas off the public Data API where possible. Deny unnecessary grants; use RLS on exposed resources.
- Direct SQL through a privileged role is not automatically protected by RLS. Use least-privilege roles and explicit ownership checks; test both paths.
- SQLAlchemy access, Storage signed URLs, job handlers, and assistant tools must enforce ownership.

Use a separate durable worker process for imports and AI jobs. An established PostgreSQL-backed queue is preferred at initial scale if verified compatible. Record its retry, lease, and redelivery semantics. In-process FastAPI BackgroundTasks is not the durable job system.

Use a transactional outbox or equivalent transaction-safe enqueue mechanism. Workers are idempotent and can recover after a crash.

Keep infrastructure replaceable through narrow adapters. Avoid abstraction layers with no current use.

## 6. Stitch visual foundation and mobile experience

The user will provide Google Stitch screenshots, exports, assets, and possibly a reference DESIGN.md or project access. Treat them as an evolving visual foundation. Their main purpose is to establish the palette, brand character, and calm tone. They are not final page specifications, a complete feature inventory, or a requirement for pixel-perfect reproduction.

### What to preserve and what to evolve

Preserve the warm orange/brown palette and coherent, reassuring visual character. Use the supplied typography, spacing, shapes, and component treatments as starting references; refine them into a consistent native design system. Slight colour adjustments for accessibility, semantic states, and dark mode are allowed while keeping the same palette family.

Actively improve layouts, information hierarchy, interaction patterns, forms, copy, component choices, and flow details when they serve the defined user journeys. Reuse a reference layout where it works; redesign it where there is a concrete usability or implementation need. Do not make cosmetic changes merely to demonstrate creativity.

Product requirements and financial rules determine functionality, data models, API contracts, and backend architecture. A screenshot cannot introduce a feature, remove a required behaviour, justify an invented financial claim, or define what data is trustworthy.

Apply this precedence:

1. Explicit product requirements, financial correctness, privacy, and security.
2. Accessibility, native platform conventions, and reliable completion of the required journeys.
3. The agreed palette and visual character.
4. Individual Stitch layout and interaction examples.

Preserve the three primary destinations: Today, My Plan, and Assistant. Within that structure, choose the navigation details, screen composition, sheets, and supporting screens that make the flows clear. Continue to honour one primary recommendation and progressive disclosure. Design flexibility does not authorize expanding the feature scope.

### Design and implementation process

Extract reusable semantic tokens and components before building screens. Preserve original Stitch exports under designs/stitch; maintain the implementation system in docs/design-system.md. The application uses this shared token system rather than independently styling each page.

Build a page/journey manifest from the product requirements, using references where helpful. Include:

- Route, navigation entry, and user objective.
- Which references or visual patterns are reused or adapted.
- Components and semantic tokens.
- Loading, empty, error, disabled, offline, and incomplete-data states.
- Data dependencies and supported API operations.
- Accessibility requirements and native interaction behaviour.

Complete missing screens and states using the same design system. The absence of a matching Stitch screen must not block an in-scope flow. Translate relevant exported elements into native React Native components; do not embed the design in a WebView.

Make routine in-scope UX improvements autonomously and record significant decisions briefly in docs/ux-decisions.md: the problem, the chosen change, and its expected benefit. Validate that benefit through testing rather than claiming it has already been proven. Ask only if a proposed change would alter agreed product scope or substantially replace the brand direction.

Baseline colours when the supplied references do not define them:
background #FAF8F5; surface #FFFFFF; primary #9C4628; pressed #80371F; accent surface #F6E8DC; text #29231F; secondary #6D6259; decorative divider #E6DED5; attention surface #FFF1D9; attention text #7A4E16. Use Manrope as the initial typography direction unless the references establish another choice.

### Mobile experience requirements

Three primary tabs:

- Today: one recommendation, compact goal progress, quick updates, data freshness.
- My Plan: goals, accepted actions, concise debt/savings summaries, history.
- Assistant: questions, explanations, what-if previews.

Secondary flows: profile, data correction, uploads, recommendation detail, goal editing, lessons, export/delete.

Recommendation cards have one short action, one calculated practical benefit, and Accept / Adjust / Not now controls. Details reveal assumptions, timing, the comparison, and an optional lesson. Acceptance creates a plan; it never claims a payment or transfer happened. Do not fabricate savings figures for persuasive copy. Notifications are opt-in, respect quiet hours, and must not turn the backend candidate list into a user to-do list.

Show at most one necessary clarification at a time. Let users skip optional questions and resume onboarding. Do not use punitive streaks, shame, alarm-colour financial scores, or false urgency. Material shortfalls still need clear, calm text. Implement system/light/dark appearance with checked contrast, extending the palette coherently where references are incomplete.

Implement safe areas, keyboard avoidance, Android back behaviour, screen-reader order, focus, readable contrast, reduced motion, text enlargement, local dates/currency formatting, and comfortable platform-sized touch targets.

Evaluate native simulator/device screenshots for consistency with the palette and shared design system, legibility, hierarchy, and complete working flows. Test small/large screens and increased text sizes. A browser screenshot alone is not native validation.

Exact visual matching to Stitch layouts is not an acceptance criterion. After implementation designs have been reviewed, use those as visual regression baselines. Record intentional layout changes with their UX rationale; preserve brand continuity without treating every reference pixel as fixed.

## 7. Data model and invariants

Represent:
users/profiles; accounts; dated balance snapshots; booked/pending transactions; transfers; received/expected income; recurring obligations and occurrences; debts and terms; goals and allocations; import batches and source rows; planned actions; confirmed execution links; recommendations; financial-state revisions; preference/policy versions; lesson progress; consent and deletion jobs; compact decision records.

Every financial record carries owner, currency, relevant dates, provenance, and status. Inferred, imported, manual, confirmed, unknown, and stale are distinct concepts.

Money:

- Use integer minor units or Decimal in the domain/database with explicit rounding.
- Use currency-tagged integers or decimal strings over JSON; enforce safe ranges.
- Keep rates, amounts, and units distinct.
- Initially support one selected currency per user. Foreign-currency data needs explicit resolution; no invented FX conversion.
- Store timezone-aware instants and distinguish booked date, due date, statement date, and effective date.

Balance:

- Define the anchor: a dated statement/balance snapshot plus later booked activity, or another explicitly documented equivalent.
- Never add historical statement activity onto its closing balance.
- Keep accounting balance, reserved money, and projected availability distinct.
- Current cash can remain unknown even when historical transactions are known.

Allocations:

- Goals are not accounts. A single account can support several goals.
- A transfer changes account balances but not total assets.
- Moving an already allocated reserve between accounts does not create new saving progress.
- Accepted actions reserve funds where appropriate; do not double-subtract them as both a reserve and an expense.

Financial mutations use transactions, idempotency keys, and optimistic concurrency. Conflicting updates return an explicit conflict and refresh path. Reversals/corrections preserve a minimal audit trail rather than silently rewriting history.

Do not promise exactly-once distributed delivery; guarantee idempotent observable effects under retries.

## 8. Onboarding, imports, and data freshness

Ask progressively for nickname, income type/range, available money, savings, debt existence, and optional goals/priorities. Country/jurisdiction is needed before country-specific policy is applied. Do not ask for unrelated identity documents.

Statement-first and manual-first paths must both work. Missing debt information is not zero debt. A skipped goal is not an error.

Import pipeline:
upload → quarantine/validate → parse → normalize → reconcile → review material ambiguities → atomic commit → state revision → recompute.

Support a documented CSV schema, user-mappable CSV fields, and at least one real, tested text-PDF format. Name the supported formats/banks in the capability matrix. Do not claim universal parsing. Scanned, encrypted, or unsupported files receive a clear manual/CSV fallback; OCR is optional unless separately implemented and verified.

Required protections:

- File type/signature, size/page/time limits; reject active or unsupported formats.
- Isolated parsing with limited resources and no unnecessary network access.
- Formula-safe CSV exports.
- User-scoped upload references, private storage, short-lived signed links.
- Raw descriptions preserved but excluded from routine telemetry.
- Exact file hashes for repeated uploads; provider IDs and overlap reconciliation for transactions.
- Date/amount/merchant matching alone must not erase genuine duplicate purchases.
- Reconcile statement opening/closing totals where available.
- Detect internal transfers and credit-card repayment to avoid income or spending double-counting.

LLM extraction is a proposal, not a commit. Require source row/page evidence for material fields and validate arithmetic. Let users resolve ambiguous material items in one concise review rather than confirming every transaction.

Raw documents are not retained indefinitely. Define retention, provider-file cleanup, retry cancellation, and deletion behaviour before live use.

The Add income flow records a received payment, its date, currency, account, and provenance. Expected income belongs to a separate forecast; it does not increase current cash. If the payment is already imported or included in a newer balance snapshot, reconcile it instead of adding it again. Support several income events per month without requiring a fixed payday. A new payment triggers the same affordability checks for regular and irregular earners; it does not automatically repeat the last allocation or apply a universal savings percentage.

Trigger recalculation on relevant record changes and time events such as a due date approaching. A scheduled sweep handles time-based invalidation even without user input. Coalesce related changes; do not spam new cards.

## 9. Domain calculators and action catalogue

Implement pure calculators for dated cash flow, affordability, debt scenarios, goal contributions, protected balances, and explicit adverse scenarios.

Specify:

- Supported debt models and unsupported terms.
- Interest timing, rounding, minimum payments, extra-payment allocation, zero-rate handling, final payment cap, and non-amortizing cases.
- Known fees and early-repayment restrictions.
- What income assumptions are included.
- Comparison horizons and any terminal balance effects.
- How baseline and proposed plans are evaluated.
- What happens when required fields are unknown.

Use exact, fixture-tested simple debt models initially. Variable rates, promotional periods, daily card-interest complexities, and unknown penalties must not receive false precision.

For an immediate cash outflow, calculate available allocation from the lowest projected uncommitted balance across the planning horizon after protected obligations and buffers, not just today's account balance. Show the horizon and income assumptions. A balance below zero at any relevant date is a shortfall even if month-end totals are positive. Recurring commitments need a separate multi-period simulation; current cash alone cannot establish future affordability.

Savings priority, goal timing, reserve needs, and discretionary capacity determine proposed contributions. A percentage of income is an optional preference constrained by affordability, not a rule derived from a user's supposed savings skill. Spending observations need provenance and adequate history; distinguish a tentative recurring charge from a confirmed obligation. Users can correct classifications. Do not infer character or financial competence from purchases.

Include this controlled catalogue:

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

Variations create concrete candidates; the catalogue is not an arbitrary finite list of canned advice. Each action defines data prerequisites, scope/jurisdiction, calculation support, contraindications, effects, lesson association, and presentation.

Do not automatically cancel services, contact lenders, or execute transactions.

### First independent acceptance fixture

Use a clearly synthetic scenario with all amounts in EUR and no uncertain obligations:

- A confirmed balance is 400 immediately before a newly received income of 600. The resulting balance is 1,000; a later statement already containing that income must not increase it again.
- Within the chosen horizon, rent is 600, necessary living costs are 150, a required debt payment is 50, and the protected unallocated balance is 100. Assume these costs do not overlap and all payment dates are known.
- With no additional income, available discretionary allocation is 100. A proposed allocation of 150 fails affordability. An allocation of 40 passes, leaving 60 of discretionary capacity.
- With a configured demo policy selecting the savings action, show: “Set aside €40 for your goal.” Its benefit must describe the computed goal progress, not invented interest savings.
- Accepting it records a planned reservation of 40; account balances remain unchanged. Confirmed completion reconciles an actual transfer or allocation and replaces the planned reservation without counting both. An internal transfer does not change total assets.
- In a separate branch before acceptance, a newly confirmed necessary cost of 80 reduces capacity to 20. The old 40 recommendation becomes ineligible. A slow job calculated from the earlier snapshot cannot republish it.

Test these expected values independently of the production calculator. This fixture establishes accounting and workflow behaviour; it does not validate a financial policy or recommend a universal savings amount.

## 10. Decision engine and psychological considerations

Specialists propose; code calculates and decides eligibility/ranking; the orchestrator explains.

Pipeline:
A. Data validity and service eligibility.
B. Candidate generation, including baseline/do-nothing.
C. Scenario calculations.
D. Hard constraints and urgency class.
E. Multi-criteria ranking of comparable eligible actions.
F. Sensitivity checks.
G. Publication with current-state validation.

Hard constraint:
After an ordinary planning action, dated available money must cover known necessary expenses, obligations, and the agreed protected balance within the documented horizon. Avoid duplicate reserve subtraction. If baseline is already infeasible, use a shortfall policy rather than discretionary allocations.

Within the ordinary planning class:
S(a) = wR*vR(a) + wF*vF(a) + wG*vG(a) + wM*vM(a) + wE*(1-cE(a)).

R: resilience; F: net financial benefit; G: goal progress; M: reduced management complexity; E: execution burden.

Implement versioned, anchored utility functions, nonnegative normalized weights, explicit horizons, and tested treatment of unavailable criteria. Never convert unknown to zero or silently renormalize differently for each candidate.

Do not normalize by whichever candidate happens to be best today. Do not count the same reserve benefit as full resilience and full goal benefit without adjusting overlap. Do not equate transfers with profit.

Weights are policy parameters, not learned psychological truths. Provide a calibration harness for swing-weighting scenarios and sensitivity analysis. Use a versioned provisional fixture configuration for demos; live policies need documented domain review. Do not pretend external research establishes our chosen percentages.

Keep urgency outside the weighted score. Define reviewed classes for immediate shortfalls, due mandatory obligations, and ordinary planning; a large long-term benefit cannot compensate for missing an imminent necessary payment. Within a class, use stable deterministic tie-breaking. Compare benefits over disclosed compatible horizons and account for remaining debt or balances at the horizon; do not compare one action's lifetime interest saving with another's one-month effect as if they were equivalent.

Preferences come from explicit choices and cautious interpretation of feedback. One refusal is not proof of risk aversion. Do not infer anxiety or reward clicks as a proxy for wellbeing.

Check plausible income delays, expense changes, and nearby weight values. When ranking is unstable, ask one useful question or preserve a still-eligible current plan. Significant price-versus-convenience trade-offs must be visible.

Revalidate accepted or displayed actions after material changes. One active primary recommendation; history can retain previous versions. Store reason codes, inputs/provenance, calculator outputs, policy/model versions, and selected/runner-up identifiers, not hidden chain-of-thought.

### Coordination and waiting system

Implement a durable state machine rather than asking an LLM to decide when everyone has finished:

1. Create a run with run_id, financial_revision, preference_version, policy_version, and an immutable snapshot read consistently from the database.
2. Build an explicit dependency graph. Cash-flow/affordability evidence is mandatory. Debt evidence is mandatory where a debt exists or is materially uncertain. Skip a specialist only with a recorded applicability reason; a failed debt task never means there is no debt.
3. Run independent tasks concurrently. Each returns a typed packet with run/revision IDs, status, candidate actions, calculator references, evidence, and missing inputs. Distinguish succeeded, failed, timed_out, and not_applicable.
4. Wait at a defined join point for every required result. Reject mismatched revisions and partial packets. A missing optional model explanation can fall back to a template; missing material cash-flow evidence cannot be bypassed with a score.
5. Enforce stage and total deadlines within the interactive budget. Long import/recompute jobs expose progress separately. Cancel superseded work where practical; otherwise discard its output. Bounded retries must not extend the total deadline indefinitely.
6. On a material failure, retain existing history but disable an action whose affordability is now unverified. Offer one clarification, retry, or a calm unavailable state. Do not keep an old card actionable merely because it was once valid.
7. Calculate eligibility/ranking in code and publish atomically only if all version checks still match. A unique publication key and idempotent writes prevent duplicate cards under retry.
8. Coalesce nearby updates and apply a documented material-change threshold before replacing a still-valid recommendation. One accepted action must not trigger an endless sequence of new tasks. Safety changes override this stability rule.

Store compact task status and dependency evidence for debugging; do not show internal agent debates or scores on Today. Test slow responses, one missing specialist, duplicate completion, newer income during processing, and a crash between calculation and publication.

## 11. Gemini model allocation and bounded agent behaviour

Use the official Google GenAI SDK through a provider adapter. Distinguish development-agent skills from the runtime model.

Configuration defaults, subject to a current capability check:

- GEMINI_LIGHT_MODEL=gemini-3.5-flash-lite
- GEMINI_REASONING_MODEL=gemini-3.1-pro-preview
- ENABLE_REASONING_ESCALATION=false in production until reviewed
- Explicit request, token, concurrency, and spend limits

Interpret Gemini 3.1 as Pro. Do not silently substitute Gemini 3.1 Flash-Lite.

### Routing

Flash-Lite:

- Routine intent/category proposals.
- Extraction assistance after deterministic parsing.
- Short explanations from approved decision packets.
- Lesson wording within reviewed content.
- Simple assistant queries that invoke known tools.

3.1 Pro:

- Bounded complex questions involving several tool results.
- Ambiguity requiring interpretation, if information actually exists.
- Complex comparative explanations or offline evaluation support.

Code:

- Identity/authorization.
- All authoritative financial calculations.
- Affordability, policy selection, weights, final ranking.
- Mutation, reconciliation, and publication checks.

A larger model cannot recover absent financial facts. Ask the user instead. No escalation based only on a model’s self-declared confidence.

A request may use at most one escalation by default. Initial engineering limits: six tool calls total per interactive turn, two retries for transient provider failures with jitter, one schema-repair attempt. Bound total wall time and token budgets. Tune these limits using observed data; do not treat them as research findings.

3.1 Pro is currently a preview. Do not make it an unconditional production dependency. Verify availability, terms, region, stability, and budgets before enabling it. If unavailable, use a validated simpler response or clarification—not an unreviewed stronger-model substitution.

Run model capability smoke tests against the actual account. Pin requested IDs/configuration and record returned version information. Any model change requires regression evaluation.

### Agent roles

Cash-flow/Spending, Debt, Savings/Goals, and Orchestrator are bounded roles in an explicit workflow, not four independently authoritative systems.

Use shared state revisions and typed tools such as:

- get_financial_snapshot
- list_obligations
- calculate_cash_flow
- simulate_debt_payment
- simulate_goal_contribution
- retrieve_reviewed_knowledge
- evaluate_candidate
- prepare_plan_change

Only confirmed application commands persist financial changes. Never trust owner IDs or permission claims supplied by the model. Tool handlers derive scope from the authenticated server context.

Provide structured outputs with semantic validation. Reject mismatched currency, dates, amounts, scenario IDs, unsupported claims, or missing evidence.

Generate financial figures in cards directly from validated results. Where practical, let the model reference fact IDs rather than retype numbers. Free-form assistant replies with monetary claims need the same binding to tool results. On failure, use a checked template or ask a clarification.

Do not expose SQL, shell execution, arbitrary HTTP requests, trading, or unrestricted retrieval to runtime agents.

## 12. Knowledge, lessons, and assistant boundaries

Maintain reviewed material separately from executable financial policy:
source, publication/review date, country, applicability, exceptions, content version, and reviewer status.

Start with a small curated collection and deterministic tags/full-text retrieval. Add embeddings only when retrieval evaluation demonstrates a need. Keep user-specific data separate and scoped; never place all users’ statements in a shared retrieval index.

Do not run live open-web financial research as part of routine recommendations. New content enters through a review/versioning process.

Create 8–10 concise lesson templates around available money, obligations, reserves, income variability, debt interest, minimum/additional payments, and goal timelines. Each contains one concept, one interaction, and one question with explanations. All are optional and accessible.

Assistant:

- Answers from the snapshot/tools and reviewed sources.
- Presents uncertainty and alternatives without false precision.
- Keeps hypotheticals separate from saved changes.
- Explains current-scope limits for investment/personalized tax/legal questions.
- Does not diagnose or promise emotional outcomes.
- Stops or changes approach when the user declines.

No fine-tuning initially. Accumulate reviewed failure categories and evaluate targeted changes before training. Do not automatically train on user data.

## 13. API, states, and failure handling

Use OpenAPI as the contract; generate TypeScript types/client and fail CI on unexplained drift. Domain logic remains server-side.

Use cursor pagination, bounded inputs, consistent errors, rate limits, request IDs, and cancellation.

Suggested endpoint groups: profile/consent, accounts, transactions, obligations, debts, goals, imports, financial snapshots, recommendations, plan/actions, simulations, assistant, lessons, export/deletion. Validate scope on every object.

Import state example:
uploaded → validating → parsing → needs_review → ready_to_commit → committed.
Additional terminal or recovery states: failed, cancelled, expired.
Transitions and retry semantics must be explicit.

Recommendation state:
proposed → accepted/planned → completed.
Alternatives: declined, postponed, superseded, invalidated.
Do not confuse an active action with a recommendation card. Completion links to an operation exactly once.

Publication checks financial_revision, preference_version, and policy_version. A stale job may finish computation but cannot overwrite a newer result.

Mobile:

- Keep cached reads clearly dated.
- Default offline mode to a truthful cached/read-only state.
- Do not silently queue financial writes or show completion before server acknowledgement.
- If offline drafts are added, label pending state and revalidate after reconnect.
- Expired sessions recover safely without losing an unsent form.
- A provider outage does not erase plans or balances.

Store enough audit information to reproduce engine decisions without collecting unnecessary raw model conversations.

## 14. Privacy and security

Build a threat model around the mobile client, API, database, object storage, workers, AI provider, imported documents, and developer tools.

Use OWASP MASVS/MASTG for mobile and a scoped ASVS Level 2 baseline for API/backend, with applicability and test evidence. These are review frameworks, not certification badges.

Required:

- Private user data and files; ownership checks on every access.
- Rotatable credentials and maintained verification libraries.
- Secure token storage; no secrets in Expo public configuration.
- Separate development, staging, and production services/keys.
- Parameterized queries, bounded uploads, rate/abuse controls.
- Restricted parsing and outbound network access.
- Redacted logs and exception reports; no raw statements, account identifiers, or full financial prompts by default.
- No sensitive push-notification text.
- No session replay or screenshots of financial screens in analytics by default.
- Separate consent states and versioned notices.
- Authenticated export and deletion, including private files, caches, jobs, and external artifacts where supported.
- Deletion cancellation checks before worker commits; no resurrection of deleted data.
- Document backup-retention and provider-retention limits honestly.

For Gemini:

- Check current terms for the selected endpoint, age, geography, billing, and data use.
- Configure a reviewed paid/business data-processing route for real financial data. Do not infer that a free prototype key is suitable.
- EEA/UK/Swiss availability and paid-service conditions require explicit verification.
- Paid processing does not imply zero retention or EU-only processing.
- Minimize/redact data before sending; prefer extracted necessary facts over whole statements.
- Keep live sensitive data disabled until those requirements are verified.
- No external file URL may cause arbitrary fetching or SSRF.

Prompt injection defence must exist in tool permissions, data isolation, schemas, and application validation. A system instruction or a second LLM “judge” is not an adequate boundary.

Scope this as a money-management and educational product; obtain a launch-market review of debt/advice/privacy boundaries before public real-data release. “Educational only” text is not a substitute for that review.

## 15. Test strategy and evaluation

### Deterministic domain

Use pytest and Hypothesis. Add independent reference cases rather than tests that simply call the implementation twice.

Cover:

- Transfer conservation.
- Snapshot reconciliation.
- Idempotent repeated import and completion.
- Legitimate identical purchases.
- Credit repayment versus purchase double counting.
- Allocation limits.
- Zero/negative/boundary values.
- Zero-rate and non-amortizing debts.
- Payments larger than remaining principal.
- Leap years, month-end dates, timezone boundaries, and delayed income.
- Unknown/unsupported terms.
- Stale job publication and concurrent accepted actions.
- Deletion during an import.
- Policy rules taking precedence over every score.

### Integration/security

Use a real test PostgreSQL instance.
Verify transactions, migrations, restart/retry recovery, private file access, session expiry/revocation behaviour, cross-user denial, and parameter tampering.
Exercise exact request retries and conflicting payload reuse under an idempotency key.

### Mobile

Use jest-expo/React Native Testing Library for meaningful component behaviours. Use Maestro for native journeys. Use browser testing only for optional web surfaces; it does not replace native E2E.

Test onboarding, supported import, corrections, add income, accept/adjust/complete, scenario preview without mutation, lessons, data freshness, outage/reconnect, export/delete, and back navigation.

### AI evaluations

Create an initial target of at least 60 distinct scenario families before release assessment, with missing-data, inconsistent-data, urgent-shortfall, irregular-income, injection, and calm-tone cases. This count is an engineering coverage target, not a reliability guarantee.

Use separate development/calibration and held-out suites grouped by scenario family/user. Repeat critical scenarios at least three times for release candidates.

Measure:

- Correct tool/argument use.
- Supported numeric claims and citations.
- Appropriate abstention/clarification.
- No unauthorized writes or cross-user access.
- Agreement with an expert-approved set of acceptable actions, not a single rigid answer where trade-offs exist.
- Tone and unnecessary question count.
- Completion latency, token use, and cost.

Code grades invariants. Humans calibrate subjective evaluations. A Pro model may assist offline scoring but is not the sole judge. Do not optimize acceptance/click rates as the sole objective.

## 16. Delivery phases

Phase 0 — Inventory and contract:
design manifest, skill manifest, ADRs, domain invariants, threat model, supported capabilities, environment setup.

Phase 1 — Working foundation:
native navigation/design tokens, authentication, private user data, manual snapshot, deterministic recommendation, plan/complete loop.

Phase 2 — Domain and persistence:
calculator fixtures, allocation rules, state revisions, idempotent operations, My Plan, meaningful history.

Phase 3 — Import:
real CSV and supported text-PDF processing, durable jobs, reconciliation, review, atomic commit, failure recovery.

Phase 4 — Decision engine:
catalogue, constraints, provisional policies, explanations, sensitivity and no-change behaviour.

Phase 5 — AI and learning:
Flash-Lite tools/assistant, optional Pro escalation, reviewed retrieval, grounded outputs, lessons, eval suite.

Phase 6 — Hardening:
native usability and visual consistency, accessibility, isolation tests, deletion/export, telemetry, load tests, build/update compatibility, recovery drills.

Phase 7 — Release preparation:
staging proof, domain/policy and privacy reviews, current provider checks, store requirements, deployment plan, accountable sign-off.

Each phase produces a demonstrable end-to-end increment. Keep moving on independent work when a gate is blocked. Do not publish automatically after phase 7.

## 17. Operations, scale, and costs

Scale from evidence:

- Stateless API instances with a bounded connection pool.
- Horizontally scalable workers with controlled provider concurrency.
- Idempotent durable jobs and per-user deduplication/coalescing.
- Indexes from real access patterns; pagination before large data loads.
- No migration to microservices without measured need.

Use structured telemetry, request/job IDs, and an OpenTelemetry-compatible instrumentation approach. Keep raw financial content out of traces. Track:

- API errors and latency.
- Import age, failures, retries, and reconciliation exceptions.
- Invalid/stale recommendation rejection.
- Model timeout/schema/grounding failures and escalation count.
- Tokens and cost by feature/model.
- Crash-free sessions and app/build versions.
- Export/deletion queue health.

Define alerts with owners and actionable runbooks. Set per-user and global AI budgets. Return a useful fallback when limits are reached.

Initial proposed engineering targets, adjustable only with recorded evidence:

- Non-AI read API p95 under 500 ms at 50 concurrent synthetic sessions.
- AI validated response or explicit fallback within a 20-second request deadline; no silent spinner.
- Import upload acknowledgement within 2 seconds of server receipt; progress exposed for background work.
- Test import workload of 5 simultaneous supported files up to 20 pages or 1,000 rows; publish measured completion time.
- Production API availability objective 99.5% monthly.
- RPO at most 24 hours and RTO at most 4 hours for the initial release, dependent on a tested backup/service plan.

These are proposed acceptance targets, not observed results or vendor guarantees. Measure on specified devices, network, dataset, and staging resources.

Back up and restore database and documents; a database backup does not necessarily cover object-storage bytes. Record one successful restore drill.

Use feature flags for imports, AI, Pro escalation, and new policy versions. A kill switch must disable affected recommendations without blocking access to existing data.

## 18. Release gates and evidence

Create docs/release-readiness.md with PASS / FAIL / BLOCKED / NOT APPLICABLE, evidence, reviewer/owner, and date.

Required gates:

1. All critical domain and authorization tests pass; zero known critical invariant violations.
2. Core native journeys pass on both target platforms. Document simulator and actual device coverage.
3. Implementation preserves the agreed palette and visual character; complete journeys and important states are reviewed on native devices, accessibility checks are complete, and material UX changes are explained. Exact matching to Stitch layouts is not a release gate.
4. No unresolved exploitable critical/high security findings; lower risks documented and owned.
5. Supported imports reconcile; repeats, ambiguity, interruption, and deletion recovery tested.
6. AI held-out evaluation passes agreed rubrics. All critical numeric/permission cases pass in the tested trials. Report sample sizes and failures; zero observed failures is not proof of zero real-world risk.
7. Financial action catalogue, thresholds, scales, and weights have documented domain review for live use.
8. Provider terms, 18+ scope, launch market, processing/retention, and applicable privacy/advice review complete.
9. Export/deletion and retention behaviour verified.
10. Performance/cost results meet the agreed targets or remain visibly blocked pending an explicit change.
11. Backup restore, application rollback, and worker recovery tested.
12. Store disclosures, permission explanations, deletion requirements, and release signing prepared and checked against current official rules.
13. Preview-model use approved or disabled with a tested fallback.
14. No mock fixtures silently used in live mode.

Separate readiness for local demo, staging, limited real-data pilot, and public release. Do not label all four as “production-ready”.

A coding agent cannot replace a human financial reviewer, legal/privacy reviewer, security review where needed, or product-owner release authorization. Record pending reviews honestly and finish all independent engineering work.

## 19. CI/CD and deliverables

CI:

- Formatting/linting, TypeScript/Python type checks.
- Contract drift checks.
- Domain/property and integration tests.
- Dependency/secret scanning and SBOM.
- Migration checks against disposable databases.
- Critical mobile flow tests on release candidates.
- Deterministic agent regression fixtures per change; budgeted live-model evaluations on scheduled/release runs.
- Separate staging and production secrets.
- Pinned actions/dependencies where supported, lockfiles, controlled upgrade PRs.

Prepare EAS builds and optional OTA configuration. Match runtime versions; native dependency changes require compatible native builds. Demonstrate rollback on staging. Keep backend APIs compatible with still-supported mobile versions. Use additive/expand-contract database migrations; do not assume destructive migration rollback is safe.

Deliver:

- Mobile app, API, worker, migrations, and supported-format fixtures.
- Reproducible local setup and physical-device network instructions.
- Validated environment examples with no secrets.
- Generated API contracts.
- Rule/action/prompt/model configuration versions.
- Design and skill manifests.
- Test/evaluation results and screenshots with synthetic data.
- Capability matrix and known limitations.
- Threat model, data map, retention/deletion policy, runbooks.
- Release-readiness evidence and remaining owner actions.

End each implementation checkpoint with the exact commands run, meaningful outcomes, and honest limitations. Never manufacture test results or deployment URLs.

Begin now with repository/design inspection and the first complete vertical slice.

# Part B — Evidence and selection notes

## What the research changes

The package uses a small set of vendor-maintained skills, an explicit financial engine, native-device evidence, and staged release gates. Skills guide the coding agent; they do not prove code correctness.

The following are deliberate product/engineering choices, not universal findings: FastAPI modular monolith, Supabase as a greenfield default, catalogue size, request limits, scenario count, performance targets, and model routing. Validate them against the real deployment and audience.

## Model allocation

Google documents Gemini 3.5 Flash-Lite as stable, with function calling and structured output. It is the default for focused tasks. Gemini 3.1 Pro is documented as a preview and is selected only as an optional reasoning route. Neither decides financial eligibility or performs authoritative arithmetic.

The name “Gemini 3.1” is an explicit interpretation, not an exact model ID supplied by the user. If a different 3.1 variant was intended, update routing after evaluation rather than silently substituting.

No inference request or account-level availability test was run while preparing this document. Implementation must verify actual access.

## Skills versus tools

Expo, Stitch, Gemini, and Supabase repositories contain relevant skills. Installation is not performed by this document. Inspect and load only what the active task needs.

Stitch provides a native-specific skill. Use its applicable conversion guidance within section 6. Supplied designs establish the visual foundation; product requirements determine behaviour and the development agent may improve layouts and flows. Any skill instruction requiring exact reproduction must yield to that project direction.

## Source register

Checked 24 October 2026. Recheck evolving documentation before implementation.

1. [Expo skills documentation](https://docs.expo.dev/skills/) and [Expo skill source](https://github.com/expo/skills): current skill inventory and supported integrations.
2. [Stitch skills source](https://github.com/google-labs-code/stitch-skills): plugin catalogue and setup.
3. [Stitch React Native skill](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-build/skills/react-native/SKILL.md): native conversion workflow.
4. [Stitch design-md skill](https://github.com/google-labs-code/stitch-skills/blob/main/plugins/stitch-utilities/skills/design-md/SKILL.md): design-system extraction when needed.
5. [Gemini API skills](https://github.com/google-gemini/gemini-skills): API development instructions. The repository states that it is not an officially supported Google product; do not treat it as a support guarantee.
6. [Supabase agent skills](https://github.com/supabase/agent-skills): Supabase and PostgreSQL guidance.
7. [Agent Skills format](https://agentskills.io/home): portable procedural instructions, distinct from runtime services.
8. [Expo development-build FAQ](https://docs.expo.dev/develop/development-builds/faq/): Expo Go's native-library limitations.
9. [Expo Router](https://docs.expo.dev/router/introduction/): native routing.
10. [Expo with Supabase](https://docs.expo.dev/guides/using-supabase/): integration reference; evaluate token storage for financial-data use rather than copying a tutorial uncritically.
11. [Supabase JWT guidance](https://supabase.com/docs/guides/auth/jwts) and [RLS guidance](https://supabase.com/docs/guides/database/postgres/row-level-security): authentication and database access boundaries.
12. [Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite): documented stable identifier and capabilities.
13. [Gemini 3.1 Pro Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview): documented preview identifier and capabilities.
14. [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output) and [function calling](https://ai.google.dev/gemini-api/docs/function-calling): interface mechanisms, not semantic guarantees.
15. [Gemini API terms](https://ai.google.dev/gemini-api/terms): age, region, paid-service, and processing conditions. Paid processing does not mean no retention or residency guarantee.
16. [OWASP MASVS](https://mas.owasp.org/MASVS/) and [MASTG](https://mas.owasp.org/MASTG/): mobile security verification.
17. [OWASP ASVS](https://asvs.owasp.org/): backend/web-service security requirements.
18. [OWASP prompt injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/): untrusted content and model/tool boundaries.
19. [Maestro React Native documentation](https://docs.maestro.dev/get-started/supported-platform/react-native): native UI automation.
20. [Hypothesis](https://hypothesis.readthedocs.io/en/latest/): property-based tests.
21. [FastAPI background-task guidance](https://fastapi.tiangolo.com/tutorial/background-tasks/): scope of in-process work; this brief separately requires durable processing.
22. [Anthropic agent evaluation guidance](https://www.anthropic.com/research/demystifying-evals-for-ai-agents): evaluating complete workflows with code, model, and human checks.
23. [Expo runtime versions](https://docs.expo.dev/eas-update/runtime-versions/): compatibility between OTA updates and native builds.
24. [HM Treasury MCDA guidance](https://www.gov.uk/government/publications/green-book-supplementary-guidance-multi-criteria-decision-analysis/use-of-multi-criteria-decision-analysis-in-options-appraisal-of-economic-cases): swing weighting and sensitivity analysis, adapted here rather than treated as financial-app validation.
25. [CFPB financial wellbeing](https://www.consumerfinance.gov/consumer-tools/educator-tool/financial-well-being-resources/): control, resilience, goals, and freedom of choice; not a source of FinAgent's numeric weights.

## Important remaining decisions

The implementation agent should resolve technical details with documented defaults and continue. Public release still depends on:

- Actual coding environment and provided repository.
- Reviewed implementation page/journey coverage and a coherent design system derived from the supplied visual references. Final Stitch designs for every state are not required.
- Launch country and supported financial/debt products.
- Service accounts, billing authorization, region, and processing terms.
- Reviewed financial policies and weight calibration.
- Named owners for security/privacy/domain review and release.
- Native device access and deployment credentials.

These are explicit release dependencies, not reasons to postpone building a working local and staging product.
