"""Deterministic debt amortization and repayment strategy calculator (§9, §15).

All monetary values are integer EUR cents (`int`, never `float`).
All interest rates are annual percentage rates in basis points (`apr_bps`, 1% = 100 bps).

Rounding & Interest Timing Rule (`round-half-up-monthly-bps-v1`):
1. Each month, interest is accrued on the opening principal balance before payment:
       interest_cents = (balance_cents * apr_bps + 60_000) // 120_000
   This is exact integer arithmetic for `round_half_up(balance_cents * (apr_bps / 10_000) / 12)`.
2. Zero-rate (`apr_bps == 0`) produces `0` interest every month.
3. Unknown terms (`not debt.terms_known`) return `status="needs_input"` with `months=None`,
   `total_interest_cents=None`, `total_paid_cents=None` — never false precision.
4. Non-amortizing check: if `balance_cents > 0` and the scheduled payment for a debt is less than
   or equal to its first month's interest (`payment <= first_month_interest`), the debt cannot
   amortize (`status="non_amortizing"`, `months=None`, `total_interest_cents=None`, `total_paid_cents=None`).
5. Final payment cap: in any month, actual payment is `min(scheduled_payment, balance_cents + interest_cents)`,
   so principal never goes negative and no overpayment occurs.
6. One-off extra payment simulation: an immediate extra payment is capped at `min(extra_cents, total_balance)`
   before monthly amortization begins.
"""

from typing import Literal
from pydantic import Field
from .domain import Debt, Money, Record

MAX_AMORTIZATION_MONTHS = 600
ROUNDING_RULE = "round-half-up-monthly-bps-v1"

AmortizationStatus = Literal["paid", "non_amortizing", "needs_input", "unsupported"]
StrategyName = Literal["minimum_only", "avalanche", "snowball"]


class DebtPayoffSummary(Record):
    debt_id: str
    label: str
    status: AmortizationStatus
    months: int | None = None
    total_interest_cents: int | None = None
    total_paid_cents: int | None = None
    principal_paid_cents: int | None = None


class StrategyResult(Record):
    strategy: StrategyName
    status: AmortizationStatus
    months: int | None = None
    total_interest_cents: int | None = None
    total_paid_cents: int | None = None
    interest_saved_vs_baseline_cents: int | None = None
    months_saved_vs_baseline: int | None = None
    debts: list[DebtPayoffSummary] = Field(default_factory=list)


class OneOffExtraPreview(Record):
    requested_extra_cents: Money
    applied_extra_cents: Money
    target_debt_id: str | None = None
    status: AmortizationStatus
    months: int | None = None
    total_interest_cents: int | None = None
    total_paid_cents: int | None = None
    interest_saved_cents: int | None = None
    months_saved: int | None = None


class DebtSimulationView(Record):
    revision: int
    status: AmortizationStatus
    rounding_rule: str = ROUNDING_RULE
    recurring_extra_cents: Money = 0
    one_off_extra_cents: Money = 0
    baseline: StrategyResult
    avalanche: StrategyResult
    snowball: StrategyResult
    one_off_preview: OneOffExtraPreview | None = None


def monthly_interest_cents(balance_cents: int, apr_bps: int) -> int:
    """Computes monthly interest in integer EUR cents using round-half-up:
    (balance_cents * apr_bps + 60_000) // 120_000.
    """
    if balance_cents <= 0 or apr_bps <= 0:
        return 0
    return (balance_cents * apr_bps + 60_000) // 120_000


