"""Versioned 15-action catalogue policy loader and deterministic candidate generator (§9, T14).

All monetary calculations use integer EUR cents (`int`, never `float`).
No action in the catalogue moves money, initiates bank transfers, cancels services, or contacts lenders.
"""

from datetime import date, timedelta
import json
from pathlib import Path
from typing import Annotated, Literal
from pydantic import Field, model_validator

from .debt import amortize_single_debt, compare_and_simulate
from .domain import (
    Money,
    Record,
    State,
    capacity,
    eligibility,
    format_eur,
    suggested_amount,
)

CATALOGUE_PATH = Path(__file__).resolve().parents[3] / "policies" / "action-catalogue.v1.json"

SECTION9_ACTION_TITLES: tuple[str, ...] = (
    "Reserve money for an upcoming necessary expense.",
    "Preserve available cash until a known payment.",
    "Prepare a required debt payment.",
    "Make an affordable one-off extra debt payment.",
    "Propose a recurring extra payment with future affordability checks.",
    "Compare supported repayment strategies.",
    "Start/add to/rebuild a reserve.",
    "Contribute to a savings goal.",
    "Adjust a contribution.",
    "Adjust a goal deadline or priority.",
    "Review a recurring discretionary charge.",
    "Pause an optional allocation.",
    "Maintain the current plan.",
    "Clarify a material unknown.",
    "Suggest appropriate external assistance for an unresolved shortfall.",
)

ActionCategory = Literal[
    "cash_flow",
    "debt",
    "reserve",
    "goals",
    "spending",
    "baseline",
    "clarification",
    "shortfall",
]
UrgencyClass = Literal["shortfall", "due_obligation", "ordinary"]
TargetDomain = Literal[
    "obligations",
    "debt",
    "reserve",
    "goal",
    "spending",
    "plan",
    "clarification",
    "shortfall",
]


class ActionEffectSpec(Record):
    reserves_cash: bool
    mutates_account_balance: Literal[False] = False
    executes_external_transfer: Literal[False] = False
    reduces_projected_capacity: bool
    target_domain: TargetDomain
    description: str = Field(min_length=1, max_length=300)


class ActionPresentationSpec(Record):
    headline_template: str = Field(min_length=1, max_length=200)
    summary_template: str = Field(min_length=1, max_length=300)
    cta_label: str = Field(min_length=1, max_length=80)
    disclaimer: str = Field(min_length=1, max_length=240)


class ActionDefinition(Record):
    id: str = Field(min_length=1, max_length=80)
    catalog_number: Annotated[int, Field(strict=True, ge=1, le=15)]
    title: str = Field(min_length=1, max_length=160)
    category: ActionCategory
    urgency_class: UrgencyClass
    scope_jurisdiction: str = Field(min_length=1, max_length=60)
    moves_money: Literal[False] = False
    auto_cancels_services: Literal[False] = False
    auto_contacts_lenders: Literal[False] = False
    calculation_support: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    effects: ActionEffectSpec
    lesson_id: str = Field(min_length=1, max_length=80)
    related_lesson_ids: list[str] = Field(min_length=1)
    presentation: ActionPresentationSpec

    @model_validator(mode="after")
    def validate_lesson_inclusion(self):
        if self.lesson_id not in self.related_lesson_ids:
            raise ValueError(f"Primary lesson_id '{self.lesson_id}' must be in related_lesson_ids for {self.id}.")
        return self


