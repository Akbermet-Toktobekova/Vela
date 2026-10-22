"""Reproducible offline comparisons; latency is reported separately from stable results."""

import json
import statistics
import time
from pathlib import Path
from typing import Any

from finagent.agents.coordinator import LLMAssistedCoordinator, RuleBasedCoordinator
from finagent.agents.specialists import candidates
from finagent.domain.math import cash_projection
from finagent.domain.models import Debt
from finagent.llm.client import get_client
from finagent.safety.checks import faithful, guard_reason
from finagent.sources.personas import ANCHOR, generate, persona

EXPECTED = {
    "P1": "weekend_habit",
    "P2": "extra_debt",
    "P3": "emergency_save",
    "P4": "subscription_review",
}


def evaluate(root: Path = Path("eval/results")) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    results, latencies = [], []
    coordinators = {
        "rule": RuleBasedCoordinator(),
        "llm_assisted": LLMAssistedCoordinator(get_client()),
    }
    for key in EXPECTED:
        for variant in ("baseline", "income_down", "new_debt", "balance_shock"):
            p = persona(key)
            if variant == "income_down":
                p.monthly_income = p.monthly_income * 80 // 100
            if variant == "new_debt":
                p.debts.append(Debt("New debt", 100000, "25", 5000))
            if variant == "balance_shock":
                p.cash_balance = 0
            options = candidates(p, generate(key), ANCHOR)
            suppressed = guard_reason(p, cash_projection(p, ANCHOR)) is not None
            expected = None if suppressed else EXPECTED[key]
            for mode, coordinator in coordinators.items():
                start = time.perf_counter()
                recommendation = None if suppressed else coordinator.choose(p, options)
                elapsed = (time.perf_counter() - start) * 1000
                repeat = None if suppressed else coordinator.choose(p, options)
                chosen = recommendation["chosen"] if recommendation else None
                top3 = (
                    [row["candidate"]["type"] for row in recommendation["considered"][:3]]
                    if recommendation
                    else []
                )
                # LLM ranking remains the rule policy; only its selected action changes.
                top1 = chosen["type"] if chosen else None
                results.append(
                    {
                        "persona": key,
                        "variant": variant,
                        "mode": mode,
                        "expected": expected,
                        "selected": top1,
                        "top1_agreement": top1 == expected,
                        "top3_agreement": expected in top3 if expected else chosen is None,
                        "affordability_violation": bool(
                            chosen
                            and (
                                not chosen["affordable"]
                                or chosen["impact"]["buffer_after"] < p.min_cash_buffer
                            )
                        ),
                        "explanation_faithful": faithful(
                            recommendation["explanation_text"], recommendation["reason_facts"]
                        )
                        if recommendation
                        else True,
                        "guard_compliant": not suppressed or recommendation is None,
                        "deterministic": recommendation == repeat,
                        "candidate_count": len(options),
                    }
                )
                latencies.append(
                    {
                        "persona": key,
                        "variant": variant,
                        "mode": mode,
                        "latency_ms": round(elapsed, 3),
                    }
                )
    metrics = {
        mode: {
            "scenarios": len(rows),
            "top1_agreement": sum(r["top1_agreement"] for r in rows) / len(rows),
            "top3_agreement": sum(r["top3_agreement"] for r in rows) / len(rows),
            "affordability_violations": sum(r["affordability_violation"] for r in rows),
            "explanation_faithfulness": sum(r["explanation_faithful"] for r in rows) / len(rows),
            "guard_compliance": sum(r["guard_compliant"] for r in rows) / len(rows),
            "determinism": all(r["deterministic"] for r in rows),
        }
        for mode in coordinators
        for rows in [[r for r in results if r["mode"] == mode]]
    }
    output = {
        "as_of": ANCHOR.isoformat(),
        "seed": 42,
        "provider": __import__("os").getenv("LLM_PROVIDER", "fake"),
        "metrics": metrics,
        "scenarios": results,
    }
    (root / "results.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    (root / "latency.json").write_text(json.dumps(latencies, indent=2) + "\n")
    lines = [
        "# FinAgent evaluation",
        "",
        f"Provider: `{output['provider']}`. Seed: 42. Financial date: {ANCHOR}.",
        "",
        "| Mode | Top-1 | Top-3 | Unsafe | Faithful | Guard | Deterministic |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for mode, m in metrics.items():
        lines.append(
            f"| {mode} | {m['top1_agreement']:.0%} | {m['top3_agreement']:.0%} | {m['affordability_violations']} | {m['explanation_faithfulness']:.0%} | {m['guard_compliance']:.0%} | {m['determinism']} |"
        )
    lines.extend(
        [
            "",
            "## Method and limits",
            "",
            "Each coordinator runs on four personas and three perturbations per persona. Expected action labels remain unchanged for income/debt perturbations; balance shocks expect suppression. This tests policy stability, not independent expert optimality. Top-3 for the LLM uses the shared rule ranking, because the model returns one id only.",
            "",
            "Guard compliance here measures the guard-before-selection wrapper. API integration tests separately exercise persistent 48-hour blackouts and daily frequency. Numeric faithfulness is an allow-list check, not semantic proof.",
            "",
            "Fake-provider agreement is a wiring test and is **not evidence of live LLM quality**. Select `LLM_PROVIDER=anthropic` with your own credential for cached provider evaluation. Cold/cache-hit latency differs. Stable results exclude measured timing; latency observations are in `latency.json`.",
            "",
            "| Mode | Median observed latency (ms) |",
            "|---|---:|",
        ]
    )
    for mode in coordinators:
        lines.append(
            f"| {mode} | {statistics.median(r['latency_ms'] for r in latencies if r['mode'] == mode):.3f} |"
        )
    (root / "report.md").write_text("\n".join(lines) + "\n")
    return output