def amortize_single_debt(
    debt: Debt,
    recurring_extra_cents: int = 0,
    one_off_extra_cents: int = 0,
) -> DebtPayoffSummary:
    """Pure single-debt monthly amortization calculator."""
    if not debt.terms_known:
        return DebtPayoffSummary(
            debt_id=debt.id,
            label=debt.label,
            status="needs_input",
        )
    if recurring_extra_cents < 0 or one_off_extra_cents < 0:
        raise ValueError("Extra payments cannot be negative.")

    if debt.balance_cents == 0:
        return DebtPayoffSummary(
            debt_id=debt.id,
            label=debt.label,
            status="paid",
            months=0,
            total_interest_cents=0,
            total_paid_cents=0,
            principal_paid_cents=0,
        )

    applied_one_off = min(debt.balance_cents, one_off_extra_cents)
    balance = debt.balance_cents - applied_one_off
    total_interest = 0
    total_paid = applied_one_off
    months = 0

    if balance == 0:
        return DebtPayoffSummary(
            debt_id=debt.id,
            label=debt.label,
            status="paid",
            months=0,
            total_interest_cents=0,
            total_paid_cents=total_paid,
            principal_paid_cents=debt.balance_cents,
        )

    monthly_budget = debt.min_payment_cents + recurring_extra_cents
    first_interest = monthly_interest_cents(balance, debt.apr_bps)
    if monthly_budget <= first_interest:
        return DebtPayoffSummary(
            debt_id=debt.id,
            label=debt.label,
            status="non_amortizing",
        )

    while balance > 0:
        if months >= MAX_AMORTIZATION_MONTHS:
            return DebtPayoffSummary(
                debt_id=debt.id,
                label=debt.label,
                status="non_amortizing",
            )
        months += 1
        interest = monthly_interest_cents(balance, debt.apr_bps)
        if monthly_budget <= interest:
            return DebtPayoffSummary(
                debt_id=debt.id,
                label=debt.label,
                status="non_amortizing",
            )
        due_total = balance + interest
        payment = min(monthly_budget, due_total)
        principal_reduction = payment - interest
        balance -= principal_reduction
        total_interest += interest
        total_paid += payment

    return DebtPayoffSummary(
        debt_id=debt.id,
        label=debt.label,
        status="paid",
        months=months,
        total_interest_cents=total_interest,
        total_paid_cents=total_paid,
        principal_paid_cents=debt.balance_cents,
    )


def _priority_key(strategy: StrategyName, debt: Debt, current_balance: int) -> tuple:
    if strategy == "avalanche":
        # Highest APR first; tie-break by smallest current balance, then id
        return (-debt.apr_bps, current_balance, debt.id)
    # Snowball: smallest current balance first; tie-break by highest APR, then id
    return (current_balance, -debt.apr_bps, debt.id)


