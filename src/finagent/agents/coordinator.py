"""Transparent selection with hard affordability filters before scoring."""

import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from finagent.domain.models import Candidate, UserProfile
from finagent.llm.client import LLMClient
from finagent.safety.checks import faithful, tone_ok


class RuleBasedCoordinator:
    """Weighted deterministic policy with a stable tie-break."""

    def __init__(self, config: str = "config/coordinator.yaml") -> None:
        """Load scoring weights from the explicit versioned configuration."""
        self.weights = yaml.safe_load(Path(config).read_text())

    def rank(self, profile: UserProfile, options: list[Candidate]) -> list[dict[str, Any]]:
        """Drop unsafe proposals and return scores in descending policy order."""
        safe = [
            c
            for c in options
            if c.affordable and c.impact["buffer_after"] >= profile.min_cash_buffer
        ]

        def impact(c: Candidate) -> int:
            return max(abs(c.impact["monthly_cash_effect"]), c.impact["interest_saved"] // 12)

        max_impact = max([impact(c) for c in safe] + [1])
        w = self.weights

        def score(c: Candidate) -> Decimal:
            return (
                Decimal(w["w_goal"]) * int(profile.priority == c.agent)
                + Decimal(w["w_impact"]) * Decimal(impact(c)) / max_impact
                + Decimal(w["w_urgency"]) * c.urgency
                + Decimal(w["w_ease"]) / c.effort
                + Decimal(w["w_stability"]) * c.stability
                - Decimal(w["w_risk"]) * c.risk
            )

        safe.sort(key=lambda c: (-score(c), -impact(c), c.effort, c.id))
        return [
            {"candidate": asdict(c), "score": str(score(c).quantize(Decimal("0.0001")))}
            for c in safe
        ]

    def choose(self, profile: UserProfile, options: list[Candidate]) -> dict[str, Any] | None:
        """Choose one candidate and narrate only deterministic facts."""
        ranked = self.rank(profile, options)
        if not ranked:
            return None
        chosen = ranked[0]["candidate"]
        return {
            "chosen": chosen,
            "considered": ranked,
            "reason_facts": chosen["facts"],
            "explanation_text": "This fits your chosen priority and keeps your planned cash above your buffer. The figures below come from your current plan.",
            "alternative": ranked[1]["candidate"]["title"]
            if len(ranked) > 1
            else "Keep your current plan",
            "alternative_reason": "It ranked lower under the goal, impact, urgency, effort, stability, and risk weights.",
            "do_nothing": "Your current contributions and payment schedule stay in place.",
            "mode": "rule",
        }


class LLMAssistedCoordinator(RuleBasedCoordinator):
    """Restrict model selection to the same affordable candidate set."""

    def __init__(self, client: LLMClient) -> None:
        """Inject a provider or deterministic fake."""
        super().__init__()
        self.client = client

    def choose(self, profile: UserProfile, options: list[Candidate]) -> dict[str, Any] | None:
        """Validate the selected id and numeric wording; fall back on any violation."""
        fallback = super().choose(profile, options)
        if not fallback:
            return None
        try:
            raw = self.client.complete(
                json.dumps(
                    {
                        "task": "select",
                        "priority": profile.priority,
                        "candidates": fallback["considered"],
                    },
                    sort_keys=True,
                )
            )
            result = json.loads(raw)
            selected = next(
                (r for r in fallback["considered"] if r["candidate"]["id"] == result.get("id")),
                None,
            )
            if (
                selected
                and isinstance(result.get("justification"), str)
                and faithful(result["justification"], selected["candidate"]["facts"])
                and tone_ok(result["justification"])
            ):
                chosen = selected["candidate"]
                fallback.update(
                    chosen=chosen,
                    reason_facts=chosen["facts"],
                    explanation_text=result["justification"],
                    mode="llm",
                )
                others = [r for r in fallback["considered"] if r is not selected]
                fallback["alternative"] = (
                    others[0]["candidate"]["title"] if others else "Keep your current plan"
                )
                fallback["alternative_reason"] = (
                    "The assistant preferred the chosen action for your priority; the policy scores remain visible."
                )
        except (ValueError, TypeError, RuntimeError, KeyError):
            fallback["mode"] = "rule_fallback"
        return fallback
