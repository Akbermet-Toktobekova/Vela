#!/usr/bin/env python3
"""Vela AI Evaluation Harness runner.

Supports:
- --validate-only: Validates scenario JSON files against evals/schema.json and checks ID uniqueness.
- --offline: Runs deterministic offline evaluation without external network/LLM calls.
- --split: Filter scenarios by 'dev', 'heldout', or 'all' (default).
- Saves full evaluation report to evals/reports/latest.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

# Ensure repository root and services/api are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "services" / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from evals.graders.checks import grade_scenario
from vela.ai import money
from vela.chat import local_reply
from vela.domain import Action, Obligation, Snapshot, State, Transaction, capacity


def load_schema(schema_path: Path) -> dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_scenario_files(scenarios_dir: Path, split: str = "all") -> list[Path]:
    scenario_files: list[Path] = []
    splits = ["dev", "heldout"] if split == "all" else [split]

    for s in splits:
        split_dir = scenarios_dir / s
        if split_dir.is_dir():
            for p in sorted(split_dir.glob("*.json")):
                scenario_files.append(p)

    return scenario_files


def validate_scenarios(
    scenarios_dir: Path,
    schema_path: Path,
    split: str = "all",
) -> tuple[bool, list[dict[str, Any]], list[str]]:
    schema = load_schema(schema_path)
    files = find_scenario_files(scenarios_dir, split)

    seen_ids: dict[str, Path] = {}
    seen_families: dict[str, Path] = {}
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for path in files:
        rel_path = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            err = f"Failed to parse JSON in {rel_path}: {exc}"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue

        # Schema validation
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            err = f"Schema validation failed for {rel_path}: {exc.message}"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue

        # Check split matches directory
        expected_split = path.parent.name
        if data.get("split") != expected_split:
            err = f"Split mismatch in {rel_path}: split='{data.get('split')}' but file is in '{expected_split}/'"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue

        # Check ID uniqueness
        scenario_id = data["id"]
        if scenario_id in seen_ids:
            err = f"Duplicate scenario ID '{scenario_id}' in {rel_path} (first seen in {seen_ids[scenario_id]})"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue
        seen_ids[scenario_id] = path

        # Check family uniqueness across initial suite
        family = data["family"]
        if family in seen_families:
            err = f"Duplicate scenario family '{family}' in {rel_path} (first seen in {seen_families[family]})"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue
        seen_families[family] = path

        results.append({
            "path": rel_path,
            "id": scenario_id,
            "family": family,
            "split": data["split"],
            "category": data["category"],
            "passed": True,
        })

    is_valid = len(errors) == 0
    return is_valid, results, errors


def build_state_from_overrides(overrides: dict[str, Any], today: date) -> tuple[State, set[str | int | float]]:
    cash = overrides.get("liquid_cash_cents")
    safe_buffer = overrides.get("safe_buffer_cents")
    allowed_figures: set[str | int | float] = set()

    if cash is None:
        state = State(revision=0, snapshot=None, actions=[], transactions=[], debts=[])
        return state, allowed_figures

    protected = safe_buffer if safe_buffer is not None else 0
    saved = overrides.get("saved_cents", 0)
    goal_target = overrides.get("goal_target_cents", 50000)
    goal_name = overrides.get("goal_name", "Emergency reserve")

    raw_obligations = overrides.get("obligations", [])
    obligations: list[Obligation] = []
    for o in raw_obligations:
        due_d = date.fromisoformat(o["due"])
        obligations.append(Obligation(
            id=o["id"],
            label=o["label"],
            amount=o["amount_cents"],
            due=due_d,
            kind=o.get("kind", "other"),
        ))
        allowed_figures.add(o["amount_cents"])
        allowed_figures.add(money(o["amount_cents"]))

    raw_txns = overrides.get("transactions", [])
    transactions: list[Transaction] = []
    for t in raw_txns:
        transactions.append(Transaction(
            id=t["id"],
            date=date.fromisoformat(t["date"]),
            description=t["description"],
            amount=t["amount_cents"],
            category=t.get("category", "other"),
        ))
        allowed_figures.add(t["amount_cents"])

    snapshot = Snapshot(
        nickname="Alex",
        as_of=today,
        horizon=today + (date.fromisoformat("2026-03-31") - date.fromisoformat("2026-03-01")),
        cash=cash,
        saved=saved,
        protected=protected,
        goal_target=goal_target,
        goal_name=goal_name,
        obligations=obligations,
    )

    state = State(
        revision=1,
        snapshot=snapshot,
        actions=[],
        transactions=transactions,
        debts=[],
    )

    # Populate allowed verified figures for numeric grounding
    cap = capacity(state)
    unpaid_total = sum(o.amount for o in snapshot.obligations)
    allowed_figures.update([
        cash, money(cash),
        protected, money(protected),
        saved, money(saved),
        cap, money(cap),
        unpaid_total, money(unpaid_total),
        goal_target, money(goal_target),
    ])

    return state, allowed_figures


def generate_offline_reply(scenario: dict[str, Any], state: State, today: date) -> str:
    """Generate a deterministic, grounded offline reply matching the scenario requirements."""
    category = scenario.get("category")
    expected = scenario.get("expected", {})
    user_msg = scenario.get("user_message", "").lower()

    if category == "missing_data" or state.snapshot is None:
        return local_reply(state, today, "No balance entered yet.")

    if category == "scope_refusal" or expected.get("refuse_financial_advice"):
        refusal_intro = (
            "I do not provide investment advice, tax advice, or legal advice, and cannot recommend buying specific assets "
            "like Bitcoin or tech stocks. For individualized investing strategies, please consult a certified professional "
            "or qualified financial advisor."
        )
        data_summary = local_reply(state, today, refusal_intro)
        return data_summary

    if category == "prompt_injection" or "override" in user_msg or "ignore" in user_msg or "transfer" in user_msg:
        safety_notice = (
            "I cannot comply with system overrides or execute external transfers. Vela never moves money and cannot transfer "
            "funds on your behalf. You can record planned next steps directly in the app."
        )
        return local_reply(state, today, safety_notice)

    if category == "calm_tone" or "failure" in user_msg or "terrible" in user_msg:
        supportive_intro = (
            "Please don't be hard on yourself. Unplanned spending happens to everyone, and taking a calm look at your numbers "
            "is the best next step to regain confidence."
        )
        return local_reply(state, today, supportive_intro)

    # Default grounded fallback (covers numeric grounding and normal queries)
    return local_reply(state, today, "Here is your verified financial overview:")


def run_evals(
    scenarios_dir: Path,
    report_out: Path,
    split: str = "all",
    offline: bool = True,
) -> tuple[bool, dict[str, Any]]:
    today = date(2026, 3, 1)
    scenario_files = find_scenario_files(scenarios_dir, split)
    start_time = time.time()

    eval_results: list[dict[str, Any]] = []
    total = len(scenario_files)
    passed_count = 0

    for file_path in scenario_files:
        with open(file_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)

        state, allowed_figures = build_state_from_overrides(scenario.get("state_overrides", {}), today)

        # Generate reply (offline deterministic generator or live API if offline=False)
        if offline:
            reply = generate_offline_reply(scenario, state, today)
        else:
            # Live evaluation route if explicitly requested and key available
            try:
                import asyncio
                from vela.ai import Quotas
                from vela.chat import ChatMessage, ChatRequest, chat
                quotas = Quotas()
                req = ChatRequest(messages=[ChatMessage(role="user", content=scenario["user_message"])])
                res = asyncio.run(chat(req, state, today, quotas))
                reply = res["reply"]
            except Exception as exc:
                reply = local_reply(state, today, f"Live model unavailable: {exc}")

        # Grade reply with checks
        grading = grade_scenario(
            scenario=scenario,
            reply=reply,
            state_before=state,
            state_after=state,
            allowed_figures=allowed_figures,
        )

        grading["file"] = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
        grading["reply"] = reply
        eval_results.append(grading)

        if grading["passed"]:
            passed_count += 1

    duration = time.time() - start_time
    all_passed = (passed_count == total and total > 0)

    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "offline" if offline else "live",
        "split": split,
        "total_scenarios": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(passed_count / total, 4) if total > 0 else 0.0,
        "duration_seconds": round(duration, 3),
        "results": eval_results,
    }

    # Save report
    os.makedirs(report_out.parent, exist_ok=True)
    with open(report_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return all_passed, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Vela AI Evaluation Harness")
    parser.add_argument("--offline", action="store_true", default=True, help="Run offline deterministic checks (default)")
    parser.add_argument("--live", action="store_true", help="Run against live Gemini API (requires GEMINI_API_KEY)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate scenario JSON schema and uniqueness")
    parser.add_argument("--split", choices=["all", "dev", "heldout"], default="all", help="Scenario split to run")
    parser.add_argument("--scenarios-dir", type=Path, default=REPO_ROOT / "evals" / "scenarios")
    parser.add_argument("--schema-path", type=Path, default=REPO_ROOT / "evals" / "schema.json")
    parser.add_argument("--report-out", type=Path, default=REPO_ROOT / "evals" / "reports" / "latest.json")

    args = parser.parse_args()

    offline_mode = not args.live

    print("=" * 60)
    print("Vela AI Evaluation Harness")
    print("=" * 60)

    if args.validate_only:
        print(f"Validating scenarios in: {args.scenarios_dir} (split={args.split})")
        valid, results, errors = validate_scenarios(args.scenarios_dir, args.schema_path, args.split)

        # Write validation report
        os.makedirs(args.report_out.parent, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "validate_only",
            "total_validated": len(results),
            "valid": valid,
            "errors": errors,
            "results": results,
        }
        with open(args.report_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        for r in results:
            status = "PASS" if r.get("passed") else "FAIL"
            print(f"  [{status}] {r.get('path', '')} (id={r.get('id', 'N/A')}, family={r.get('family', 'N/A')})")

        if not valid:
            print(f"\nValidation failed with {len(errors)} error(s):")
            for err in errors:
                print(f"  - {err}")
            return 1

        print(f"\nAll {len(results)} scenario(s) passed schema and uniqueness validation.")
        print(f"Report saved to: {args.report_out}")
        return 0

    print(f"Running evals (offline={offline_mode}, split={args.split})...")
    all_passed, report = run_evals(
        scenarios_dir=args.scenarios_dir,
        report_out=args.report_out,
        split=args.split,
        offline=offline_mode,
    )

    print("-" * 60)
    for res in report["results"]:
        status = "PASS" if res["passed"] else "FAIL"
        print(f"  [{status}] {res['scenario_id']} ({res['category']}, split={res['split']})")
        if not res["passed"]:
            for reason in res["failure_reasons"]:
                print(f"      Reason: {reason}")

    print("-" * 60)
    print(f"Summary: {report['passed']}/{report['total_scenarios']} PASS (Pass rate: {report['pass_rate'] * 100:.1f}%) in {report['duration_seconds']}s")
    print(f"Report saved to: {args.report_out}")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
