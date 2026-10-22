"""Application use-cases. All writes share an atomic SQLite unit of work."""

import os
import re
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlmodel import Session, delete

from finagent.agents.coordinator import LLMAssistedCoordinator, RuleBasedCoordinator
from finagent.agents.specialists import candidates
from finagent.analysis.patterns import analyse
from finagent.assistant.chat import respond
from finagent.domain.math import amortize, cash_projection, contribution_months, goal_projection
from finagent.domain.models import FixedCost, Money, Transaction, UserProfile
from finagent.learning.lessons import lessons, select_lesson
from finagent.llm.client import LLMClient, get_client
from finagent.persistence.store import HistoryEvent, Record, Store, get, history, log, put
from finagent.rules.engine import execute
from finagent.safety.checks import guard_reason, guard_until
from finagent.sources.csv_source import parse_csv
from finagent.sources.personas import ANCHOR, generate, persona


class Service:
    def __init__(self, store: Store, client: LLMClient | None = None) -> None:
        self.store, self.client = store, client or get_client()

    def clock(self, session: Session) -> datetime:
        return (
            datetime.fromisoformat(get(session, "clock"))
            if get(session, "clock")
            else datetime.now(timezone.utc)
        )

    def profile(self, session: Session) -> UserProfile:
        data = get(session, "profile")
        if not data:
            raise ValueError("Load a synthetic persona to start")
        return UserProfile.from_dict(data)

    def transactions(self, session: Session) -> list[Transaction]:
        return [Transaction(**t) for t in get(session, "transactions", [])]

    def reset_persona(self, key: str) -> dict[str, Any]:
        profile = persona(key)
        with self.store.transaction() as s:
            s.exec(delete(Record))
            s.exec(delete(HistoryEvent))
            put(s, "profile", profile.to_dict())
            put(s, "transactions", [asdict(t) for t in generate(key)])
            put(
                s,
                "clock",
                datetime.combine(ANCHOR, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            )
            log(
                s,
                self.clock(s).isoformat(),
                "plan_change",
                {"reason": "Synthetic persona loaded", "persona": key},
            )
            put(s, "goal_projection", goal_projection(profile, self.clock(s).date()))
            self.refresh(s)
        return profile.to_dict()

    def recompute(self, s: Session, reason: str) -> None:
        rec = get(s, "recommendation")
        if rec and rec["status"] == "pending":
            rec["status"] = "superseded"
            put(s, "recommendation", rec)
            put(s, "recommendation:" + rec["id"], rec)
        before = get(s, "goal_projection")
        after = goal_projection(self.profile(s), self.clock(s).date())
        put(s, "goal_projection", after)
        change = {"before": before, "after": after} if before != after else None
        if change:
            put(s, "timeline_change", change)
        log(
            s,
            self.clock(s).isoformat(),
            "plan_change",
            {"reason": reason, "recomputes": 1, "goal_timeline_change": change},
        )
        self.refresh(s)

    def guard(self, s: Session, profile: UserProfile) -> dict[str, Any] | None:
        now = self.clock(s)
        previous = get(s, "guard")
        if previous and datetime.fromisoformat(previous["until"]) > now:
            return previous
        reason = guard_reason(profile, cash_projection(profile, now.date()))
        if reason:
            state = {
                "reason": reason,
                "until": guard_until(now, int(os.getenv("GUARD_HOURS", "48"))),
            }
            put(s, "guard", state)
            log(s, now.isoformat(), "guard_suppression", state)
            return state
        put(s, "guard", None)
        return None

    def refresh(self, s: Session) -> dict[str, Any] | None:
        profile, now = self.profile(s), self.clock(s)
        if self.guard(s, profile):
            return None
        if get(s, "last_issued") == now.date().isoformat():
            return get(s, "recommendation")
        pending = get(s, "recommendation")
        if pending and pending["status"] == "pending":
            return pending
        cooldowns = get(s, "cooldowns", {})
        options = [
            c
            for c in candidates(profile, self.transactions(s), now.date())
            if cooldowns.get(c.type, "") <= now.isoformat()
        ]
        coordinator = (
            LLMAssistedCoordinator(self.client)
            if os.getenv("COORDINATOR") == "llm"
            else RuleBasedCoordinator()
        )
        result = coordinator.choose(profile, options)
        if not result:
            return None
        result.update(
            id=uuid4().hex,
            user_id=profile.id,
            created_at=now.isoformat(),
            status="pending",
            decision_at=None,
            adjustment_params=None,
            chosen_candidate_id=result["chosen"]["id"],
        )
        put(s, "recommendation", result)
        put(s, "recommendation:" + result["id"], result)
        put(s, "last_issued", now.date().isoformat())
        log(
            s,
            now.isoformat(),
            "recommendation",
            {"id": result["id"], "title": result["chosen"]["title"]},
        )
        return result

    def lesson(self, s: Session, profile: UserProfile) -> Any:
        today = self.clock(s).date().isoformat()
        current = get(s, "lesson")
        if current and current["day"] == today:
            return current
        patterns = analyse(profile, self.transactions(s), self.clock(s).date())
        context = {
            "debt_present": bool(profile.debts),
            "no_emergency": not any(
                a.balance > 0 for a in profile.savings if a.kind == "emergency"
            ),
            "weekend_habit": any(
                t.category == "dining" and date.fromisoformat(t.date).weekday() >= 5
                for t in self.transactions(s)
            ),
            "subscription_creep": sum(
                r["category"] == "subscriptions" for r in patterns["recurring"]
            )
            > 1,
        }
        chosen = select_lesson(profile, get(s, "lessons_seen", []), context)
        if not chosen:
            return None
        current = {**chosen, "day": today, "answered": False, "correct": None}
        put(s, "lesson", current)
        seen = get(s, "lessons_seen", [])
        if len(seen) >= len(lessons()):
            seen = []
        put(s, "lessons_seen", [*seen, chosen["id"]])
        put(
            s,
            "lesson_progress:" + chosen["id"],
            {"shown_at": self.clock(s).isoformat(), "answered_at": None, "correct": None},
        )
        return current

    def today(self) -> dict[str, Any]:
        with self.store.transaction() as s:
            profile = self.profile(s)
            guard = self.guard(s, profile)
            rec = None if guard else get(s, "recommendation")
            patterns = analyse(profile, self.transactions(s), self.clock(s).date())
            return {
                "profile": profile.to_dict(),
                "date": self.clock(s).date().isoformat(),
                "demo": True,
                "provider": os.getenv("LLM_PROVIDER", "fake"),
                "goal_projection": goal_projection(profile, self.clock(s).date()),
                "timeline_change": get(s, "timeline_change"),
                "overview": {
                    **patterns["projection"],
                    "emergency_saved": sum(
                        a.balance for a in profile.savings if a.kind == "emergency"
                    ),
                    "emergency_target": sum(c.amount for c in profile.fixed_costs)
                    * profile.emergency_months,
                    "cushion_months": str(
                        (
                            Decimal(
                                sum(a.balance for a in profile.savings if a.kind == "emergency")
                            )
                            / max(1, sum(c.amount for c in profile.fixed_costs))
                        ).quantize(Decimal("0.1"))
                    ),
                },
                "analysis": patterns,
                "recommendation": rec,
                "guard": guard,
                "lesson": None if guard else self.lesson(s, profile),
                "rules": get(s, "rules", []),
                "history": history(s),
                "disclaimer": "Educational guidance only. All transfers are simulated.",
            }

    def update_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        profile = UserProfile.from_dict(data)
        with self.store.transaction() as s:
            if get(s, "profile") and profile.id != self.profile(s).id:
                raise ValueError("Use the persona selector to switch demo profiles")
            names = [a.name for a in profile.savings] + [d.name for d in profile.debts]
            if len(names) != len(set(names)):
                raise ValueError("Account and debt names must be unique")
            if any(
                r["status"] == "active" and r["account"] not in names for r in get(s, "rules", [])
            ):
                raise ValueError("Pause rules linked to an account before removing or renaming it")
            put(s, "profile", profile.to_dict())
            self.recompute(s, "Profile updated; projections recalculated")
        return profile.to_dict()

    def confirm(self, merchant: str) -> dict[str, Any]:
        with self.store.transaction() as s:
            p = self.profile(s)
            found = next(
                (
                    r
                    for r in analyse(p, self.transactions(s), self.clock(s).date())["recurring"]
                    if r["merchant"] == merchant
                ),
                None,
            )
            if not found:
                raise ValueError("Recurring assumption not found")
            if not any(c.name == merchant for c in p.fixed_costs):
                p.fixed_costs.append(
                    FixedCost(
                        merchant, found["amount"], min(found["due_day"], 28), found["category"]
                    )
                )
                put(s, "profile", p.to_dict())
                self.recompute(s, "Recurring cost confirmed")
            return p.to_dict()

    def decide(
        self,
        rec_id: str,
        action: str,
        amount: int | None = None,
        schedule_day: int | None = None,
        reason: str = "",
    ) -> dict[str, Any]:
        with self.store.transaction() as s:
            rec = get(s, "recommendation")
            if not rec or rec["id"] != rec_id or rec["status"] != "pending":
                raise ValueError("This recommendation is no longer pending")
            p, now = self.profile(s), self.clock(s)
            if action not in ("accept", "adjust", "decline"):
                raise ValueError("Unknown decision")
            params = dict(rec["chosen"]["params"])
            if action != "decline":
                if self.guard(s, p):
                    raise ValueError("Coaching is paused; keep your cash buffer for now")
                if amount is not None:
                    if type(amount) is not int or amount < 0:
                        raise ValueError("Amount must be nonnegative minor units")
                    params["amount"] = amount
                if schedule_day is not None:
                    if not 1 <= schedule_day <= 28:
                        raise ValueError("Schedule day must be 1–28")
                    params["schedule_day"] = schedule_day
                if (
                    cash_projection(p, now.date(), params["amount"])["buffer_after"]
                    < p.min_cash_buffer
                ):
                    raise ValueError("This amount would use your protected cash buffer")
                if not params.get("review_only") and params["amount"] > 0:
                    rules = get(s, "rules", [])
                    rule = {
                        "id": uuid4().hex,
                        "user_id": p.id,
                        "name": rec["chosen"]["title"],
                        "trigger": {"kind": "category", "value": params["category"]}
                        if params.get("category")
                        else {"kind": "schedule", "value": str(params["schedule_day"])},
                        "amount": params["amount"],
                        "account": params["account"],
                        "status": "active",
                        "affordability_floor": p.min_cash_buffer,
                        "created_from_recommendation": rec_id,
                    }
                    rules.append(rule)
                    put(s, "rules", rules)
                rec["adjustment_params"] = params if action == "adjust" else None
                if action == "adjust":
                    facts = dict(rec["reason_facts"])
                    facts.update(
                        amount=params["amount"],
                        buffer_after=cash_projection(p, now.date(), params["amount"])[
                            "buffer_after"
                        ],
                    )
                    if rec["chosen"]["agent"] == "debt":
                        debt = next(d for d in p.debts if d.name == params["account"])
                        base, changed = amortize(debt), amortize(debt, params["amount"])
                        facts.update(
                            interest_saved=max(0, base.interest - changed.interest),
                            months_saved=max(0, base.months - changed.months),
                            proposed_months=changed.months,
                        )
                    elif rec["chosen"]["agent"] == "savings":
                        facts["proposed_months"] = contribution_months(
                            max(0, facts["target"] - facts["saved"]), params["amount"]
                        )
                        facts["months_saved"] = max(
                            0, facts["current_months"] - facts["proposed_months"]
                        )
                    rec["reason_facts"] = facts
                    rec["chosen"]["facts"] = facts
                    rec["chosen"]["params"] = params
                    rec["chosen"]["impact"].update(
                        buffer_after=facts["buffer_after"],
                        interest_saved=facts.get("interest_saved", 0),
                        goal_months_delta=facts.get("months_saved", 0),
                    )
            else:
                cooldowns = get(s, "cooldowns", {})
                cooldowns[rec["chosen"]["type"]] = (
                    now + timedelta(days=int(os.getenv("DECLINE_COOLDOWN_DAYS", "7")))
                ).isoformat()
                put(s, "cooldowns", cooldowns)
            rec.update(
                status={"accept": "accepted", "adjust": "adjusted", "decline": "declined"}[action],
                decision_at=now.isoformat(),
            )
            put(s, "recommendation", rec)
            put(s, "recommendation:" + rec_id, rec)
            log(
                s,
                now.isoformat(),
                "decision",
                {"id": rec_id, "status": rec["status"], "params": params, "reason": reason},
            )
            return rec

    def save_rule(self, data: dict[str, Any], rule_id: str | None = None) -> dict[str, Any]:
        with self.store.transaction() as s:
            p = self.profile(s)
            rules = get(s, "rules", [])
            rule = (
                next((r for r in rules if r["id"] == rule_id), None)
                if rule_id
                else {
                    "id": uuid4().hex,
                    "user_id": p.id,
                    "created_from_recommendation": None,
                    "name": "My savings rule",
                    "status": "active",
                    "affordability_floor": p.min_cash_buffer,
                }
            )
            if rule is None:
                raise ValueError("Rule not found")
            allowed = {"name", "trigger", "amount", "account", "status", "affordability_floor"}
            rule.update({k: v for k, v in data.items() if k in allowed})
            if (
                rule.get("status") not in ("active", "paused")
                or type(rule.get("amount")) is not int
                or rule["amount"] <= 0
            ):
                raise ValueError("Use a positive rule amount and active or paused status")
            if (
                type(rule.get("affordability_floor")) is not int
                or rule["affordability_floor"] < p.min_cash_buffer
            ):
                raise ValueError("The rule floor must protect your profile buffer")
            trigger = rule.get("trigger", {})
            if trigger.get("kind") not in ("category", "merchant", "schedule") or not trigger.get(
                "value"
            ):
                raise ValueError("Choose a category, merchant, or schedule trigger")
            if trigger["kind"] == "schedule" and not 1 <= int(trigger["value"]) <= 28:
                raise ValueError("Schedule day must be 1–28")
            if rule.get("account") not in [a.name for a in p.savings] + [d.name for d in p.debts]:
                raise ValueError("Choose an existing account")
            if (
                rule["status"] == "active"
                and cash_projection(p, self.clock(s).date(), rule["amount"])["buffer_after"]
                < rule["affordability_floor"]
            ):
                raise ValueError("Rule amount would use your protected buffer")
            if not rule_id:
                rules.append(rule)
            put(s, "rules", rules)
            log(
                s,
                self.clock(s).isoformat(),
                "plan_change",
                {"rule_id": rule["id"], "status": rule["status"], "amount": rule["amount"]},
            )
            return rule

    def ingest(self, s: Session, batch: list[Transaction], advance_clock: bool) -> int:
        p = self.profile(s)
        existing = self.transactions(s)
        ids = {t.id for t in existing}
        unique = {t.id: t for t in batch if t.id not in ids}
        fresh = sorted(
            unique.values(),
            key=lambda t: (
                t.date,
                0 if t.amount > 0 else 2 if t.category == "schedule" else 1,
                t.id,
            ),
        )
        rules, ledger = get(s, "rules", []), get(s, "ledger", [])
        for index, t in enumerate(fresh):
            if advance_clock:
                if p.cash_balance + t.amount < 0:
                    p.declined_transaction = True
                    log(
                        s,
                        self.clock(s).isoformat(),
                        "plan_change",
                        {
                            "reason": "Synthetic outflow declined: insufficient available cash",
                            "transaction_id": t.id,
                        },
                    )
                else:
                    p.cash_balance = Money(p.cash_balance).plus(Money(t.amount)).cents
                    if t.category == "debt":
                        debt = next((d for d in p.debts if d.name == t.merchant), None)
                        if debt:
                            interest = (
                                Money(debt.balance).scale(Decimal(debt.annual_rate) / 1200).cents
                            )
                            debt.balance = max(0, debt.balance + interest + t.amount)
                put(
                    s,
                    "clock",
                    datetime.combine(
                        date.fromisoformat(t.date), datetime.min.time(), tzinfo=timezone.utc
                    ).isoformat(),
                )
                for rule in rules:
                    if rule["trigger"]["kind"] == "schedule" and t.category != "schedule":
                        continue
                    if rule["trigger"]["kind"] == "schedule" and any(
                        e["rule_id"] == rule["id"] and e["executed_at"] == t.date for e in ledger
                    ):
                        continue
                    entry = execute(
                        rule,
                        p,
                        t,
                        sum(
                            -later.amount
                            for later in fresh[index + 1 :]
                            if later.date == t.date and later.amount < 0
                        ),
                    )
                    if entry:
                        if entry["outcome"] == "executed":
                            p.cash_balance = entry["buffer_after"]
                            account = next(
                                (a for a in p.savings if a.name == rule["account"]), None
                            )
                            if account:
                                account.balance += entry["amount"]
                            else:
                                debt = next((d for d in p.debts if d.name == rule["account"]), None)
                                if debt:
                                    actual = min(debt.balance, entry["amount"])
                                    p.cash_balance += entry["amount"] - actual
                                    debt.balance -= actual
                                    entry.update(amount=actual, buffer_after=p.cash_balance)
                                else:
                                    raise ValueError(
                                        "Rule account no longer exists; pause or edit the rule"
                                    )
                        ledger.append(entry)
                        log(s, self.clock(s).isoformat(), "rule_run", entry)
                self.guard(s, p)
        put(s, "profile", p.to_dict())
        put(s, "transactions", [asdict(t) for t in [*existing, *fresh]])
        put(s, "ledger", ledger)
        if fresh:
            self.recompute(s, "Transaction batch imported; projections recalculated")
        return len(fresh)

    def replay(self, days: int) -> dict[str, Any]:
        if not 1 <= days <= 31:
            raise ValueError("Replay 1–31 days at a time")
        with self.store.transaction() as s:
            p, start = self.profile(s), self.clock(s).date()
            batch = []
            for offset in range(1, days + 1):
                day = start + timedelta(days=offset)
                if day.day == p.income_day:
                    batch.append(
                        Transaction(
                            "replay-income-" + day.isoformat(),
                            p.id,
                            day.isoformat(),
                            p.monthly_income,
                            "Synthetic income",
                            "Income",
                            "income",
                            "replay",
                        )
                    )
                if any(
                    r["status"] == "active"
                    and r["trigger"]["kind"] == "schedule"
                    and int(r["trigger"]["value"]) == day.day
                    for r in get(s, "rules", [])
                ):
                    batch.append(
                        Transaction(
                            "replay-schedule-" + day.isoformat(),
                            p.id,
                            day.isoformat(),
                            0,
                            "Scheduled rule check",
                            "Schedule",
                            "schedule",
                            "replay",
                        )
                    )
                for cost in p.fixed_costs:
                    if day.day == cost.due_day:
                        batch.append(
                            Transaction(
                                "replay-" + cost.name + day.isoformat(),
                                p.id,
                                day.isoformat(),
                                -cost.amount,
                                cost.name,
                                cost.name,
                                cost.category,
                                "replay",
                            )
                        )
                if day.weekday() == 5:
                    batch.append(
                        Transaction(
                            "replay-dining-" + day.isoformat(),
                            p.id,
                            day.isoformat(),
                            -2400,
                            "Synthetic dining",
                            "Takeout",
                            "dining",
                            "replay",
                        )
                    )
                if day.day == 28:
                    for debt in p.debts:
                        batch.append(
                            Transaction(
                                "replay-min-" + debt.name + day.isoformat(),
                                p.id,
                                day.isoformat(),
                                -debt.min_payment,
                                "Debt minimum",
                                debt.name,
                                "debt",
                                "replay",
                            )
                        )
            count = self.ingest(s, batch, True)
            put(
                s,
                "clock",
                datetime.combine(
                    start + timedelta(days=days), datetime.min.time(), tzinfo=timezone.utc
                ).isoformat(),
            )
            return {"imported": count, "date": (start + timedelta(days=days)).isoformat()}

    def import_statement(
        self, content: bytes, mapping: dict[str, str], keywords: dict[str, str]
    ) -> dict[str, Any]:
        with self.store.transaction() as s:
            p = self.profile(s)
            result = parse_csv(content, p.id, mapping, keywords)
            count = self.ingest(s, result.transactions, False)
            summary = {
                "imported": count,
                "errors": result.errors,
                "detected": result.detected,
                "patterns": analyse(p, result.transactions, self.clock(s).date()),
            }
            put(s, "import_summary", summary)
            return summary

    def answer_lesson(self, lesson_id: str, answer: int) -> dict[str, Any]:
        with self.store.transaction() as s:
            current = get(s, "lesson")
            if not current or current["id"] != lesson_id:
                raise ValueError("Lesson not shown")
            if not 0 <= answer < len(current["options"]):
                raise ValueError("Choose an available answer")
            if not current["answered"]:
                current.update(answered=True, correct=answer == current["answer"])
                put(s, "lesson", current)
                progress = get(s, "lesson_progress:" + lesson_id)
                progress.update(answered_at=self.clock(s).isoformat(), correct=current["correct"])
                put(s, "lesson_progress:" + lesson_id, progress)
                log(
                    s,
                    self.clock(s).isoformat(),
                    "lesson_completed",
                    {"lesson_id": lesson_id, "correct": current["correct"]},
                )
            return current

    def chat(self, message: str) -> dict[str, Any]:
        recurring = re.fullmatch(
            r"(?:confirm (?:that )?)?(.+?) (?:is|as) (?:a )?recurring (?:cost|expense)[.!]?",
            message.strip(),
            re.I,
        )
        income = re.fullmatch(
            r"(?:set|change|update) my (?:monthly )?income to [$€£]?(\d+(?:\.\d{1,2})?)[.!]?",
            message.strip(),
            re.I,
        )
        if recurring:
            with self.store.transaction() as s:
                patterns = analyse(self.profile(s), self.transactions(s), self.clock(s).date())
                merchant = next(
                    (
                        r["merchant"]
                        for r in patterns["recurring"]
                        if r["merchant"].casefold() == recurring.group(1).strip().casefold()
                    ),
                    None,
                )
            if not merchant:
                raise ValueError(
                    "I could not match that recurring cost. Review the assumptions in My Plan."
                )
            self.confirm(merchant)
            return {
                "text": "I confirmed that recurring cost and recalculated your plan. You can review it in My Plan. Educational guidance only; all actions are simulated.",
                "tools": ["confirm_recurring_assumption"],
                "facts": {},
                "fallback": False,
            }
        if income:
            with self.store.transaction() as s:
                profile = self.profile(s)
            profile.monthly_income = Money(100).scale(Decimal(income.group(1))).cents
            self.update_profile(profile.to_dict())
            return {
                "text": "I updated your monthly income and recalculated the plan. You can review or change it in My Plan. Educational guidance only; all actions are simulated.",
                "tools": ["update_income_assumption"],
                "facts": {"monthly_income": profile.monthly_income},
                "fallback": False,
            }
        with self.store.transaction() as s:
            return respond(
                message,
                self.profile(s),
                get(s, "recommendation"),
                history(s),
                self.clock(s).date(),
                self.client,
            )

    def delete_data(self) -> None:
        import shutil

        with self.store.transaction() as s:
            s.exec(delete(Record))
            s.exec(delete(HistoryEvent))
        # Cache can contain prompts derived from imported data; erase it too.
        from pathlib import Path

        if Path(".llm-cache").exists():
            shutil.rmtree(".llm-cache")
