"""Pure specialist agents. No provider or database dependency."""

from datetime import date
from decimal import Decimal
from typing import Protocol

from finagent.analysis.patterns import analyse
from finagent.domain.math import amortize, cash_projection, contribution_months, portfolio_payoff
from finagent.domain.models import Candidate, Money, Transaction, UserProfile


class Agent(Protocol):
    """A deterministic financial proposal generator."""

    def analyse(
        self, profile: UserProfile, transactions: list[Transaction], now: date
    ) -> list[Candidate]:
        """Return proposals without mutating inputs."""
        ...


def proposal(
    p: UserProfile,
    now: date,
    kind: str,
    agent: str,
    title: str,
    amount: int,
    effect: int,
    **facts: int,
) -> Candidate:
    """Construct an affordable proposal and a canonical numeric fact set."""
    projection = cash_projection(p, now, amount)
    data = {
        "amount": amount,
        "monthly_cash_effect": effect,
        "buffer_after": projection["buffer_after"],
        "minimum_buffer": p.min_cash_buffer,
        **facts,
    }
    return Candidate(
        f"{p.id}:{kind}",
        agent,
        kind,
        title,
        {"amount": amount, "schedule_day": p.income_day, "account": "Safety net"},
        {
            "monthly_cash_effect": effect,
            "goal_months_delta": facts.get("months_saved", 0),
            "interest_saved": facts.get("interest_saved", 0),
            "buffer_after": projection["buffer_after"],
        },
        projection["buffer_after"] >= p.min_cash_buffer,
        data,
    )


class BudgetAgent:
    """Find recurring-service, dining-habit, and category baseline opportunities."""

    def analyse(
        self, profile: UserProfile, transactions: list[Transaction], now: date
    ) -> list[Candidate]:
        """Produce reversible budget options grounded in observed outflows."""
        patterns = analyse(profile, transactions, now)
        result = []
        subscriptions = [r for r in patterns["recurring"] if r["category"] == "subscriptions"]
        if len(subscriptions) >= 2:
            amount = min(r["amount"] for r in subscriptions)
            c = proposal(
                profile,
                now,
                "subscription_review",
                "budget",
                "Make room with a subscription review",
                0,
                amount,
                services=len(subscriptions),
                potential_saving=amount,
            )
            c.params["review_only"] = True
            c.urgency = 1
            result.append(c)
        dining = [
            t
            for t in transactions
            if t.category == "dining" and date.fromisoformat(t.date).weekday() >= 5
        ]
        if len(dining) >= 4:
            amount = min(1000, max(100, sum(-t.amount for t in dining) // len(dining) // 4))
            c = proposal(
                profile,
                now,
                "weekend_habit",
                "budget",
                "Turn a weekend habit into a small saving",
                amount,
                amount,
                matching_transactions=len(dining),
            )
            c.params.update({"category": "dining", "trigger": "category"})
            result.append(c)
        for trend in patterns["trends"]:
            if trend["baseline"] > 0 and trend["latest"] > trend["baseline"] * 12 // 10:
                c = proposal(
                    profile,
                    now,
                    "category_reallocation",
                    "budget",
                    f"Review room in {trend['category']}",
                    0,
                    trend["latest"] - trend["baseline"],
                    baseline=trend["baseline"],
                    latest=trend["latest"],
                )
                c.params.update({"category": trend["category"], "review_only": True})
                c.effort = 3
                c.risk = 2  # A broad category change is less certain than an observed habit.
                result.append(c)
                break
        return result


class DebtAgent:
    """Calculate extra-payment and avalanche-versus-snowball outcomes."""

    def analyse(
        self, profile: UserProfile, transactions: list[Transaction], now: date
    ) -> list[Candidate]:
        """Offer an extra payment only when it reduces a payable debt's interest."""
        if not profile.debts:
            return []
        debt = max(profile.debts, key=lambda d: Decimal(d.annual_rate))
        spare = max(0, cash_projection(profile, now)["buffer_after"] - profile.min_cash_buffer)
        amount = min(Money(profile.monthly_income).scale(Decimal("0.05")).cents, spare // 2)
        base, extra = amortize(debt), amortize(debt, amount)
        if not amount or not base.payable or not extra.payable:
            return []
        avalanche = portfolio_payoff(profile.debts, amount, "avalanche")
        snowball = portfolio_payoff(profile.debts, amount, "snowball")
        c = proposal(
            profile,
            now,
            "extra_debt",
            "debt",
            f"Give your {debt.name.lower()} a little extra",
            amount,
            -amount,
            interest_saved=max(0, base.interest - extra.interest),
            months_saved=max(0, base.months - extra.months),
            current_months=base.months,
            proposed_months=extra.months,
            avalanche_interest=avalanche.interest,
            snowball_interest=snowball.interest,
            debt_balance=debt.balance,
        )
        c.params["account"] = debt.name
        c.urgency = int(Decimal(debt.annual_rate) >= 15)
        return [c]


class SavingsAgent:
    """Build an emergency cushion without crossing the cash floor."""

    def analyse(
        self, profile: UserProfile, transactions: list[Transaction], now: date
    ) -> list[Candidate]:
        """Offer a 5–10% contribution, capped by projected affordability."""
        target = sum(c.amount for c in profile.fixed_costs) * profile.emergency_months
        saved = sum(s.balance for s in profile.savings if s.kind == "emergency")
        account = next((a.name for a in profile.savings if a.kind == "emergency"), None)
        kind, title = "emergency_save", "Add a little breathing room to your safety net"
        if profile.goal.get("target_amount"):
            linked = next(
                (a for a in profile.savings if a.name == profile.goal.get("linked_account")), None
            )
            if linked:
                target, saved, account = profile.goal["target_amount"], linked.balance, linked.name
                kind, title = "goal_save", "Take a small step toward your savings goal"
        if account is None or saved >= target:
            return []
        spare = max(0, cash_projection(profile, now)["buffer_after"] - profile.min_cash_buffer)
        amount = min(
            Money(profile.monthly_income).scale(Decimal(max(5, profile.auto_save_pct)) / 100).cents,
            spare,
            target - saved,
        )
        if amount <= 0:
            return []
        baseline = Money(profile.monthly_income).scale(Decimal(profile.auto_save_pct) / 100).cents
        months = contribution_months(target - saved, amount)
        c = proposal(
            profile,
            now,
            kind,
            "savings",
            title,
            amount,
            -amount,
            target=target,
            saved=saved,
            proposed_months=months,
            current_months=contribution_months(target - saved, baseline),
            months_saved=max(0, contribution_months(target - saved, baseline) - months),
        )
        c.urgency = int(saved == 0)
        c.params["account"] = account
        return [c]


def candidates(profile: UserProfile, transactions: list[Transaction], now: date) -> list[Candidate]:
    """Gather each specialist's proposals in stable order."""
    return [
        candidate
        for agent in (BudgetAgent(), DebtAgent(), SavingsAgent())
        for candidate in agent.analyse(profile, transactions, now)
    ]
