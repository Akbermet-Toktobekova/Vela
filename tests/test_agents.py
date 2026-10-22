import json
from dataclasses import replace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from finagent.agents.coordinator import LLMAssistedCoordinator, RuleBasedCoordinator
from finagent.agents.specialists import BudgetAgent, DebtAgent, SavingsAgent, candidates
from finagent.analysis.patterns import analyse
from finagent.domain.models import Debt, SavingsAccount
from finagent.llm.client import FakeLLMClient
from finagent.safety.checks import faithful
from finagent.sources.personas import ANCHOR, generate, persona, seed_files


@pytest.mark.parametrize(
    "key,expected",
    [
        ("P1", "weekend_habit"),
        ("P2", "extra_debt"),
        ("P3", "emergency_save"),
        ("P4", "subscription_review"),
    ],
)
def test_golden(key, expected):
    p = persona(key)
    options = candidates(p, generate(key), ANCHOR)
    result = RuleBasedCoordinator().choose(p, options)
    assert result["chosen"]["type"] == expected
    assert result == RuleBasedCoordinator().choose(p, options)
    assert faithful(result["explanation_text"], result["reason_facts"])
    assert LLMAssistedCoordinator(FakeLLMClient()).choose(p, options)["chosen"]["type"] == expected


@given(cash=st.integers(0, 1000000), income=st.integers(0, 1000000))
def test_savings_never_breach_floor(cash, income):
    p = persona("P3")
    p.cash_balance = cash
    p.monthly_income = income
    for candidate in SavingsAgent().analyse(p, [], ANCHOR):
        assert candidate.impact["buffer_after"] >= p.min_cash_buffer


@given(extra=st.integers(0, 100000))
def test_budget_reversible_and_stable(extra):
    p = persona("P1")
    p.cash_balance += extra
    options = BudgetAgent().analyse(p, generate("P1"), ANCHOR)
    assert all(c.reversible for c in options)
    assert options == BudgetAgent().analyse(p, generate("P1"), ANCHOR)


def test_filters_and_fallback():
    p = persona("P2")
    options = candidates(p, generate("P2"), ANCHOR)
    unsafe = [replace(c, affordable=False) for c in options]
    assert RuleBasedCoordinator().choose(p, unsafe) is None
    assert LLMAssistedCoordinator(FakeLLMClient()).choose(p, unsafe) is None

    class Bad:
        def complete(self, prompt):
            return json.dumps({"id": "invalid", "justification": "99999 guaranteed"})

    assert (
        LLMAssistedCoordinator(Bad()).choose(p, options)["chosen"]
        == RuleBasedCoordinator().choose(p, options)["chosen"]
    )

    class Broken:
        def complete(self, prompt):
            raise RuntimeError("offline")

    assert LLMAssistedCoordinator(Broken()).choose(p, options)["mode"] == "rule_fallback"


def test_empty_and_completed_agents():
    p = persona("P3")
    p.savings = [SavingsAccount("Safety net", 9999999)]
    assert SavingsAgent().analyse(p, [], ANCHOR) == []
    assert DebtAgent().analyse(p, [], ANCHOR) == []
    p.debts = [Debt("x", 100000, "99", 1)]
    assert DebtAgent().analyse(p, [], ANCHOR) == []
    assert BudgetAgent().analyse(p, [], ANCHOR) == []


def test_recurring_precision_recall_and_trends():
    for key in ["P1", "P2", "P3", "P4"]:
        p = persona(key)
        result = analyse(p, generate(key), ANCHOR)
        expected = {c.name for c in p.fixed_costs} | {"Spotify"}
        if key == "P4":
            expected |= {"Netflix", "Cloud", "Fitness", "News"}
        actual = {r["merchant"] for r in result["recurring"]}
        assert len(actual & expected) / len(actual) >= 0.9
        assert len(actual & expected) / len(expected) >= 0.9
        assert result["weekend"] > 0 and result["weekday"] > 0
        assert result["trends"]
    assert analyse(persona("P1"), [], ANCHOR)["categories"] == {}


def test_seed_byte_identical(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    seed_files(first)
    seed_files(second)
    for f in first.iterdir():
        assert f.read_bytes() == (second / f.name).read_bytes()


def test_explicit_savings_goal():
    p = persona("P3")
    p.savings.append(SavingsAccount("Course", 10000, "goal"))
    p.goal = {"linked_account": "Course", "target_amount": 100000, "target_date": "2027-01-01"}
    option = SavingsAgent().analyse(p, [], ANCHOR)[0]
    assert option.type == "goal_save"
    assert option.params["account"] == "Course"
    assert option.facts["target"] == 100000
    p.savings = []
    assert SavingsAgent().analyse(p, [], ANCHOR) == []
