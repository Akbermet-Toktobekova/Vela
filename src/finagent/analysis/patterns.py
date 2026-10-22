"""Explainable transaction patterns; inference remains an unconfirmed assumption."""

from collections import defaultdict
from datetime import date
from statistics import median
from typing import Any

from finagent.domain.math import cash_projection
from finagent.domain.models import Transaction, UserProfile


def analyse(profile: UserProfile, transactions: list[Transaction], now: date) -> dict[str, Any]:
    """Find monthly recurring outflows, complete-month trends, and cash shortfalls."""
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    monthly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    weekday, weekend = 0, 0
    for t in transactions:
        if t.amount >= 0 or t.date > now.isoformat():
            continue
        grouped[t.merchant].append(t)
        monthly[t.date[:7]][t.category] -= t.amount
        if date.fromisoformat(t.date).weekday() >= 5:
            weekend -= t.amount
        else:
            weekday -= t.amount
    recurring = []
    for merchant, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda t: t.date)
        if len(rows) < 3:
            continue
        intervals = [
            (date.fromisoformat(b.date) - date.fromisoformat(a.date)).days
            for a, b in zip(rows, rows[1:])
        ]
        amounts = [-t.amount for t in rows]
        typical = int(median(amounts))
        if all(25 <= d <= 35 for d in intervals) and max(amounts) - min(amounts) <= max(
            1, typical // 10
        ):
            recurring.append(
                {
                    "merchant": merchant,
                    "amount": typical,
                    "due_day": date.fromisoformat(rows[-1].date).day,
                    "category": rows[-1].category,
                    "confirmed": any(c.name == merchant for c in profile.fixed_costs),
                }
            )
    months = sorted(m for m in monthly if m < now.strftime("%Y-%m"))[-4:]
    latest = monthly[months[-1]] if months else {}
    categories = sorted(set(k for m in months for k in monthly[m]))
    trends = [
        {
            "category": c,
            "latest": latest.get(c, 0),
            "baseline": int(median([monthly[m].get(c, 0) for m in months[:-1]]))
            if len(months) > 1
            else 0,
        }
        for c in categories
    ]
    projection = cash_projection(profile, now)
    return {
        "recurring": recurring,
        "trends": trends,
        "categories": dict(latest),
        "weekday": weekday,
        "weekend": weekend,
        "focus_area": max(latest, key=lambda k: latest[k])
        if latest
        else "Build a picture of your spending",
        "projection": projection,
        "shortfall": projection["buffer_after"] < profile.min_cash_buffer,
    }
