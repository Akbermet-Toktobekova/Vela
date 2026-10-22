"""Deterministic minor-unit cash-flow and amortization calculations."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from finagent.domain.models import Debt, Money, UserProfile, nonnegative


@dataclass(frozen=True)
class Payoff:
    """An exact monthly rounded debt payoff, or a non-amortizing result."""

    months: int
    interest: int
    payable: bool


def amortize(debt: Debt, extra: int = 0) -> Payoff:
    """Accrue monthly APR interest then pay; cap at 1,200 months."""
    nonnegative(extra, "Extra payment")
    balance, interest, months = debt.balance, 0, 0
    payment = Money(debt.min_payment).plus(Money(extra)).cents
    rate = Decimal(debt.annual_rate) / Decimal(1200)
    while balance > 0 and months < 1200:
        charge = Money(balance).scale(rate).cents
        if payment <= charge:
            return Payoff(months, interest, False)
        interest = Money(interest).plus(Money(charge)).cents
        balance = max(0, Money(balance).plus(Money(charge)).plus(Money(-payment)).cents)
        months += 1
    return Payoff(months, interest, balance == 0)


def portfolio_payoff(debts: list[Debt], extra: int, strategy: str) -> Payoff:
    """Keep the total payment fixed, rolling released payments into priority debt."""
    nonnegative(extra, "Extra payment")
    if strategy not in ("avalanche", "snowball"):
        raise ValueError("Unknown payoff strategy")
    balances = [d.balance for d in debts]
    budget = sum(d.min_payment for d in debts) + extra
    total_interest = 0
    for month in range(1201):
        if not any(balances):
            return Payoff(month, total_interest, True)
        if month == 1200:
            break
        charges = [
            Money(b).scale(Decimal(d.annual_rate) / Decimal(1200)).cents
            for b, d in zip(balances, debts)
        ]
        if budget <= sum(charges):
            return Payoff(month, total_interest, False)
        total_interest += sum(charges)
        balances = [b + c for b, c in zip(balances, charges)]
        left = budget
        for i, debt in enumerate(debts):
            paid = min(balances[i], debt.min_payment, left)
            balances[i] -= paid
            left -= paid
        order = sorted(
            range(len(debts)),
            key=lambda i: (-Decimal(debts[i].annual_rate), i)
            if strategy == "avalanche"
            else (Decimal(balances[i]), i),
        )
        for i in order:
            paid = min(balances[i], left)
            balances[i] -= paid
            left -= paid
    return Payoff(1200, total_interest, False)


def next_income(profile: UserProfile, now: date) -> date:
    """Return the next strictly future income date."""
    if now.day < profile.income_day:
        return now.replace(day=profile.income_day)
    return (now.replace(day=28) + timedelta(days=4)).replace(day=profile.income_day)


def cash_projection(profile: UserProfile, now: date, transfer: int = 0) -> dict[str, int]:
    """Reserve all fixed and debt obligations due before the next income."""
    nonnegative(transfer, "Transfer")
    end = next_income(profile, now)
    due = 0
    day = now + timedelta(days=1)
    while day < end:
        due += sum(c.amount for c in profile.fixed_costs if c.due_day == day.day)
        if day.day == min(28, monthrange(day.year, day.month)[1]):
            due += sum(d.min_payment for d in profile.debts)
        day += timedelta(days=1)
    balance = (
        Money(profile.cash_balance, profile.currency)
        .plus(Money(-transfer - due, profile.currency))
        .cents
    )
    days = (end - now).days
    return {
        "buffer_after": balance,
        "reserved": due,
        "days_to_income": days,
        "safe_to_spend": max(0, balance - profile.min_cash_buffer) // days,
    }


def contribution_months(remaining: int, contribution: int) -> int:
    """Ceiling months to reach a goal; zero denotes no feasible contribution."""
    nonnegative(remaining, "Remaining target")
    nonnegative(contribution, "Contribution")
    return (remaining + contribution - 1) // contribution if contribution else 0


def goal_projection(profile: UserProfile, now: date) -> dict[str, int | str | bool | None]:
    """Project a constant-contribution goal date, without assuming savings interest."""
    target = sum(c.amount for c in profile.fixed_costs) * profile.emergency_months
    saved = sum(a.balance for a in profile.savings if a.kind == "emergency")
    account = "Emergency fund"
    linked = next(
        (a for a in profile.savings if a.name == profile.goal.get("linked_account")), None
    )
    if linked and profile.goal.get("target_amount"):
        target, saved, account = profile.goal["target_amount"], linked.balance, linked.name
    remaining = max(0, target - saved)
    contribution = Money(profile.monthly_income).scale(Decimal(profile.auto_save_pct) / 100).cents
    months = contribution_months(remaining, contribution)
    projected: date | None = None
    if remaining == 0:
        projected = now
    elif contribution > 0:
        index = now.year * 12 + now.month - 1 + months
        year, month = divmod(index, 12)
        projected = date(year, month + 1, min(now.day, monthrange(year, month + 1)[1]))
    deadline = (
        date.fromisoformat(profile.goal["target_date"]) if profile.goal.get("target_date") else None
    )
    return {
        "account": account,
        "target": target,
        "saved": saved,
        "remaining": remaining,
        "contribution": contribution,
        "months": months,
        "projected_date": projected.isoformat() if projected else None,
        "target_date": deadline.isoformat() if deadline else None,
        "on_schedule": projected <= deadline if projected and deadline else None,
    }
