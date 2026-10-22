"""Pure simulated-rule transitions. Persistence owns idempotency."""

from datetime import date
from typing import Any

from finagent.domain.math import cash_projection
from finagent.domain.models import Money, Transaction, UserProfile


def matches(rule: dict[str, Any], transaction: Transaction) -> bool:
    """Match active rules by category, merchant, or incoming schedule date."""
    if rule["status"] != "active":
        return False
    trigger = rule["trigger"]
    if trigger["kind"] == "category":
        return transaction.amount < 0 and transaction.category == trigger["value"]
    if trigger["kind"] == "merchant":
        return transaction.amount < 0 and transaction.merchant == trigger["value"]
    return (transaction.amount > 0 or transaction.category == "schedule") and date.fromisoformat(
        transaction.date
    ).day == int(trigger["value"])


def execute(
    rule: dict[str, Any], profile: UserProfile, transaction: Transaction, reserved_today: int = 0
) -> dict[str, Any] | None:
    """Simulate a matching transfer only if projected cash remains above its floor."""
    if not matches(rule, transaction):
        return None
    amount = rule["amount"]
    if type(amount) is not int or amount <= 0:
        raise ValueError("Rule amount must be a positive integer")
    after = (
        cash_projection(profile, date.fromisoformat(transaction.date), amount)["buffer_after"]
        - reserved_today
    )
    floor = max(profile.min_cash_buffer, rule["affordability_floor"])
    outcome = "executed" if after >= floor else "skipped_unaffordable"
    return {
        "rule_id": rule["id"],
        "transaction_id": transaction.id,
        "executed_at": transaction.date,
        "amount": amount,
        "outcome": outcome,
        "buffer_before": profile.cash_balance,
        "buffer_after": Money(profile.cash_balance).plus(Money(-amount)).cents
        if outcome == "executed"
        else profile.cash_balance,
        "projected_buffer_after": after,
        "reason": "Within your cash buffer"
        if outcome == "executed"
        else "Would use your protected cash buffer",
    }
