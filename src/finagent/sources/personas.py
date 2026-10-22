"""Seeded demonstration fixtures, independent of the machine clock."""

import csv
import random
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Protocol

import yaml

from finagent.domain.models import Debt, FixedCost, SavingsAccount, Transaction, UserProfile

ANCHOR = date(2026, 10, 22)


def persona(key: str) -> UserProfile:
    profiles = {
        "P1": UserProfile(
            id="P1",
            name="Maya",
            monthly_income=160000,
            cash_balance=95000,
            priority="budget",
            min_cash_buffer=20000,
            fixed_costs=[FixedCost("Rent", 60000), FixedCost("Transport", 5000, 5)],
            savings=[SavingsAccount("Safety net", 15000)],
        ),
        "P2": UserProfile(
            id="P2",
            name="Alex",
            fixed_costs=[
                FixedCost("Rent", 120000),
                FixedCost("Utilities", 16000, 12),
                FixedCost("Transport", 9000, 5),
            ],
            debts=[
                Debt("Credit card", 480000, "21.9", 16000),
                Debt("Personal loan", 180000, "8.5", 9000),
            ],
            savings=[SavingsAccount("Safety net", 220000)],
        ),
        "P3": UserProfile(
            id="P3",
            name="Sam",
            monthly_income=260000,
            cash_balance=180000,
            priority="savings",
            fixed_costs=[FixedCost("Rent", 80000), FixedCost("Utilities", 12000, 12)],
            savings=[SavingsAccount("Safety net", 0)],
        ),
        "P4": UserProfile(
            id="P4",
            name="Jordan",
            monthly_income=720000,
            cash_balance=410000,
            priority="budget",
            fixed_costs=[FixedCost("Rent", 220000), FixedCost("Utilities", 18000, 12)],
            savings=[SavingsAccount("Safety net", 400000)],
        ),
    }
    if key not in profiles:
        raise ValueError("Choose a persona from P1–P4")
    return profiles[key]


def generate(key: str, seed: int = 42) -> list[Transaction]:
    rng = random.Random(f"{seed}:{key}")
    p = persona(key)
    rows: list[Transaction] = []

    def add(day: date, amount: int, merchant: str, category: str) -> None:
        rows.append(
            Transaction(
                f"{key}-{len(rows):04}", key, day.isoformat(), amount, merchant, merchant, category
            )
        )

    for month in range(5, 11):
        add(
            date(2026, month, 1),
            p.monthly_income if key != "P3" else rng.randint(210000, 310000),
            "Income",
            "income",
        )
        for cost in p.fixed_costs:
            add(date(2026, month, cost.due_day), -cost.amount, cost.name, cost.category)
        add(date(2026, month, 7), -1299, "Spotify", "subscriptions")
        if key == "P4":
            for i, name in enumerate(["Netflix", "Cloud", "Fitness", "News"]):
                if month >= 5 + i:
                    add(date(2026, month, 8 + i), -(1599 + i * 500), name, "subscriptions")
        day = date(2026, month, 1)
        while day.month == month and day <= ANCHOR:
            if day.weekday() == 2:
                add(day, -rng.randint(4500, 6500), "Market", "groceries")
            if day.weekday() in (5, 6):
                add(day, -rng.randint(1800, 3200) * (2 if key == "P4" else 1), "Takeout", "dining")
            day += timedelta(days=1)
    return sorted([t for t in rows if t.date <= ANCHOR.isoformat()], key=lambda t: (t.date, t.id))


def seed_files(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    actions = {
        "P1": "weekend_habit",
        "P2": "extra_debt",
        "P3": "emergency_save",
        "P4": "subscription_review",
    }
    for key, action in actions.items():
        rows = generate(key)
        with (root / f"{key}.csv").open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(asdict(rows[0])))
            writer.writeheader()
            writer.writerows(asdict(t) for t in rows)
        (root / f"{key}.yaml").write_text(
            yaml.safe_dump(
                {
                    "profile": persona(key).to_dict(),
                    "seed": 42,
                    "as_of": ANCHOR.isoformat(),
                    "expected_top_action": action,
                    "rationale": {
                        "P1": "A repeat weekend dining pattern offers a small reversible saving.",
                        "P2": "Extra repayment reduces high-rate credit-card interest.",
                        "P3": "An initial contribution builds the missing emergency fund.",
                        "P4": "Several recurring services make a subscription review useful.",
                    }[key],
                },
                sort_keys=False,
            )
        )


class TransactionSource(Protocol):
    def fetch(self, user_id: str, since: date) -> Iterable[Transaction]: ...


class SyntheticSource:
    def fetch(self, user_id: str, since: date) -> Iterable[Transaction]:
        return [t for t in generate(user_id) if t.date >= since.isoformat()]


class ReplaySource:
    def __init__(self, transactions: list[Transaction]) -> None:
        self.transactions = transactions

    def fetch(self, user_id: str, since: date) -> Iterable[Transaction]:
        return sorted(
            [t for t in self.transactions if t.user_id == user_id and t.date >= since.isoformat()],
            key=lambda t: (t.date, t.id),
        )