class ActionCataloguePolicy(Record):
    version: str = Field(min_length=1, max_length=60)
    schema_version: Annotated[int, Field(strict=True, ge=1)] = 1
    jurisdiction: str = Field(min_length=1, max_length=60)
    currency: Literal["EUR"] = "EUR"
    executes_money_movement: Literal[False] = False
    auto_cancels_services: Literal[False] = False
    auto_contacts_lenders: Literal[False] = False
    actions: list[ActionDefinition] = Field(min_length=15, max_length=15)

    @model_validator(mode="after")
    def validate_catalogue_invariants(self):
        if len(self.actions) != 15:
            raise ValueError("Catalogue must contain exactly 15 actions per §9.")
        ids = [a.id for a in self.actions]
        if len(set(ids)) != 15:
            raise ValueError("Action IDs in catalogue must be unique.")
        numbers = [a.catalog_number for a in self.actions]
        if numbers != list(range(1, 16)):
            raise ValueError("Action catalog_number must be ordered 1..15.")
        titles = tuple(a.title for a in self.actions)
        if titles != SECTION9_ACTION_TITLES:
            raise ValueError("Action titles must match the 15 canonical §9 action titles.")
        baseline = next((a for a in self.actions if a.id == "maintain_current_plan"), None)
        if baseline is None:
            raise ValueError("Baseline action 'maintain_current_plan' is required.")
        if baseline.prerequisites or baseline.contraindications:
            raise ValueError("Baseline 'maintain_current_plan' must have no prerequisites or contraindications.")
        return self


class ActionEligibilityResult(Record):
    action_id: str
    eligible: bool
    met_prerequisites: list[str] = Field(default_factory=list)
    unmet_prerequisites: list[str] = Field(default_factory=list)
    active_contraindications: list[str] = Field(default_factory=list)


class CandidateAction(Record):
    candidate_id: str = Field(min_length=1, max_length=120)
    action_id: str = Field(min_length=1, max_length=80)
    catalog_number: Annotated[int, Field(strict=True, ge=1, le=15)]
    title: str
    category: ActionCategory
    urgency_class: UrgencyClass
    amount_cents: Money = 0
    moves_money: Literal[False] = False
    reserves_cash: bool = False
    mutates_account_balance: Literal[False] = False
    executes_external_transfer: Literal[False] = False
    target_id: str | None = None
    target_label: str | None = None
    clarify_field: str | None = None
    lesson_id: str
    related_lesson_ids: list[str] = Field(default_factory=list)
    headline: str
    summary: str
    cta_label: str
    disclaimer: str
    policy_version: str
    calculation_evidence: dict[str, int | str | bool | None] = Field(default_factory=dict)


def load_catalogue(path: Path | None = None) -> ActionCataloguePolicy:
    """Loads and validates the versioned 15-action catalogue policy from disk."""
    target = path or CATALOGUE_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    return ActionCataloguePolicy.model_validate(raw)


def _has_multi_period_income(state: State) -> bool:
    """Checks whether confirmed income history spans at least 2 distinct months or >= 25 days."""
    incomes = [t for t in state.transactions if t.amount > 0 and t.category != "transfers"]
    if len(incomes) < 2:
        return False
    months = {(t.date.year, t.date.month) for t in incomes}
    if len(months) >= 2:
        return True
    dates = [t.date for t in incomes]
    return (max(dates) - min(dates)).days >= 25


def _has_amortizing_debt(state: State, available_cents: int) -> bool:
    """Checks whether at least one known-terms positive-balance debt can amortize."""
    if any(not d.terms_known for d in state.debts):
        return False
    active = [d for d in state.debts if d.balance_cents > 0 and d.terms_known]
    if not active:
        return False
    total_balance = sum(d.balance_cents for d in active)
    extra = suggested_amount(available_cents, total_balance) if available_cents >= 500 else 0
    for d in active:
        summary = amortize_single_debt(d, one_off_extra_cents=extra)
        if summary.status == "paid":
            return True
    return False


