#!/usr/bin/env python3
"""Vela AI Evaluation Harness runner.

Supports:
- --validate-only: Validates scenario JSON files against schema and checks ID/family uniqueness (uses Pydantic, zero extra deps).
- --offline: Runs evaluation against the application chat path with external model calls disabled.
- --split: Filter scenarios by 'dev', 'heldout', or 'all' (default).
- Saves full evaluation report to evals/reports/latest.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Ensure repository root and services/api are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "services" / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from evals.graders.checks import grade_scenario
from vela.ai import Quotas, money
from vela.chat import ChatMessage, ChatRequest, chat
from vela.domain import Obligation, Snapshot, State, Transaction, capacity


# Pydantic schema model strictly matching evals/schema.json (zero extra dependencies)
class ObligationOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    amount_cents: int = Field(gt=0)
    due: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    kind: Literal["living", "rent", "debt", "other"] = "other"


class TransactionOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    description: str = Field(min_length=1)
    amount_cents: int
    category: str = "other"


class StateOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    liquid_cash_cents: int | None = Field(..., ge=0)
    safe_buffer_cents: int | None = Field(..., ge=0)
    saved_cents: int = Field(default=0, ge=0)
    goal_target_cents: int = Field(default=50000, gt=0)
    goal_name: str = Field(default="Emergency reserve", min_length=1)
    obligations: list[ObligationOverride] = Field(...)
    transactions: list[TransactionOverride] = Field(...)


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    must_contain_any: list[str] = Field(...)
    must_not_contain: list[str] = Field(...)
    refuse_financial_advice: bool = Field(...)
    allowed_numbers_only: bool = Field(...)


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    split: Literal["dev", "heldout"]
    category: Literal[
        "numeric_grounding",
        "scope_refusal",
        "prompt_injection",
        "missing_data",
        "calm_tone",
        "no_unconfirmed_mutation",
    ]
    user_message: str = Field(min_length=1)
    state_overrides: StateOverrides
    expected: Expected


def load_schema(schema_path: Path) -> dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_json_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the Draft-07 keywords used by the checked-in scenario schema."""
    errors: list[str] = []
    declared_type = schema.get("type")
    if declared_type is not None:
        types = declared_type if isinstance(declared_type, list) else [declared_type]
        matches = {
            "object": isinstance(instance, dict), "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "boolean": isinstance(instance, bool), "null": instance is None,
        }
        if not any(matches.get(value, False) for value in types):
            return [f"{path}: expected type {types}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}, got {instance!r}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")
    if isinstance(instance, int) and not isinstance(instance, bool) and "minimum" in schema and instance < schema["minimum"]:
        errors.append(f"{path}: must be >= {schema['minimum']}")
    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            errors.extend(_validate_json_schema(value, schema["items"], f"{path}[{index}]"))
    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in instance:
                errors.append(f"{path}: missing required property {required!r}")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, value in instance.items():
            if key in properties:
                errors.extend(_validate_json_schema(value, properties[key], f"{path}.{key}"))
    return errors


def find_scenario_files(scenarios_dir: Path, split: str = "all") -> list[Path]:
    scenario_files: list[Path] = []
    splits = ["dev", "heldout"] if split == "all" else [split]

    for s in splits:
        split_dir = scenarios_dir / s
        if split_dir.is_dir():
            for p in sorted(split_dir.glob("*.json")):
                scenario_files.append(p)

    return scenario_files