def simulate_strategy(
    debts: list[Debt],
    strategy: StrategyName,
    recurring_extra_cents: int = 0,
    one_off_extra_cents: int = 0,
    target_debt_id: str | None = None,
    baseline: StrategyResult | None = None,
) -> StrategyResult:
    """Simulates multi-debt payoff under `minimum_only`, `avalanche`, or `snowball`."""
    if recurring_extra_cents < 0 or one_off_extra_cents < 0:
        raise ValueError("Extra payments cannot be negative.")

    if not debts:
        return StrategyResult(
            strategy=strategy,
            status="paid",
            months=0,
            total_interest_cents=0,
            total_paid_cents=0,
            interest_saved_vs_baseline_cents=0 if baseline else None,
            months_saved_vs_baseline=0 if baseline else None,
            debts=[],
        )

    if any(not d.terms_known for d in debts):
        summaries = [
            DebtPayoffSummary(
                debt_id=d.id,
                label=d.label,
                status="needs_input" if not d.terms_known else "unsupported",
            )
            for d in debts
        ]
        return StrategyResult(
            strategy=strategy,
            status="needs_input",
            debts=summaries,
        )

    if strategy == "minimum_only" and recurring_extra_cents == 0 and one_off_extra_cents == 0:
        # Pure minimum-only baseline: each debt amortizes independently on its own minimum payment
        summaries = [amortize_single_debt(d) for d in debts]
        if any(s.status != "paid" for s in summaries):
            return StrategyResult(
                strategy=strategy,
                status="non_amortizing",
                debts=summaries,
            )
        max_months = max((s.months or 0) for s in summaries) if summaries else 0
        tot_interest = sum((s.total_interest_cents or 0) for s in summaries)
        tot_paid = sum((s.total_paid_cents or 0) for s in summaries)
        return StrategyResult(
            strategy=strategy,
            status="paid",
            months=max_months,
            total_interest_cents=tot_interest,
            total_paid_cents=tot_paid,
            interest_saved_vs_baseline_cents=0,
            months_saved_vs_baseline=0,
            debts=summaries,
        )

    # Multi-debt simulation with rollover (for avalanche/snowball) or minimum_only with one-off extra
    balances = {d.id: d.balance_cents for d in debts}
    interest_by_id = {d.id: 0 for d in debts}
    paid_by_id = {d.id: 0 for d in debts}
    months_by_id = {d.id: 0 for d in debts}

    # Apply immediate one-off extra payment before month 1, capped at remaining balances
    remaining_one_off = min(one_off_extra_cents, sum(balances.values()))
    if remaining_one_off > 0:
        ordered_for_one_off = list(debts)
        order_strategy: StrategyName = "avalanche" if strategy == "minimum_only" else strategy
        ordered_for_one_off.sort(key=lambda d: _priority_key(order_strategy, d, balances[d.id]))
        if target_debt_id:
            ordered_for_one_off.sort(key=lambda d: 0 if d.id == target_debt_id else 1)
        for d in ordered_for_one_off:
            if remaining_one_off <= 0:
                break
            take = min(balances[d.id], remaining_one_off)
            balances[d.id] -= take
            paid_by_id[d.id] += take
            remaining_one_off -= take

    # Total monthly budget for avalanche/snowball is the constant sum of all initial minimums + recurring_extra
    total_monthly_budget = sum(d.min_payment_cents for d in debts) + recurring_extra_cents

    month = 0
    while any(b > 0 for b in balances.values()):
        if month >= MAX_AMORTIZATION_MONTHS:
            return StrategyResult(
                strategy=strategy,
                status="non_amortizing",
                debts=[
                    DebtPayoffSummary(
                        debt_id=d.id,
                        label=d.label,
                        status="paid" if balances[d.id] == 0 else "non_amortizing",
                        months=months_by_id[d.id] if balances[d.id] == 0 else None,
                        total_interest_cents=interest_by_id[d.id] if balances[d.id] == 0 else None,
                        total_paid_cents=paid_by_id[d.id] if balances[d.id] == 0 else None,
                        principal_paid_cents=d.balance_cents if balances[d.id] == 0 else None,
                    )
                    for d in debts
                ],
            )
        month += 1
        active_debts = [d for d in debts if balances[d.id] > 0]
        interests = {d.id: monthly_interest_cents(balances[d.id], d.apr_bps) for d in active_debts}

        # Step 1: every active debt requires at least min(min_payment, balance + interest)
        min_allocations: dict[str, int] = {}
        for d in active_debts:
            due = balances[d.id] + interests[d.id]
            min_allocations[d.id] = min(d.min_payment_cents, due)

        # Step 2: allocate surplus (rollover of freed minimums + recurring_extra_cents) if avalanche or snowball
        extra_allocations = {d.id: 0 for d in active_debts}
        if strategy in ("avalanche", "snowball"):
            surplus = max(0, total_monthly_budget - sum(min_allocations.values()))
            ordered = sorted(active_debts, key=lambda d: _priority_key(strategy, d, balances[d.id]))
            if target_debt_id:
                ordered.sort(key=lambda d: 0 if d.id == target_debt_id else 1)
            for d in ordered:
                if surplus <= 0:
                    break
                room = (balances[d.id] + interests[d.id]) - min_allocations[d.id]
                if room > 0:
                    add = min(surplus, room)
                    extra_allocations[d.id] += add
                    surplus -= add

        # Step 3: check that total principal decreases this month; otherwise non-amortizing
        total_payment = sum(min_allocations[d.id] + extra_allocations[d.id] for d in active_debts)
        total_month_interest = sum(interests.values())
        if total_payment <= total_month_interest:
            return StrategyResult(
                strategy=strategy,
                status="non_amortizing",
                debts=[
                    DebtPayoffSummary(
                        debt_id=d.id,
                        label=d.label,
                        status="paid" if balances[d.id] == 0 else "non_amortizing",
                    )
                    for d in debts
                ],
            )
        # Also if any individual debt has payment < interest and cannot be reached before MAX_AMORTIZATION_MONTHS,
        # the loop bound or non-positive total progress catches it. For minimum_only without rollover, each active
        # debt must amortize on its own:
        if strategy == "minimum_only":
            for d in active_debts:
                if min_allocations[d.id] <= interests[d.id]:
                    return StrategyResult(
                        strategy=strategy,
                        status="non_amortizing",
                        debts=[
                            DebtPayoffSummary(
                                debt_id=item.id,
                                label=item.label,
                                status="paid" if balances[item.id] == 0 and item.id != d.id else "non_amortizing",
                            )
                            for item in debts
                        ],
                    )

        for d in active_debts:
            pay = min_allocations[d.id] + extra_allocations[d.id]
            interest = interests[d.id]
            balances[d.id] = balances[d.id] + interest - pay
            interest_by_id[d.id] += interest
            paid_by_id[d.id] += pay
            if balances[d.id] == 0:
                months_by_id[d.id] = month

    summaries = [
        DebtPayoffSummary(
            debt_id=d.id,
            label=d.label,
            status="paid",
            months=months_by_id[d.id],
            total_interest_cents=interest_by_id[d.id],
            total_paid_cents=paid_by_id[d.id],
            principal_paid_cents=d.balance_cents,
        )
        for d in debts
    ]
    total_interest = sum(interest_by_id.values())
    total_paid = sum(paid_by_id.values())
    interest_saved = None
    months_saved = None
    if baseline and baseline.status == "paid" and baseline.total_interest_cents is not None and baseline.months is not None:
        interest_saved = baseline.total_interest_cents - total_interest
        months_saved = baseline.months - month

    return StrategyResult(
        strategy=strategy,
        status="paid",
        months=month,
        total_interest_cents=total_interest,
        total_paid_cents=total_paid,
        interest_saved_vs_baseline_cents=interest_saved,
        months_saved_vs_baseline=months_saved,
        debts=summaries,
    )


