# FinAgent — Consolidated Solution Description

## 1. Product purpose

FinAgent helps users decide what to do next with their money based on their financial situation and personal priorities.

The experience follows one principle: **minimal input, meaningful background analysis, and one clear next step.**

Each recommendation states an action and its practical benefit. Calculations, alternatives, and short lessons are available when the user wants more detail.

FinAgent does not move money. Users remain in control of their decisions.

## 2. Financial data collection

The application gradually collects:

- Name or nickname.
- Income type: regular, irregular, or mixed.
- Approximate income amount or range.
- Available money and existing savings.
- Whether the user has debts.
- Savings goals and their priorities.

These are information requirements, not a mandatory questionnaire. Users can skip questions and provide details later.

If no goal is provided, FinAgent may suggest one. The user can accept, modify, or decline it.

### Bank statements and manual entry

Bank statement upload is the primary way to reduce manual work. The application extracts available transactions, income, recurring payments, account balances, and potential debt or savings transfers.

Manual entry remains an alternative.

The system distinguishes between:

- Information extracted from documents.
- Inferred patterns.
- User-confirmed information.
- Missing or outdated information.

It asks targeted questions only when an answer could materially change the next recommendation. For example, a statement may show a loan payment without revealing the outstanding balance or interest rate.

Users can review and correct their data. Repeated uploads are reconciled to prevent duplicate transactions, and transfers between the user’s accounts are not counted as new income.

## 3. Background analysis and specialist agents

Three specialist agents analyze the same version of the user’s financial information. They use software tools for calculations and return structured findings and candidate actions.

### Cash-flow and Spending Agent

Analyzes:

- Income regularity and variability.
- Recurring payments and likely subscriptions.
- Spending categories and changes over time.
- Repeated low-cash periods.
- Potential duplicate transactions and fees.
- Expected balances around upcoming expenses and payments.

It identifies observable patterns without claiming to know every habit or the user’s motivations.

### Debt Agent

Uses a debt calculator to evaluate:

- Balances, interest rates, minimum payments, and due dates.
- Overdue payments and known consequences.
- Repayment timelines and interest costs.
- Additional one-off or recurring payment scenarios.

Calculations use supported debt models and explicit assumptions. Missing critical information triggers clarification rather than invented precision.

### Savings and Goals Agent

Evaluates:

- Existing savings and their purposes.
- Goal amounts, dates, and priorities.
- Required and affordable contributions.
- Alternative amounts or timelines.
- The distinction between emergency reserves and known future expenses.

A preferred savings percentage can guide proposals, but affordability takes precedence. Financial literacy influences explanations and lessons, not assumed saving capacity.

### Internal tools

Statement extraction, transaction reconciliation, financial calculations, and constraint checks are software components—not independent reasoning agents.

The specialists may use the same underlying language model with different instructions, tools, and responsibilities.

## 4. Updates and ongoing planning

Users update information through statement uploads, manual corrections, or quick actions such as “Add income.”

A material change triggers recalculation. The system accounts for expenses already paid and money already allocated.

Regular and irregular earners use the same framework, but future income is treated according to its uncertainty. Expected money is distinguished from received money.

Background recalculation does not automatically create a new user-facing task. FinAgent preserves the current recommendation when it remains appropriate.

Statement uploads do not provide a continuous bank connection. Recommendations account for data freshness.

## 5. Recommendation selection: orchestrator and decision engine

The Orchestrator coordinates the specialists. A programmatic decision engine validates and ranks their proposals.

### Step 1: Generate candidate actions

Each candidate specifies:

- Action, amount where applicable, and timing.
- One-off or recurring commitment.
- Required information.
- Calculated consequences.
- Assumptions and limitations.

Maintaining the current plan is also a valid option.

### Step 2: Calculate consequences

Software tools compare the current plan with each proposed scenario.

Comparisons use consistent horizons and assumptions. Results may include interest savings, repayment dates, available cash, and goal progress.

A one-off payment and a recurring monthly commitment are evaluated separately.

### Step 3: Apply hard constraints

An ordinary planning action is ineligible if it:

- Creates a projected shortage for known necessary expenses, obligations, and the agreed protected balance.
- Allocates the same money twice.
- Violates explicit user restrictions.
- Depends on missing critical information.

Payment and income dates matter, not just monthly totals. A high score cannot override these constraints.

If the user already faces a shortfall, the system switches to assistance with that situation rather than recommending discretionary allocations.

### Step 4: Evaluate eligible actions

The engine evaluates five criteria:

| Criterion | Meaning |
| --- | --- |
| Financial resilience | Ability to withstand income delays or unexpected expenses |
| Financial benefit | Calculated savings in interest and fees, net of associated costs |
| Goal progress | Advancement toward the user’s stated objectives |
| Management simplicity | Reduction in separate obligations and recurring administrative tasks |
| Execution effort | Time, steps, and ongoing effort required |

