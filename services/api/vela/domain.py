"""Pure financial rules. Money is always EUR integer cents, never floats."""
from collections import defaultdict
from datetime import date, timedelta
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
PositiveMoney = Annotated[int, Field(strict=True, gt=0, le=1_000_000_000)]
SignedMoney = Annotated[int, Field(strict=True, ge=-1_000_000_000, le=1_000_000_000)]

CATEGORIES = ("income", "housing", "utilities", "groceries", "dining", "transport", "shopping",
              "subscriptions", "health", "debt", "transfers", "cash", "fees", "other")
Category = Literal["income", "housing", "utilities", "groceries", "dining", "transport", "shopping",
                   "subscriptions", "health", "debt", "transfers", "cash", "fees", "other"]
MAX_TRANSACTIONS = 3000


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, json_schema_serialization_defaults_required=True)


class Obligation(Record):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=100)
    amount: PositiveMoney
    due: date
    kind: Literal["living", "rent", "debt", "other"] = "other"


class Snapshot(Record):
    nickname: str = Field(default="Alex", min_length=1, max_length=40)
    currency: Literal["EUR"] = "EUR"
    as_of: date
    horizon: date
    cash: Money
    saved: Money = 0
    protected: Money
    goal_target: PositiveMoney = 50000
    goal_name: str = Field(default="Emergency reserve", min_length=1, max_length=60)
    obligations: list[Obligation] = Field(default_factory=list, max_length=100)
    obligations_complete: bool = False
    debt_known: bool = False
    provenance: Literal["synthetic", "manual", "import"] = "manual"

    @model_validator(mode="after")
    def validate_window(self):
        if not self.as_of <= self.horizon <= self.as_of + timedelta(days=93):
            raise ValueError("Use a planning horizon of up to 93 days after the balance date.")
        if len({o.id for o in self.obligations}) != len(self.obligations):
            raise ValueError("Obligation IDs must be unique.")
        if any(o.due < self.as_of or o.due > self.horizon for o in self.obligations):
            raise ValueError("All unpaid bills must be dated between today and your plan-through date.")
        if self.saved > self.cash:
            raise ValueError("Money already set aside is part of your cash, so it cannot be larger than your cash.")
        return self


class Transaction(Record):
    id: str = Field(min_length=1, max_length=80)
    date: date
    description: str = Field(min_length=1, max_length=200)
    amount: SignedMoney
    category: Category = "other"
    source: str = Field(default="manual", max_length=120)


class Action(Record):
    id: str
    amount: PositiveMoney
    status: Literal["planned", "completed", "cancelled"] = "planned"
    created_on: date
    completed_on: date | None = None


class State(Record):
    revision: int = 0
    snapshot: Snapshot | None = None
    actions: list[Action] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)
    income_ids: list[str] = Field(default_factory=list)
    deferred: bool = False
    transactions: list[Transaction] = Field(default_factory=list)


class Recommendation(Record):
    kind: Literal["save", "clarify", "shortfall", "maintain", "goal_reached"]
    amount: Money
    message: str
    policy: str | None = None
    clarify_field: Literal["debt_known", "obligations_complete", "refresh"] | None = None


class ActionView(Action):
    can_complete: bool


class CategoryTotal(Record):
    category: str
    amount: int


class Summary(Record):
    transaction_count: int
    period_start: date | None
    period_end: date | None
    income: int
    spending: int
    top_categories: list[CategoryTotal]


class Breakdown(Record):
    cash: int
    saved: int
    protected: int
    bills: int
    planned: int


class StateView(Record):
    revision: int
    snapshot: Snapshot | None
    actions: list[ActionView] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)
    income_ids: list[str] = Field(default_factory=list)
    deferred: bool
    available: int
    breakdown: Breakdown
    recommendation: Recommendation
    summary: Summary
    mode: Literal["local"]


class PreviewView(Record):
    revision: int
    amount: Money
    eligible: bool
    remaining: int
    goal_after: int


def fixture(today: date) -> Snapshot:
    return Snapshot(as_of=today, horizon=today + timedelta(days=30), cash=100000,
                    protected=10000, obligations_complete=True, debt_known=True, provenance="synthetic",
                    obligations=[
                        Obligation(id="rent", label="Rent", amount=60000, due=today+timedelta(days=5), kind="rent"),
                        Obligation(id="living", label="Necessary living costs", amount=15000, due=today+timedelta(days=15), kind="living"),
                        Obligation(id="debt", label="Required debt payment", amount=5000, due=today+timedelta(days=20), kind="debt"),
                    ])


def capacity(state: State, exclude_action: str | None = None) -> int:
    s = state.snapshot
    if s is None:
        return 0
    reserved = sum(a.amount for a in state.actions if a.status == "planned" and a.id != exclude_action)
    # No forecast income is counted. Unpaid dated obligations remain protected even if overdue.
    balance = s.cash - s.saved - s.protected - reserved
    lowest = balance
    for obligation in sorted(s.obligations, key=lambda o: (o.due, o.id)):
        balance -= obligation.amount
        lowest = min(lowest, balance)
    return lowest