def compare_and_simulate(
    debts: list[Debt],
    revision: int = 0,
    recurring_extra_cents: int = 0,
    one_off_extra_cents: int = 0,
    target_debt_id: str | None = None,
) -> DebtSimulationView:
    """Computes minimum_only baseline, Avalanche, Snowball, and optional one-off extra payment preview."""
    baseline = simulate_strategy(debts, "minimum_only")
    avalanche = simulate_strategy(
        debts,
        "avalanche",
        recurring_extra_cents=recurring_extra_cents,
        baseline=baseline,
    )
    snowball = simulate_strategy(
        debts,
        "snowball",
        recurring_extra_cents=recurring_extra_cents,
        baseline=baseline,
    )

    total_balance = sum(d.balance_cents for d in debts)
    applied_extra = min(one_off_extra_cents, total_balance)
    with_one_off = simulate_strategy(
        debts,
        "avalanche",
        recurring_extra_cents=recurring_extra_cents,
        one_off_extra_cents=one_off_extra_cents,
        target_debt_id=target_debt_id,
        baseline=avalanche,
    )

    interest_saved_one_off = None
    months_saved_one_off = None
    if (
        avalanche.status == "paid"
        and with_one_off.status == "paid"
        and avalanche.total_interest_cents is not None
        and with_one_off.total_interest_cents is not None
        and avalanche.months is not None
        and with_one_off.months is not None
    ):
        interest_saved_one_off = avalanche.total_interest_cents - with_one_off.total_interest_cents
        months_saved_one_off = avalanche.months - with_one_off.months

    one_off_preview = OneOffExtraPreview(
        requested_extra_cents=one_off_extra_cents,
        applied_extra_cents=applied_extra,
        target_debt_id=target_debt_id,
        status=with_one_off.status,
        months=with_one_off.months,
        total_interest_cents=with_one_off.total_interest_cents,
        total_paid_cents=with_one_off.total_paid_cents,
        interest_saved_cents=interest_saved_one_off,
        months_saved=months_saved_one_off,
    )

    overall_status: AmortizationStatus = "paid"
    if any(not d.terms_known for d in debts):
        overall_status = "needs_input"
    elif avalanche.status != "paid" or snowball.status != "paid":
        overall_status = "non_amortizing"

    return DebtSimulationView(
        revision=revision,
        status=overall_status,
        rounding_rule=ROUNDING_RULE,
        recurring_extra_cents=recurring_extra_cents,
        one_off_extra_cents=one_off_extra_cents,
        baseline=baseline,
        avalanche=avalanche,
        snowball=snowball,
        one_off_preview=one_off_preview,
    )
