# ADR-002 — Financial assumptions and deterministic policy

All stored money uses integer minor units with an explicit profile currency. Percentage rates are decimal strings; multiplication and interest round half-up through `Money`. Aggregate totals use integer addition/subtraction; no binary floating-point financial calculations are used. Frontend currency formatting is presentation only.

Transactions use ISO dates; system timestamps are UTC. The seeded demo uses a persistent synthetic clock, initially 2026-10-22. Income and bill days are restricted to 1–28 to avoid ambiguous month-end rules. Synthetic sources cover May–October 2026 with seed 42.

Cash projection reserves fixed costs on dates strictly after the current date and before the next income; it also reserves minimum debt payments on day 28. Current-day transactions are treated as settled. During replay, rule execution additionally reserves known later outflows on the same date. The displayed safe-to-spend amount spreads cash above these reserves and the minimum buffer over days to the next income. Variable future spending is not forecast. Rules always recheck the current floor.

Debt forecasts assume a fixed APR, monthly accrual, no fees or new borrowing. A 1,200-month cap and a non-amortizing check prevent false payoff claims. Avalanche rolls freed minimums toward the highest APR; snowball uses the smallest balance. Replayed minimum payments apply rounded monthly interest and reduce principal. Model results are educational estimates, not quotes from a lender.

Savings defaults to three months of known fixed costs. Contributions are 5–10% of income capped by the available buffer and remaining target. A linked named savings goal can override the emergency target. Timeline estimates assume fixed contributions, no savings interest, and ceiling months.

Policy weights in `config/coordinator.yaml`: goal 5, impact 3, urgency 2, ease 1, stability 1, risk 2. Goal alignment is 0/1; impact is max(abs(monthly cash effect), annual interest saving / 12), normalized by the largest eligible impact. Urgency identifies no emergency fund, high APR, or multiple subscriptions. Stability is 1 for these deterministic proposals. Ease is 1/effort. A broad category reallocation has effort 3 and risk 2 because the apparent change may not be repeatable; this favors a small observed habit over treating an entire category delta as guaranteed savings. Review savings are potential, not committed income.

Ties resolve by impact, effort, and stable candidate id. LLM-assisted selection receives the same hard-filtered options; invalid ids or unfaithful wording fall back. Top-3 evaluation uses the rule ranking in both modes because the model selects one id rather than producing a new ranking.

A declined recommendation type is suppressed for seven days by default. Exactly one recommendation can be issued per synthetic date. Recomputing invalidates an old pending recommendation but does not bypass that limit. Guard events suppress new recommendations and lessons for at least 48 hours, and extend if the strain remains. Existing approved rules retain their independent cash-floor check; they are not new coaching nudges.

Known approximations: monthly-only recurring detection, no statistical income forecast, bounded English assistant routing, and constant-contribution goal dates. The projected calendar date is compared with the requested deadline; profile changes record before/after dates. These approximations are disclosed rather than presented as guarantees.