def eligibility(state: State, today: date) -> tuple[str, str] | None:
    """Returns (field, question) when the snapshot needs the user's input before planning."""
    s = state.snapshot
    if s is None:
        return ("refresh", "Add your balance to see your next step.")
    if today < s.as_of or today > s.as_of + timedelta(days=7) or today > s.horizon:
        return ("refresh", "Your balance is more than a week old. Update it before making a new plan.")
    if not s.debt_known:
        return ("debt_known", "Are all required debt payments (loans, credit cards) included in your bills?")
    if not s.obligations_complete:
        return ("obligations_complete", "Are all bills you still need to pay before your plan-through date included?")
    return None


def suggested_amount(available: int, remaining: int) -> int:
    """Illustrative policy: a fifth of what is free, rounded down to €5, capped by the goal."""
    if available < 500 or remaining <= 0:
        return 0
    fifth = (available // 5) // 500 * 500
    return min(remaining, available, max(500, fifth))


def recommendation(state: State, today: date) -> dict:
    reason = eligibility(state, today)
    if reason:
        return {"kind": "clarify", "amount": 0, "message": reason[1], "clarify_field": reason[0]}
    available = capacity(state)
    if available < 0:
        return {"kind": "shortfall", "amount": 0, "message": "Your bills and buffer are larger than your cash right now. Keep your money available and review your bills."}
    if any(a.status == "planned" for a in state.actions):
        return {"kind": "maintain", "amount": 0, "message": "You already have a step in your plan. Mark it done when you've set the money aside."}
    if state.deferred:
        return {"kind": "maintain", "amount": 0, "message": "Okay, no step for now. Update your balance whenever you're ready."}
    remaining = max(0, state.snapshot.goal_target - state.snapshot.saved)
    if remaining == 0:
        return {"kind": "goal_reached", "amount": 0, "message": "You've reached your goal. Raise the target or set a new goal to keep going."}
    amount = suggested_amount(available, remaining)
    if not amount:
        return {"kind": "maintain", "amount": 0, "message": "There isn't enough free money for a new step right now. That's okay."}
    return {"kind": "save", "amount": amount, "message": "About a fifth of what's free until your plan-through date.",
            "policy": "fifth-of-available-v1"}


def summary(state: State) -> dict:
    txns = state.transactions
    if not txns:
        return {"transaction_count": 0, "period_start": None, "period_end": None, "income": 0, "spending": 0, "top_categories": []}
    end = max(t.date for t in txns)
    start = end - timedelta(days=29)
    recent = [t for t in txns if t.date >= start]
    by_cat: dict[str, int] = defaultdict(int)
    for t in recent:
        if t.amount < 0 and t.category != "transfers":
            by_cat[t.category] += -t.amount
    top = sorted(by_cat.items(), key=lambda kv: -kv[1])[:6]
    return {"transaction_count": len(txns), "period_start": start.isoformat(), "period_end": end.isoformat(),
            "income": sum(t.amount for t in recent if t.amount > 0 and t.category != "transfers"),
            "spending": sum(-t.amount for t in recent if t.amount < 0 and t.category != "transfers"),
            "top_categories": [{"category": c, "amount": a} for c, a in top]}


def view(state: State, today: date) -> dict:
    data = state.model_dump(mode="json", exclude={"transactions"})
    s = state.snapshot
    data.update(available=capacity(state), recommendation=recommendation(state, today), mode="local",
                summary=summary(state),
                breakdown={"cash": s.cash if s else 0, "saved": s.saved if s else 0, "protected": s.protected if s else 0,
                           "bills": sum(o.amount for o in s.obligations) if s else 0,
                           "planned": sum(a.amount for a in state.actions if a.status == "planned")})
    for action in data["actions"]:
        action["can_complete"] = (action["status"] == "planned" and eligibility(state, today) is None
                                  and capacity(state, action["id"]) >= action["amount"])
    return data


def accept(state: State, amount: int, action_id: str, today: date):
    reason = eligibility(state, today)
    if reason:
        raise ValueError(reason[1])
    if any(a.status == "planned" for a in state.actions):
        raise ValueError("Finish or cancel the existing plan first.")
    if amount <= 0 or amount > capacity(state) or amount > state.snapshot.goal_target - state.snapshot.saved:
        raise ValueError("This amount is above what's free or what's left of your goal.")
    state.actions.append(Action(id=action_id, amount=amount, created_on=today))
    state.deferred = False


def complete(state: State, action_id: str, today: date):
    action = next((a for a in state.actions if a.id == action_id), None)
    if not action:
        raise ValueError("Plan not found.")
    if action.status == "completed":
        return
    if action.status != "planned":
        raise ValueError("This plan is no longer active.")
    reason = eligibility(state, today)
    if reason:
        raise ValueError(reason[1])
    if action.amount > capacity(state, action_id):
        raise ValueError("Your free amount has changed. Review or cancel this plan.")
    # Allocation in the same cash pool. No bank transfer is claimed or performed.
    state.snapshot.saved += action.amount
    action.status = "completed"
    action.completed_on = today


def merge_transactions(state: State, incoming: list[Transaction]) -> int:
    """Adds transactions, skipping exact duplicates (same date, amount and description). Returns count added."""
    seen = {(t.date, t.amount, t.description.lower()) for t in state.transactions}
    added = 0
    for t in incoming:
        key = (t.date, t.amount, t.description.lower())
        if key in seen:
            continue
        seen.add(key)
        state.transactions.append(t)
        added += 1
    state.transactions.sort(key=lambda t: (t.date, t.id), reverse=True)
    del state.transactions[MAX_TRANSACTIONS:]
    return added