The proposed scoring structure is:

[

S(a)=w_Rv_R(a)+w_Fv_F(a)+w_Gv_G(a)+w_Mv_M(a)+w_E[1-c_E(a)]

]

Scores use predefined scales from 0 to 1. Weights are nonnegative and sum to 1.

Overlapping benefits must not be counted twice. Strongly overlapping criteria require adjustment or consolidation.

### Step 5: Calibrate weights and preferences

Weights are established through **swing weighting**: experts and representative users compare the importance of concrete improvements across defined criterion ranges.

Research informs the criteria; it does not supply universal percentages.

Explicit user preferences can personalize the trade-offs. A refusal alone does not establish a preference, and the system does not infer psychological diagnoses from transactions.

### Step 6: Check robustness

The engine tests whether reasonable changes in financial assumptions or weights change the preferred action.

If the choice is unstable, it may:

- Ask one useful clarification.
- Offer a more cautious option.
- Preserve an existing eligible plan.

“Best” means most suitable among the evaluated options under known information—not guaranteed globally optimal.

## 6. Psychological considerations

FinAgent considers both financial outcomes and the practical burden of managing money.

It supports:

- Financial flexibility and an appropriate protected balance.
- Manageable actions.
- Clear explanations.
- Meaningful personal goals.
- User choice without pressure.
- Stability rather than constantly changing recommendations.

The application does not claim to calculate happiness or anxiety. When personal comfort affects a financial trade-off, it asks rather than assumes.

Material financial costs of choosing convenience or simplicity remain visible.

## 7. Recommendation and action experience

The main card presents:

> **Action → practical benefit → optional explanation**
> 

Details show the calculation, assumptions, alternative, and an adjustable scenario.

Users can:

- Add the action to their plan.
- Adjust it.
- Postpone or decline it.
- Confirm completion.

Acceptance represents intention, not execution. Financial records change only when the action is recorded or reconciled with a transaction.

## 8. Learning and assistant

Recommendations can link to optional micro-lessons:

1. Understand one principle.
2. Try a small interactive scenario.
3. Answer one comprehension question with feedback.

Lessons use reviewed content. Personal figures are inserted only when supported by valid calculations. Learning never blocks a financial action.

The Assistant answers questions about the current plan, explains recommendations, and runs what-if scenarios. Hypothetical conversations do not change financial records without confirmation.

## 9. Mobile structure

Three primary screens:

- **Today:** one recommendation, relevant goal progress, quick updates, and data freshness.
- **My Plan:** goals, accepted actions, concise debt and savings information, and history.
- **Assistant:** questions, explanations, and scenario exploration.

Calculations, lessons, and editing open within these flows. Most analysis remains in the background.

## 10. Reliability and improvement

The system combines:

- A capable base language model.
- Reviewed financial knowledge and versioned policies.
- Financial calculators.
- A constrained action catalogue.
- Programmatic validation and ranking.
- Expert-reviewed evaluation scenarios.

The model handles interpretation, tool use, candidate generation, and explanation. Code controls calculations, eligibility, scoring, and record updates.

Fine-tuning is optional and addresses demonstrated recurring model errors. It does not replace calculators, rules, or current knowledge.

Before deployment, evaluation must cover data extraction, numerical correctness, eligibility, recommendation quality, robustness, clarity, and user burden.

**The architecture is defined. Scoring scales, weights, supported financial products, and release thresholds remain implementation decisions to validate before treating the system as production-ready.**

## Product scope and future development

### Current product: everyday financial guidance

FinAgent initially serves students and people beginning to manage their finances independently.

Its recommendations focus on:

- Managing regular and irregular income.
- Keeping enough money for necessary expenses and upcoming payments.
- Understanding spending patterns and reviewing recurring costs.
- Managing debt and comparing affordable repayment options.
- Building and maintaining a financial reserve.
- Setting savings goals and adjusting contributions or deadlines.
- Learning financial concepts through short, optional lessons connected to decisions.

The recommendation engine selects from a controlled catalogue of supported actions. It may also suggest maintaining the current plan, updating information, or seeking appropriate help.

**Investment selection, portfolio recommendations, and personalized buy, sell, or hold advice are outside the current scope.** If asked, the assistant explains this boundary and may provide a basic educational explanation from reviewed materials.

### Future phase: support for more advanced financial needs

As users’ needs develop, FinAgent may expand to include:

- Investment education and long-term planning scenarios.
- Descriptive analysis of holdings and investment costs.
- Additional tools for users with established savings and investment plans.
- Personalized investment recommendations through an appropriately authorized service or partner, subject to applicable requirements.

These capabilities are future extensions. The current product does not require an Investment Agent, portfolio data collection, or investment-ranking functionality.