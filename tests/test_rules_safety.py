from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from finagent.domain.models import Transaction
from finagent.rules.engine import execute, matches
from finagent.safety.checks import faithful, guard_reason, guard_until, tone_ok
from finagent.sources.personas import persona


def rule(**changes):
    return {
        "id": "r",
        "status": "active",
        "amount": 1000,
        "affordability_floor": 50000,
        "trigger": {"kind": "category", "value": "dining"},
        **changes,
    }


def txn(category="dining", amount=-1000):
    return Transaction("t", "P2", "2026-10-22", amount, "x", "Merchant", category)


def test_rule_branches():
    p = persona("P2")
    assert execute(rule(), p, txn())["outcome"] == "executed"
    assert execute(rule(status="paused"), p, txn()) is None
    assert execute(rule(), p, txn("other")) is None
    p.cash_balance = 50000
    assert execute(rule(), p, txn())["outcome"] == "skipped_unaffordable"
    assert matches(rule(trigger={"kind": "merchant", "value": "Merchant"}), txn())
    assert matches(rule(trigger={"kind": "schedule", "value": "22"}), txn(amount=10000))
    assert not matches(rule(trigger={"kind": "schedule", "value": "22"}), txn())
    with pytest.raises(ValueError):
        execute(rule(amount=-1), p, txn())


@given(cash=st.integers(0, 1000000), amount=st.integers(1, 100000))
def test_rule_floor_property(cash, amount):
    p = persona("P2")
    p.cash_balance = cash
    result = execute(rule(amount=amount), p, txn())
    if result["outcome"] == "executed":
        assert result["projected_buffer_after"] >= p.min_cash_buffer
    else:
        assert result["buffer_after"] == cash


ACCEPTED = [
    f"{intro} {tail}"
    for intro in [
        "We can take a small step.",
        "Your plan can change.",
        "You are in control.",
        "Let’s look at the options.",
        "Your buffer comes first.",
        "Take the time you need.",
    ]
    for tail in [
        "A little room can help.",
        "The choice is yours.",
        "We can pause here.",
        "These are simulated figures.",
        "Keep what works for you.",
    ]
]
REJECTED = [
    f"{word} {tail}"
    for word in [
        "You overspent.",
        "You failed.",
        "That is irresponsible.",
        "You are careless.",
        "You should feel shame.",
        "This is urgent.",
    ]
    for tail in [
        "Change now.",
        "Fix your spending.",
        "Do better.",
        "Act immediately.",
        "Stop this.",
    ]
]


@pytest.mark.parametrize("text", ACCEPTED)
def test_accepted_tone(text):
    assert tone_ok(text)


@pytest.mark.parametrize("text", REJECTED)
def test_rejected_tone(text):
    assert not tone_ok(text)


def test_numeric_and_guard():
    assert faithful("Try $12.50.", {"amount": 1250})
    assert not faithful("You will save 99.", {"amount": 1250})
    p = persona("P2")
    p.declined_transaction = True
    assert guard_reason(p, {"buffer_after": 999999})
    p.declined_transaction = False
    p.cash_balance = 0
    assert guard_reason(p, {"buffer_after": 999999})
    p.cash_balance = 999999
    assert guard_reason(p, {"buffer_after": 0})
    assert guard_reason(p, {"buffer_after": 999999}) is None
    assert guard_until(datetime(2026, 10, 22, tzinfo=timezone.utc)).startswith("2026-10-24")


def test_same_day_pending_costs_are_reserved():
    p = persona("P2")
    p.cash_balance = 80000
    assert execute(rule(), p, txn(), reserved_today=30000)["outcome"] == "skipped_unaffordable"
