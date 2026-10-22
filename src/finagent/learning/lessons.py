"""Deterministic relevant-first lesson selection, persisted by the service."""

from pathlib import Path
from typing import Any

import yaml

from finagent.domain.models import UserProfile


def lessons() -> list[dict[str, Any]]:
    return [
        yaml.safe_load(path.read_text()) for path in sorted(Path("data/lessons").glob("*.yaml"))
    ]


def select_lesson(
    profile: UserProfile, seen: list[str], context: dict[str, bool] | None = None
) -> dict[str, Any] | None:
    pool = lessons()
    remaining = [lesson for lesson in pool if lesson["id"] not in seen] or pool
    context = context or {
        "debt_present": bool(profile.debts),
        "no_emergency": not any(a.balance for a in profile.savings if a.kind == "emergency"),
    }
    return (
        min(
            remaining,
            key=lambda x: (
                x["topic"] != profile.priority,
                -sum(context.get(condition, False) for condition in x["trigger_conditions"]),
                x["id"],
            ),
        )
        if remaining
        else None
    )
