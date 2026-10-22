"""Read-only tool routing; scenario numbers always originate in domain functions."""

import json
import re
from decimal import Decimal
from typing import Any

from finagent.domain.math import amortize, cash_projection, contribution_months
from finagent.domain.models import Money, UserProfile
from finagent.llm.client import LLMClient
from finagent.safety.checks import faithful, tone_ok

DISCLAIMER = "Educational guidance only. All transfers are simulated."


def respond(
    message: str,
    profile: UserProfile,
    recommendation: Any,
    events: list[Any],
    now: Any,
    client: LLMClient,
) -> dict[str, Any]:
    if re.search(
        r"\b(stock|stocks|securit\w*|bitcoin|crypto|tax|legal|lawsuit|invest\w*)\b", message, re.I
    ):
        return {
            "text": "I can help explore your budget, debt, and savings. For specific securities, tax, or legal questions, speak with a qualified professional. "
            + DISCLAIMER,
            "tools": [],
            "facts": {},
            "fallback": False,
        }
    text = message.lower()
    number = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    tools: list[str] = []
    facts: dict[str, Any] = {}
    if "income" in text and number:
        pct = Decimal(number.group())
        if "decrease" in text or "less" in text or "down" in text:
            pct = -abs(pct)
        if pct < -100 or pct > 500:
            raise ValueError("Choose an income change between -100% and 500%")
        changed = UserProfile.from_dict(profile.to_dict())
        changed.monthly_income = Money(profile.monthly_income).scale(1 + pct / 100).cents
        facts = {
            "current_income": profile.monthly_income,
            "scenario_income": changed.monthly_income,
            "monthly_available_after_commitments": changed.monthly_income
            - sum(c.amount for c in changed.fixed_costs)
            - sum(d.min_payment for d in changed.debts),
            "current_cash_projection": cash_projection(profile, now),
        }
        tools = ["simulate_income_change"]
    elif number and any(word in text for word in ("pay", "debt", "save", "saving", "more")):
        extra = Money(100).scale(Decimal(number.group())).cents
        if extra < 0 or extra > 100000000:
            raise ValueError("Choose a nonnegative extra contribution")
        if "sav" in text or not profile.debts:
            target = sum(c.amount for c in profile.fixed_costs) * profile.emergency_months
            remaining = max(
                0, target - sum(s.balance for s in profile.savings if s.kind == "emergency")
            )
            base = Money(profile.monthly_income).scale(Decimal(profile.auto_save_pct) / 100).cents
            facts = {
                "extra": extra,
                "target": target,
                "months": contribution_months(remaining, base + extra),
                "projection": cash_projection(profile, now, base + extra),
            }
        else:
            debt = max(profile.debts, key=lambda d: Decimal(d.annual_rate))
            base, scenario = amortize(debt), amortize(debt, extra)
            facts = {
                "extra": extra,
                "months": scenario.months,
                "interest_saved": max(0, base.interest - scenario.interest),
                "months_saved": max(0, base.months - scenario.months),
                "payable": scenario.payable,
                "projection": cash_projection(profile, now, extra),
            }
        tools = ["simulate_extra_payment"]
    elif "history" in text:
        tools, facts = ["get_history"], {"events": events[:10]}
    elif "why" in text or "recommend" in text:
        tools, facts = (
            ["get_recommendation_facts"],
            recommendation["reason_facts"] if recommendation else {},
        )
    else:
        tools = ["get_profile"]
        facts = {
            "monthly_income": profile.monthly_income,
            "cash_balance": profile.cash_balance,
            "minimum_buffer": profile.min_cash_buffer,
            "priority": profile.priority,
        }
    template = "Here are the figures from your current plan. These are a scenario, and your plan has not changed."
    try:
        answer = client.complete(
            json.dumps(
                {"task": "explain", "message": message, "tools": tools, "facts": facts},
                sort_keys=True,
            )
        )
        fallback = not faithful(answer, facts) or not tone_ok(answer)
    except RuntimeError:
        answer, fallback = template, True
    affordability_note = ""
    if (
        isinstance(facts.get("projection"), dict)
        and facts["projection"]["buffer_after"] < profile.min_cash_buffer
    ):
        affordability_note = (
            " This scenario would use your protected cash buffer. Consider a smaller amount."
        )
    return {
        "text": (template if fallback else answer) + affordability_note + " " + DISCLAIMER,
        "tools": tools,
        "facts": facts,
        "fallback": fallback,
    }