def evaluate_predicates(
    state: State,
    today: date,
    policy: str = "fifth-of-available-v1",
) -> dict[str, bool]:
    """Computes all boolean prerequisite and contraindication predicates for a financial `State`."""
    s = state.snapshot
    elig = eligibility(state, today)
    avail = capacity(state) if s is not None else 0
    has_planned = any(a.status == "planned" for a in state.actions)
    debt_terms_unknown = any(not d.terms_known for d in state.debts)
    has_unknown_or_stale = (elig is not None) or debt_terms_unknown

    snapshot_present = s is not None
    snapshot_fresh = bool(
        s is not None
        and s.as_of <= today <= s.as_of + timedelta(days=7)
        and today <= s.horizon
    )
    obligations_complete = bool(s is not None and s.obligations_complete)
    debt_known = bool(s is not None and s.debt_known)
    no_shortfall = bool(s is not None and avail >= 0)
    has_shortfall = bool(s is not None and avail < 0)

    upcoming_necessary = bool(
        s is not None
        and any(o.kind in ("rent", "living") and o.due >= today for o in s.obligations)
    )
    upcoming_any = bool(
        s is not None and any(o.due >= today for o in s.obligations)
    )
    has_req_debt = bool(
        s is not None
        and (
            any(o.kind == "debt" and o.due >= today for o in s.obligations)
            or any(d.balance_cents > 0 and d.min_payment_cents > 0 for d in state.debts)
        )
    )

    goal_remaining = max(0, s.goal_target - s.saved) if s is not None else 0
    prop_save = suggested_amount(avail, goal_remaining, policy=policy) if (s is not None and avail >= 500) else 0
    has_positive_capacity = bool(s is not None and avail >= 500)
    has_amortizing = _has_amortizing_debt(state, avail) if s is not None else False
    multi_period_income = bool(s is not None and avail >= 1000 and _has_multi_period_income(state))
    known_active_debts = [d for d in state.debts if d.balance_cents > 0 and d.terms_known]
    has_multiple_debts = bool(not debt_terms_unknown and len(known_active_debts) >= 2)

    has_adjustable = bool(
        s is not None
        and no_shortfall
        and (has_planned or (avail >= 1000 and goal_remaining > 0 and prop_save >= 500))
    )
    has_active_goal = bool(s is not None and s.goal_target > 0 and goal_remaining > 0)
    goal_timeline_strained = bool(s is not None and goal_remaining > avail)

    has_recurring_discretionary = bool(
        s is not None
        and (
            any(t.amount < 0 and t.category == "subscriptions" for t in state.transactions)
            or any(o.kind == "other" and o.due >= today for o in s.obligations)
        )
    )
    planned_pressures_capacity = bool(
        s is not None
        and has_planned
        and (avail < 0 or avail < (s.protected // 2))
    )

    return {
        # Prerequisites
        "snapshot_present": snapshot_present,
        "snapshot_fresh": snapshot_fresh,
        "obligations_complete": obligations_complete,
        "debt_known": debt_known,
        "no_shortfall": no_shortfall,
        "has_shortfall": has_shortfall,
        "has_unknown_or_stale_data": has_unknown_or_stale,
        "has_upcoming_necessary_obligation": upcoming_necessary,
        "has_upcoming_obligation": upcoming_any,
        "has_required_debt_obligation_or_debt": has_req_debt,
        "has_positive_capacity": has_positive_capacity,
        "has_amortizing_debt_with_balance": has_amortizing,
        "has_multi_period_income_history": multi_period_income,
        "has_multiple_debts_or_repayment_choice": has_multiple_debts,
        "reserve_below_target": bool(s is not None and s.saved < s.goal_target),
        "goal_remaining_positive": bool(goal_remaining > 0),
        "has_adjustable_contribution": has_adjustable,
        "has_active_goal": has_active_goal,
        "goal_timeline_strained": goal_timeline_strained,
        "has_recurring_discretionary_charge": has_recurring_discretionary,
        "has_active_planned_action": has_planned,
        "planned_allocation_pressures_capacity": planned_pressures_capacity,
        # Contraindications
        "active_shortfall": has_shortfall,
        "material_unknown_unclarified": elig is not None,
        "active_planned_action_exists": has_planned,
        "debt_terms_unknown": debt_terms_unknown,
        "zero_discretionary_capacity": not has_positive_capacity,
        "no_shortfall_present": not has_shortfall,
        "all_material_fields_known": not has_unknown_or_stale,
    }


def evaluate_action_eligibility(
    action: ActionDefinition,
    state: State,
    today: date,
    policy: str = "fifth-of-available-v1",
    predicates: dict[str, bool] | None = None,
) -> ActionEligibilityResult:
    """Evaluates whether an `ActionDefinition` is eligible under the given `State`."""
    preds = predicates if predicates is not None else evaluate_predicates(state, today, policy=policy)
    met: list[str] = []
    unmet: list[str] = []
    for req in action.prerequisites:
        if preds.get(req, False):
            met.append(req)
        else:
            unmet.append(req)
    contra = [c for c in action.contraindications if preds.get(c, False)]
    return ActionEligibilityResult(
        action_id=action.id,
        eligible=(len(unmet) == 0 and len(contra) == 0),
        met_prerequisites=met,
        unmet_prerequisites=unmet,
        active_contraindications=contra,
    )


def _build_candidate(
    action: ActionDefinition,
    catalogue_version: str,
    suffix: str = "default",
    amount_cents: int = 0,
    target_id: str | None = None,
    target_label: str | None = None,
    clarify_field: str | None = None,
    headline: str | None = None,
    summary: str | None = None,
    evidence: dict[str, int | str | bool | None] | None = None,
) -> CandidateAction:
    return CandidateAction(
        candidate_id=f"{action.id}:{suffix}",
        action_id=action.id,
        catalog_number=action.catalog_number,
        title=action.title,
        category=action.category,
        urgency_class=action.urgency_class,
        amount_cents=max(0, int(amount_cents)),
        moves_money=False,
        reserves_cash=action.effects.reserves_cash,
        mutates_account_balance=False,
        executes_external_transfer=False,
        target_id=target_id,
        target_label=target_label,
        clarify_field=clarify_field,
        lesson_id=action.lesson_id,
        related_lesson_ids=list(action.related_lesson_ids),
        headline=headline or action.presentation.headline_template,
        summary=summary or action.presentation.summary_template,
        cta_label=action.presentation.cta_label,
        disclaimer=action.presentation.disclaimer,
        policy_version=catalogue_version,
        calculation_evidence=evidence or {},
    )


def generate_candidates(
    state: State,
    today: date,
    policy: str = "fifth-of-available-v1",
    catalogue: ActionCataloguePolicy | None = None,
) -> list[CandidateAction]:
    """Generates concrete, eligible `CandidateAction` instances for the given `State`."""
    cat = catalogue if catalogue is not None else load_catalogue()
    preds = evaluate_predicates(state, today, policy=policy)
    s = state.snapshot
    avail = capacity(state) if s is not None else 0
    elig_reason = eligibility(state, today)

    candidates: list[CandidateAction] = []

    for action in cat.actions:
        elig_res = evaluate_action_eligibility(action, state, today, policy=policy, predicates=preds)
        if not elig_res.eligible:
            continue

        aid = action.id

        if aid == "reserve_necessary_expense" and s is not None:
            necessary = sorted(
                [o for o in s.obligations if o.kind in ("rent", "living") and o.due >= today],
                key=lambda o: (o.due, o.id),
            )
            target = necessary[0]
            amt = min(avail, target.amount)
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=target.id,
                    amount_cents=amt,
                    target_id=target.id,
                    target_label=target.label,
                    headline=action.presentation.headline_template.format(
                        amount=format_eur(amt),
                        target_label=target.label,
                    ),
                    summary=action.presentation.summary_template.format(
                        amount=format_eur(amt),
                        target_label=target.label,
                        due_date=target.due.isoformat(),
                    ),
                    evidence={
                        "available_cents": avail,
                        "obligation_amount_cents": target.amount,
                        "due_date": target.due.isoformat(),
                    },
                )
            )

        elif aid == "preserve_cash_until_payment" and s is not None:
            upcoming = sorted([o for o in s.obligations if o.due >= today], key=lambda o: (o.due, o.id))
            target = upcoming[0]
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=target.id,
                    amount_cents=0,
                    target_id=target.id,
                    target_label=target.label,
                    headline=action.presentation.headline_template.format(
                        available=format_eur(avail),
                        target_label=target.label,
                    ),
                    summary=action.presentation.summary_template.format(
                        target_label=target.label,
                        obligation_amount=format_eur(target.amount),
                        due_date=target.due.isoformat(),
                    ),
                    evidence={
                        "available_cents": avail,
                        "next_obligation_cents": target.amount,
                        "due_date": target.due.isoformat(),
                    },
                )
            )

        elif aid == "prepare_required_debt" and s is not None:
            debt_obs = sorted([o for o in s.obligations if o.kind == "debt" and o.due >= today], key=lambda o: (o.due, o.id))
            if debt_obs:
                target_ob = debt_obs[0]
                amt = min(avail, target_ob.amount) if avail > 0 else 0
                candidates.append(
                    _build_candidate(
                        action,
                        cat.version,
                        suffix=target_ob.id,
                        amount_cents=amt,
                        target_id=target_ob.id,
                        target_label=target_ob.label,
                        headline=action.presentation.headline_template.format(
                            amount=format_eur(target_ob.amount),
                            target_label=target_ob.label,
                        ),
                        summary=action.presentation.summary_template.format(
                            amount=format_eur(target_ob.amount),
                            target_label=target_ob.label,
                        ),
                        evidence={
                            "required_payment_cents": target_ob.amount,
                            "available_cents": avail,
                            "already_in_obligations": True,
                        },
                    )
                )
            else:
                active_debts = sorted(
                    [d for d in state.debts if d.balance_cents > 0 and d.min_payment_cents > 0],
                    key=lambda d: (d.due_day, -d.apr_bps, d.id),
                )
                target_d = active_debts[0]
                amt = min(avail, target_d.min_payment_cents)
                candidates.append(
                    _build_candidate(
                        action,
                        cat.version,
                        suffix=target_d.id,
                        amount_cents=amt,
                        target_id=target_d.id,
                        target_label=target_d.label,
                        headline=action.presentation.headline_template.format(
                            amount=format_eur(target_d.min_payment_cents),
                            target_label=target_d.label,
                        ),
                        summary=action.presentation.summary_template.format(
                            amount=format_eur(target_d.min_payment_cents),
                            target_label=target_d.label,
                        ),
                        evidence={
                            "required_payment_cents": target_d.min_payment_cents,
                            "available_cents": avail,
                            "already_in_obligations": False,
                        },
                    )
                )

        elif aid == "extra_debt_payment_one_off" and s is not None:
            active_debts = sorted(
                [d for d in state.debts if d.balance_cents > 0 and d.terms_known],
                key=lambda d: (-d.apr_bps, d.balance_cents, d.id),
            )
            target_d = active_debts[0]
            total_debt = sum(d.balance_cents for d in active_debts)
            extra = min(target_d.balance_cents, suggested_amount(avail, total_debt, policy=policy))
            sim = compare_and_simulate(
                active_debts,
                revision=state.revision,
                one_off_extra_cents=extra,
                target_debt_id=target_d.id,
            )
            interest_saved = (
                sim.one_off_preview.interest_saved_cents
                if sim.one_off_preview and sim.one_off_preview.interest_saved_cents is not None
                else 0
            )
            rem_cap = avail - extra
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=target_d.id,
                    amount_cents=extra,
                    target_id=target_d.id,
                    target_label=target_d.label,
                    headline=action.presentation.headline_template.format(
                        amount=format_eur(extra),
                        target_label=target_d.label,
                    ),
                    summary=action.presentation.summary_template.format(
                        interest_saved=format_eur(interest_saved),
                        remaining_capacity=format_eur(rem_cap),
                    ),
                    evidence={
                        "extra_payment_cents": extra,
                        "interest_saved_cents": interest_saved,
                        "remaining_capacity_cents": rem_cap,
                        "target_apr_bps": target_d.apr_bps,
                    },
                )
            )

        elif aid == "extra_debt_payment_recurring" and s is not None:
            active_debts = sorted(
                [d for d in state.debts if d.balance_cents > 0 and d.terms_known],
                key=lambda d: (-d.apr_bps, d.balance_cents, d.id),
            )
            target_d = active_debts[0]
            total_debt = sum(d.balance_cents for d in active_debts)
            rec_extra = min(target_d.balance_cents, suggested_amount(avail, total_debt, policy=policy))
            sim = compare_and_simulate(
                active_debts,
                revision=state.revision,
                recurring_extra_cents=rec_extra,
            )
            int_saved = sim.avalanche.interest_saved_vs_baseline_cents or 0
            m_saved = sim.avalanche.months_saved_vs_baseline or 0
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=target_d.id,
                    amount_cents=rec_extra,
                    target_id=target_d.id,
                    target_label=target_d.label,
                    headline=action.presentation.headline_template.format(
                        amount=format_eur(rec_extra),
                        target_label=target_d.label,
                    ),
                    summary=action.presentation.summary_template.format(
                        months_saved=m_saved,
                        interest_saved=format_eur(int_saved),
                    ),
                    evidence={
                        "recurring_extra_cents": rec_extra,
                        "interest_saved_cents": int_saved,
                        "months_saved": m_saved,
                    },
                )
            )

        elif aid == "compare_repayment_strategies" and s is not None:
            active_debts = [d for d in state.debts if d.balance_cents > 0 and d.terms_known]
            sim = compare_and_simulate(active_debts, revision=state.revision)
            av_m = sim.avalanche.months or 0
            av_i = sim.avalanche.total_interest_cents or 0
            sn_m = sim.snowball.months or 0
            sn_i = sim.snowball.total_interest_cents or 0
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="avalanche_vs_snowball",
                    amount_cents=0,
                    headline=action.presentation.headline_template.format(debt_count=len(active_debts)),
                    summary=action.presentation.summary_template.format(
                        avalanche_months=av_m,
                        avalanche_interest=format_eur(av_i),
                        snowball_months=sn_m,
                        snowball_interest=format_eur(sn_i),
                    ),
                    evidence={
                        "debt_count": len(active_debts),
                        "avalanche_months": av_m,
                        "avalanche_interest_cents": av_i,
                        "snowball_months": sn_m,
                        "snowball_interest_cents": sn_i,
                    },
                )
            )

        elif aid == "build_reserve" and s is not None:
            remaining = max(0, s.goal_target - s.saved)
            amt = suggested_amount(avail, remaining, policy=policy)
            after = s.saved + amt
            rem_cap = avail - amt
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="reserve",
                    amount_cents=amt,
                    target_id="reserve",
                    target_label=s.goal_name,
                    headline=action.presentation.headline_template.format(amount=format_eur(amt)),
                    summary=action.presentation.summary_template.format(
                        saved_before=format_eur(s.saved),
                        saved_after=format_eur(after),
                        goal_target=format_eur(s.goal_target),
                        remaining_capacity=format_eur(rem_cap),
                    ),
                    evidence={
                        "amount_cents": amt,
                        "saved_before_cents": s.saved,
                        "saved_after_cents": after,
                        "goal_target_cents": s.goal_target,
                        "remaining_capacity_cents": rem_cap,
                    },
                )
            )

        elif aid == "contribute_savings_goal" and s is not None:
            remaining = max(0, s.goal_target - s.saved)
            amt = suggested_amount(avail, remaining, policy=policy)
            after = s.saved + amt
            headline = action.presentation.headline_template.format(amount=format_eur(amt))
            summary_txt = action.presentation.summary_template.format(
                goal_name=s.goal_name,
                saved_before=format_eur(s.saved),
                saved_after=format_eur(after),
                goal_target=format_eur(s.goal_target),
            )
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="goal",
                    amount_cents=amt,
                    target_id="goal",
                    target_label=s.goal_name,
                    headline=headline,
                    summary=summary_txt,
                    evidence={
                        "amount_cents": amt,
                        "saved_before_cents": s.saved,
                        "saved_after_cents": after,
                        "goal_target_cents": s.goal_target,
                        "remaining_capacity_cents": avail - amt,
                        "policy": policy,
                    },
                )
            )

        elif aid == "adjust_contribution" and s is not None:
            remaining = max(0, s.goal_target - s.saved)
            planned = next((a for a in state.actions if a.status == "planned"), None)
            if planned is not None:
                cap_without = capacity(state, exclude_action=planned.id)
                adjusted = min(cap_without, max(500, planned.amount // 2 // 500 * 500 or 500))
                rem_cap = max(0, cap_without - adjusted)
            else:
                base_amt = suggested_amount(avail, remaining, policy=policy)
                adjusted = max(500, (base_amt // 2) // 500 * 500 or 500)
                adjusted = min(avail, remaining, adjusted)
                rem_cap = avail - adjusted
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="conservative",
                    amount_cents=adjusted,
                    target_id="goal",
                    target_label=s.goal_name,
                    headline=action.presentation.headline_template.format(
                        amount=format_eur(adjusted),
                        goal_name=s.goal_name,
                    ),
                    summary=action.presentation.summary_template.format(
                        amount=format_eur(adjusted),
                        remaining_capacity=format_eur(rem_cap),
                        horizon_date=s.horizon.isoformat(),
                    ),
                    evidence={
                        "adjusted_amount_cents": adjusted,
                        "remaining_capacity_cents": rem_cap,
                    },
                )
            )

        elif aid == "adjust_goal_timeline" and s is not None:
            remaining = max(0, s.goal_target - s.saved)
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="timeline",
                    amount_cents=0,
                    target_id="goal",
                    target_label=s.goal_name,
                    headline=action.presentation.headline_template.format(goal_name=s.goal_name),
                    summary=action.presentation.summary_template.format(
                        goal_remaining=format_eur(remaining),
                        available=format_eur(avail),
                    ),
                    evidence={
                        "goal_remaining_cents": remaining,
                        "available_cents": avail,
                    },
                )
            )

        elif aid == "review_recurring_charge" and s is not None:
            sub_txns = [t for t in state.transactions if t.amount < 0 and t.category == "subscriptions"]
            if sub_txns:
                target_t = sub_txns[0]
                charge_amt = abs(target_t.amount)
                label = target_t.description
                tid = target_t.id
            else:
                other_obs = [o for o in s.obligations if o.kind == "other" and o.due >= today]
                target_o = other_obs[0]
                charge_amt = target_o.amount
                label = target_o.label
                tid = target_o.id
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=tid,
                    amount_cents=0,
                    target_id=tid,
                    target_label=label,
                    headline=action.presentation.headline_template.format(
                        target_label=label,
                        amount=format_eur(charge_amt),
                    ),
                    summary=action.presentation.summary_template.format(
                        target_label=label,
                        amount=format_eur(charge_amt),
                    ),
                    evidence={
                        "recurring_charge_cents": charge_amt,
                    },
                )
            )

        elif aid == "pause_optional_allocation" and s is not None:
            planned = next(a for a in state.actions if a.status == "planned")
            cap_after = capacity(state, exclude_action=planned.id)
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=planned.id,
                    amount_cents=0,
                    target_id=planned.id,
                    target_label="Planned reservation",
                    headline=action.presentation.headline_template.format(amount=format_eur(planned.amount)),
                    summary=action.presentation.summary_template.format(
                        amount=format_eur(planned.amount),
                        capacity_after_pause=format_eur(cap_after),
                    ),
                    evidence={
                        "paused_amount_cents": planned.amount,
                        "capacity_before_cents": avail,
                        "capacity_after_cents": cap_after,
                    },
                )
            )

        elif aid == "maintain_current_plan":
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="baseline",
                    amount_cents=0,
                    headline=action.presentation.headline_template,
                    summary=action.presentation.summary_template,
                    evidence={"available_cents": avail},
                )
            )

        elif aid == "clarify_material_unknown":
            if elig_reason is not None:
                c_field, c_question = elig_reason
            else:
                unknown_debt = next(d for d in state.debts if not d.terms_known)
                c_field = "debt_terms"
                c_question = f"Confirm the interest rate (APR) and minimum payment for {unknown_debt.label} before comparing debt steps."
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix=c_field,
                    amount_cents=0,
                    clarify_field=c_field,
                    headline=action.presentation.headline_template.format(clarify_field=c_field),
                    summary=action.presentation.summary_template.format(clarify_question=c_question),
                    evidence={"clarify_field": c_field},
                )
            )

        elif aid == "external_assistance_shortfall" and s is not None:
            shortfall_abs = abs(avail)
            candidates.append(
                _build_candidate(
                    action,
                    cat.version,
                    suffix="shortfall",
                    amount_cents=0,
                    headline=action.presentation.headline_template.format(
                        shortfall_amount=format_eur(shortfall_abs)
                    ),
                    summary=action.presentation.summary_template.format(
                        shortfall_amount=format_eur(shortfall_abs)
                    ),
                    evidence={
                        "shortfall_cents": shortfall_abs,
                        "available_cents": avail,
                    },
                )
            )

    return candidates