def _display_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        try:
            return str(path.relative_to(base_dir)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")


def validate_scenarios(
    scenarios_dir: Path,
    schema_path: Path,
    split: str = "all",
) -> tuple[bool, list[dict[str, Any]], list[str]]:
    # Verify schema JSON loads cleanly
    try:
        raw_schema = load_schema(schema_path)
        if not isinstance(raw_schema, dict) or "required" not in raw_schema:
            return False, [], [f"Invalid schema format in {schema_path}"]
    except Exception as exc:
        return False, [], [f"Failed to load schema from {schema_path}: {exc}"]

    files = find_scenario_files(scenarios_dir, split)

    seen_ids: dict[str, Path] = {}
    seen_families: dict[str, Path] = {}
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    if not files:
        errors.append(f"No scenarios found in {scenarios_dir} (split={split})")

    for path in files:
        rel_path = _display_path(path, scenarios_dir)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            err = f"Failed to parse JSON in {rel_path}: {exc}"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue

        schema_errors = _validate_json_schema(data, raw_schema)
        if schema_errors:
            err = f"Schema validation failed for {rel_path}: {'; '.join(schema_errors)}"
            errors.append(err)
            results.append({"path": rel_path, "passed": False, "error": err})
            continue

        # Pydantic additionally proves this scenario can be safely converted to State.
        try:
            ScenarioModel.model_validate(data)
            build_state_from_overrides(data["state_overrides"], date(2026, 3, 1))
        except Exception as exc:
            err = f"Schema validation failed for {rel_path}: {exc}"
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


def build_state_from_overrides(overrides: dict[str, Any], today: date) -> tuple[State, set[str | int]]:
    cash = overrides.get("liquid_cash_cents")
    safe_buffer = overrides.get("safe_buffer_cents")
    allowed_figures: set[str | int] = set()

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

    if cash is None:
        # Validate nested inputs above even when there is no balance snapshot.
        state = State(revision=0, snapshot=None, actions=[], transactions=[], debts=[])
        return state, set()

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

    # Populate allowed verified figures in integer cents
    cap = capacity(state)
    unpaid_total = sum(o.amount for o in snapshot.obligations)
    allowed_figures.update([
        cash,
        protected,
        saved,
        cap,
        unpaid_total,
        goal_target,
    ])

    return state, allowed_figures


async def call_app_chat(user_message: str, state: State, today: date, offline: bool = True) -> str:
    """Call the real application chat entrypoint (`chat`) with external API disabled when `offline=True`."""
    quotas_path = REPO_ROOT / ".local" / "evals_quotas.db"
    os.makedirs(quotas_path.parent, exist_ok=True)
    quotas = Quotas(quotas_path)

    req = ChatRequest(messages=[ChatMessage(role="user", content=user_message)])
    if not offline:
        res = await chat(req, state, today, quotas)
        return res["reply"]

    previous = os.environ.get("ENABLE_GEMINI")
    os.environ["ENABLE_GEMINI"] = "false"
    try:
        res = await chat(req, state, today, quotas)
        return res["reply"]
    finally:
        if previous is None:
            os.environ.pop("ENABLE_GEMINI", None)
        else:
            os.environ["ENABLE_GEMINI"] = previous


def run_evals(
    scenarios_dir: Path,
    report_out: Path,
    split: str = "all",
    offline: bool = True,
    schema_path: Path = REPO_ROOT / "evals" / "schema.json",
) -> tuple[bool, dict[str, Any]]:
    today = date(2026, 3, 1)
    scenario_files = find_scenario_files(scenarios_dir, split)
    start_time = time.time()

    eval_results: list[dict[str, Any]] = []
    total = len(scenario_files)
    passed_count = 0

    valid, validation_results, validation_errors = validate_scenarios(scenarios_dir, schema_path, split)
    if not valid:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "offline" if offline else "live", "split": split,
            "total_scenarios": total, "passed": 0, "failed": total,
            "pass_rate": 0.0, "duration_seconds": round(time.time() - start_time, 3),
            "results": [], "validation_results": validation_results,
            "validation_errors": validation_errors,
        }
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return False, report

    for file_path in scenario_files:
        with open(file_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)

        reply = ""
        try:
            state, allowed_figures = build_state_from_overrides(scenario.get("state_overrides", {}), today)

            # Independent deep copy before application call
            state_before = state.model_copy(deep=True)

            # Call real application chat path (never passing gold standard expected answers)
            reply = asyncio.run(call_app_chat(scenario["user_message"], state, today, offline=offline))

            # Independent deep copy after application call
            state_after = state.model_copy(deep=True)

            # Grade reply with invariant graders
            grading = grade_scenario(
                scenario=scenario,
                reply=reply,
                state_before=state_before,
                state_after=state_after,
                allowed_figures=allowed_figures,
            )

        except Exception as exc:
            # A failed application invocation must replace any old success report
            # and must not prevent remaining independent scenarios from running.
            grading = {
                "scenario_id": scenario["id"], "family": scenario["family"],
                "split": scenario["split"], "category": scenario["category"],
                "passed": False, "checks": [],
                "failure_reasons": [f"Scenario execution failed: {type(exc).__name__}: {exc}"],
            }

        grading["file"] = _display_path(file_path, scenarios_dir)
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
    parser.add_argument("--validate-only", action="store_true", help="Only validate scenario JSON schema and uniqueness")
    parser.add_argument("--split", choices=["all", "dev", "heldout"], default="all", help="Scenario split to run")
    parser.add_argument("--scenarios-dir", type=Path, default=REPO_ROOT / "evals" / "scenarios")
    parser.add_argument("--schema-path", type=Path, default=REPO_ROOT / "evals" / "schema.json")
    parser.add_argument("--report-out", type=Path, default=REPO_ROOT / "evals" / "reports" / "latest.json")

    args = parser.parse_args()

    print("=" * 60)
    print("Vela AI Evaluation Harness")
    print("=" * 60)

    if args.validate_only:
        print(f"Validating scenarios in: {args.scenarios_dir} (split={args.split})")
        valid, results, errors = validate_scenarios(args.scenarios_dir, args.schema_path, args.split)

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

    print(f"Running evals against application chat (offline=True, split={args.split})...")
    all_passed, report = run_evals(
        scenarios_dir=args.scenarios_dir,
        report_out=args.report_out,
        split=args.split,
        offline=True,
        schema_path=args.schema_path,
    )

    print("-" * 60)
    for error in report.get("validation_errors", []):
        print(f"  [FAIL] {error}")
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
