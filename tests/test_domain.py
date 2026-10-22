from datetime import date
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from finagent.domain.math import (
    amortize,
    cash_projection,
    contribution_months,
    next_income,
    portfolio_payoff,
)
from finagent.domain.models import (
    Candidate,
    Debt,
    FixedCost,
    Money,
    SavingsAccount,
    Transaction,
    UserProfile,
)


@pytest.mark.parametrize(
    "constructor,args",
    [
        (Money, (1.2,)),
        (Money, (1, "usd")),
        (Debt, ("x", -1, "1", 1)),
        (Debt, ("x", 1, "101", 1)),
        (Debt, ("x", 1, "NaN", 1)),
        (Debt, ("x", 1, "1", -1)),
        (FixedCost, ("x", -1)),
        (FixedCost, ("x", 1, 31)),
        (SavingsAccount, ("x", -1)),
        (SavingsAccount, ("x", 1, "other")),
        (SavingsAccount, ("x", 1, "goal", -1)),
        (Transaction, ("x", "x", "invalid", 1, "x", "x", "x")),
        (Transaction, ("x", "x", "2026-01-01", 1.2, "x", "x", "x")),
    ],
)
def test_validators(constructor, args):
    with pytest.raises((ValueError, TypeError)):
        constructor(*args)


@pytest.mark.parametrize(
    "field,value",
    [
        ("monthly_income", -1),
        ("cash_balance", -1),
        ("min_cash_buffer", -1),
        ("priority", "invalid"),
        ("income_day", 29),
        ("auto_save_pct", 11),
        ("auto_save_pct", 1.5),
        ("emergency_months", 0),
        ("goal", {"target_amount": -1}),
        ("goal", {"target_date": "invalid"}),
    ],
)
def test_profile_validation(field, value):
    with pytest.raises(ValueError):
        UserProfile(**{field: value})


def test_money_rounding_and_currency():
    assert Money(101).scale(Decimal(".5")).cents == 51
    assert Money(-101).scale(Decimal(".5")).cents == -51
    assert Money(10).plus(Money(20)).cents == 30
    with pytest.raises(ValueError):
        Money(1, "USD").plus(Money(1, "EUR"))


@given(balance=st.integers(100, 1000000), extra=st.integers(0, 100000), rate=st.integers(0, 40))
def test_extra_never_increases_interest(balance, extra, rate):
    debt = Debt("Card", balance, str(rate), max(100, balance // 10))
    base = amortize(debt)
    boosted = amortize(debt, extra)
    assert boosted.payable and base.payable
    assert boosted.interest <= base.interest
    assert boosted.months <= base.months


def test_exact_amortization():
    assert amortize(Debt("Zero", 10000, "0", 1000)).months == 10
    result = amortize(Debt("APR", 10000, "12", 5100))
    assert (result.months, result.interest) == (2, 150)
    assert not amortize(Debt("Stuck", 10000, "100", 1)).payable
    assert amortize(Debt("Paid", 0, "12", 0)).months == 0
    assert contribution_months(101, 50) == 3
    assert contribution_months(101, 0) == 0


def test_portfolio():
    debts = [Debt("A", 10000, "20", 1000), Debt("B", 3000, "5", 500)]
    assert portfolio_payoff(debts, 1000, "avalanche").payable
    assert portfolio_payoff(debts, 1000, "snowball").payable
    assert (
        portfolio_payoff(debts, 1000, "avalanche").interest
        <= portfolio_payoff(debts, 0, "avalanche").interest
    )
    assert not portfolio_payoff([Debt("x", 10000, "99", 1)], 0, "snowball").payable
    with pytest.raises(ValueError):
        portfolio_payoff(debts, 1, "invalid")


def test_projection_crosses_year_and_preserves_floor():
    p = UserProfile(
        cash_balance=10000,
        min_cash_buffer=1000,
        income_day=5,
        fixed_costs=[FixedCost("Rent", 5000, 1)],
    )
    assert next_income(p, date(2026, 12, 30)) == date(2027, 1, 5)
    assert next_income(p, date(2026, 12, 1)) == date(2026, 12, 5)
    assert cash_projection(p, date(2026, 12, 30))["buffer_after"] == 5000
    assert cash_projection(p, date(2026, 12, 30), 1000)["buffer_after"] == 4000
    with pytest.raises(ValueError):
        cash_projection(p, date(2026, 12, 30), -1)


def test_round_trip_and_other_validation():
    p = UserProfile(
        savings=[SavingsAccount("Goal", 10, "goal", 100, "2027-01-01")],
        debts=[Debt("D", 1, "0", 1)],
        fixed_costs=[FixedCost("C", 1)],
    )
    assert UserProfile.from_dict(p.to_dict()) == p
    with pytest.raises(ValueError):
        Candidate("x", "budget", "x", "x", {}, {}, True, {}, effort=4)


def test_goal_projection_deadline_and_zero_contribution():
    from finagent.domain.math import goal_projection

    p = UserProfile(
        monthly_income=100000,
        auto_save_pct=5,
        savings=[SavingsAccount("Course", 10000, "goal")],
        goal={"linked_account": "Course", "target_amount": 20000, "target_date": "2027-01-01"},
    )
    result = goal_projection(p, date(2026, 10, 31))
    assert result["months"] == 2 and result["projected_date"] == "2026-12-31"
    assert result["on_schedule"] is True
    p.auto_save_pct = 0
    assert goal_projection(p, date(2026, 10, 31))["projected_date"] is None
    p.savings[0].balance = 20000
    assert goal_projection(p, date(2026, 10, 31))["projected_date"] == "2026-10-31"
