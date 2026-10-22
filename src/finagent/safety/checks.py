"""Conservative tone and numeric allow-list checks."""

import re
from datetime import datetime, timedelta
from typing import Any

BAD = re.compile(
    r"\b(overspent|failed|failure|irresponsible|stupid|careless|shame|blame|reckless|lazy|urgent|alarm|panic|must act now)\b",
    re.I,
)
NUMBERS = re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?")


def tone_ok(text: str) -> bool:
    return not bool(BAD.search(text))


def faithful(text: str, facts: Any) -> bool:
    allowed: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, int) and not isinstance(value, bool):
            allowed.update(
                [str(value), f"{value / 100:.2f}", f"{value / 100:.2f}".rstrip("0").rstrip(".")]
            )
        elif isinstance(value, str):
            allowed.update(n.replace(",", "") for n in NUMBERS.findall(value))

    visit(facts)
    return all(n.replace(",", "") in allowed for n in NUMBERS.findall(text))


def guard_reason(profile: Any, projection: dict[str, int]) -> str | None:
    if profile.declined_transaction:
        return "A transaction needs your attention. Coaching is taking a pause."
    if profile.cash_balance < profile.min_cash_buffer:
        return "Your cash is below the buffer you chose. Coaching is taking a pause."
    if projection["buffer_after"] < profile.min_cash_buffer:
        return "Upcoming commitments may use your buffer. Coaching is taking a pause."
    return None


def guard_until(now: datetime, hours: int = 48) -> str:
    return (now + timedelta(hours=hours)).isoformat()
