"""Framework-free, validated financial records. All amounts are minor units."""

from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal


def nonnegative(value: int, name: str) -> None:
    """Reject negative or non-integer minor-unit amounts."""
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(frozen=True)
class Money:
    """An integer minor-unit amount and explicit ISO currency."""

    cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if type(self.cents) is not int or len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("Money needs integer minor units and an uppercase currency code")

    def plus(self, other: "Money") -> "Money":
        """Add amounts only when their currencies match."""
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.cents + other.cents, self.currency)

    def scale(self, multiplier: Decimal) -> "Money":
        """Multiply using decimal arithmetic and half-up minor-unit rounding."""
        return Money(
            int((Decimal(self.cents) * multiplier).quantize(Decimal(1), rounding=ROUND_HALF_UP)),
            self.currency,
        )


@dataclass
class FixedCost:
    """A monthly obligation; due dates are restricted to all-month-valid days."""

    name: str
    amount: int
    due_day: int = 1
    category: str = "bills"

    def __post_init__(self) -> None:
        nonnegative(self.amount, "Fixed cost")
        if not 1 <= self.due_day <= 28:
            raise ValueError("Due day must be between 1 and 28")


@dataclass
class Debt:
    """Debt APR is a percentage represented as a decimal string."""

    name: str
    balance: int
    annual_rate: str
    min_payment: int

    def __post_init__(self) -> None:
        nonnegative(self.balance, "Debt balance")
        nonnegative(self.min_payment, "Minimum payment")
        rate = Decimal(self.annual_rate)
        if not rate.is_finite() or not 0 <= rate <= 100:
            raise ValueError("Annual rate must be between 0 and 100")


@dataclass
class SavingsAccount:
    """A simulated savings account with an optional goal."""

    name: str
    balance: int
    kind: Literal["emergency", "goal"] = "emergency"
    target_amount: int | None = None
    target_date: str | None = None

    def __post_init__(self) -> None:
        nonnegative(self.balance, "Savings balance")
        if self.kind not in ("emergency", "goal"):
            raise ValueError("Unknown savings kind")
        if self.target_amount is not None:
            nonnegative(self.target_amount, "Target")
        if self.target_date:
            date.fromisoformat(self.target_date)


@dataclass
class UserProfile:
    """Single-user demo profile and its cash buffer, goals, and obligations."""

    id: str = "P2"
    name: str = "Alex"
    currency: str = "USD"
    monthly_income: int = 380000
    income_day: int = 1
    priority: str = "debt"
    min_cash_buffer: int = 50000
    cash_balance: int = 240000
    auto_save_pct: int = 5
    emergency_months: int = 3
    fixed_costs: list[FixedCost] = field(default_factory=list)
    debts: list[Debt] = field(default_factory=list)
    savings: list[SavingsAccount] = field(default_factory=list)
    goal: dict[str, Any] = field(default_factory=dict)
    declined_transaction: bool = False
    created_at: str = "2026-01-01T00:00:00+00:00"

    def __post_init__(self) -> None:
        for name in ("monthly_income", "min_cash_buffer", "cash_balance"):
            nonnegative(getattr(self, name), name)
        if self.priority not in ("debt", "savings", "budget"):
            raise ValueError("Choose debt, savings, or budget")
        if type(self.auto_save_pct) is not int or not 0 <= self.auto_save_pct <= 10:
            raise ValueError("Auto-save must be 0–10 percent")
        if not 1 <= self.income_day <= 28 or not 1 <= self.emergency_months <= 12:
            raise ValueError("Invalid income day or emergency target")
        Money(0, self.currency)
        if self.goal.get("target_amount") is not None:
            nonnegative(self.goal["target_amount"], "Goal target")
        if self.goal.get("target_date"):
            date.fromisoformat(self.goal["target_date"])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfile":
        """Rehydrate and validate a profile and all nested obligations."""
        values = dict(data)
        values["fixed_costs"] = [FixedCost(**x) for x in data.get("fixed_costs", [])]
        values["debts"] = [Debt(**x) for x in data.get("debts", [])]
        values["savings"] = [SavingsAccount(**x) for x in data.get("savings", [])]
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable profile data."""
        return asdict(self)


@dataclass(frozen=True)
class Transaction:
    """A dated inflow (positive) or outflow (negative) in minor units."""

    id: str
    user_id: str
    date: str
    amount: int
    description: str
    merchant: str
    category: str
    source: str = "synthetic"

    def __post_init__(self) -> None:
        date.fromisoformat(self.date)
        if type(self.amount) is not int or self.source not in ("synthetic", "csv", "replay"):
            raise ValueError("Invalid transaction amount or source")


@dataclass
class Candidate:
    """A deterministic proposal; facts are the only source of numeric claims."""

    id: str
    agent: str
    type: str
    title: str
    params: dict[str, Any]
    impact: dict[str, int]
    affordable: bool
    facts: dict[str, int]
    effort: int = 1
    reversible: bool = True
    urgency: int = 0
    stability: int = 1
    risk: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.effort <= 3:
            raise ValueError("Effort must be 1–3")
