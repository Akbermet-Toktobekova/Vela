"""Deterministic Multi-Criteria Decision Analysis (MCDA) ranking, urgency classes,
hard affordability constraints, and sensitivity analysis (§10, T15).

Specification guarantees (§10):
- Pipeline:
    A. Data validity and service eligibility.
    B. Candidate generation (including `maintain_current_plan` baseline).
    C. Scenario calculations.
    D. Hard constraints and urgency class (`shortfall` > `due_obligation` > `ordinary`).
    E. Multi-criteria ranking of comparable eligible actions:
       S(a) = wR*vR(a) + wF*vF(a) + wG*vG(a) + wM*vM(a) + wE*(1 - cE(a)).
    F. Sensitivity checks (±20% weight perturbation).
    G. Publication with `DecisionEvaluationSnapshot` (inputs, versions, reason codes,
       selected + runner-up, never hidden chain-of-thought).
- All calculations use integer EUR cents and integer basis points (`0..10_000`).
- Unknown criteria are represented as `None` (never silently converted to `0` or
  renormalized differently per candidate); a candidate with an unknown criterion on a
  positively weighted dimension cannot receive a numeric score.
- Reserve/goal overlap is explicitly discounted (`reserve_goal_overlap_discount_bp`) so the
  same reserve euro is never double-counted as both 100% resilience and 100% goal benefit.
- Internal transfers / savings reservations are never treated as financial profit (`vF = 0`).
"""

from datetime import date, timedelta
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4
from pydantic import Field, model_validator

from .catalogue import (
    ActionCataloguePolicy,
    CandidateAction,
    UrgencyClass,
    generate_candidates,
    load_catalogue,
)
from .domain import (
    Money,
    Record,
    State,
    capacity,
    eligibility,
    format_eur,
)

SCORING_PATH = Path(__file__).resolve().parents[3] / "policies" / "scoring.v1.json"
BP_SCALE = 10_000

URGENCY_PRECEDENCE: dict[UrgencyClass, int] = {
    "shortfall": 0,
    "due_obligation": 1,
    "ordinary": 2,
}


class ScoringWeights(Record):
    R: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)]
    F: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)]
    G: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)]
    M: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)]
    E: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)]

    @model_validator(mode="after")
    def validate_normalized(self):
        total = self.R + self.F + self.G + self.M + self.E
        if total != BP_SCALE:
            raise ValueError(f"Scoring weights must sum to {BP_SCALE} basis points, got {total}.")
        return self


class ScoringAnchors(Record):
    resilience_target_cents: Annotated[int, Field(strict=True, gt=0)] = 100_000
    financial_benefit_horizon_days: Annotated[int, Field(strict=True, gt=0)] = 365
    financial_benefit_anchor_cents: Annotated[int, Field(strict=True, gt=0)] = 15_000
    goal_progress_step_anchor_cents: Annotated[int, Field(strict=True, gt=0)] = 20_000
    reserve_goal_overlap_discount_bp: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)] = 5_000
    imminent_obligation_window_days: Annotated[int, Field(strict=True, ge=1, le=30)] = 5
    imminent_obligation_tight_capacity_ratio_bp: Annotated[int, Field(strict=True, ge=0, le=BP_SCALE)] = 2_500


class SensitivityConfig(Record):
    perturbation_ratio_bp: Annotated[int, Field(strict=True, ge=100, le=5_000)] = 2_000
    min_top_margin_bp: Annotated[int, Field(strict=True, ge=0, le=2_000)] = 150
    unstable_fallback_action: Literal["clarify_or_preserve_plan"] = "clarify_or_preserve_plan"


class ScoringPolicy(Record):
    version: str = Field(min_length=1, max_length=60)
    schema_version: Annotated[int, Field(strict=True, ge=1)] = 1
    provisional: bool = True
    domain_review_status: str = Field(default="pending_human_review", min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    scale_max_bp: Annotated[int, Field(strict=True, ge=10_000, le=10_000)] = BP_SCALE
    weights_bp: ScoringWeights
    anchors: ScoringAnchors = Field(default_factory=ScoringAnchors)
    sensitivity: SensitivityConfig = Field(default_factory=SensitivityConfig)
    urgency_precedence: list[UrgencyClass] = Field(
        default_factory=lambda: ["shortfall", "due_obligation", "ordinary"]
    )


class CriterionUtilities(Record):
    """Anchored utility values in basis points [0..10_000], or None if unknown.
    Never converts unknown (`None`) to `0`.
    """

    vR_bp: int | None = None
    vF_bp: int | None = None
    vG_bp: int | None = None
    vM_bp: int | None = None
    cE_bp: int | None = None


class ScoredCandidate(Record):
    candidate: CandidateAction
    passed_hard_constraints: bool
    hard_constraint_reasons: list[str] = Field(default_factory=list)
    active_urgency_tier: UrgencyClass
    utilities: CriterionUtilities
    has_unknown_criterion: bool = False
    weighted_score_bp: int | None = None
    rank: int | None = None


class SensitivityReport(Record):
    stable: bool
    perturbation_ratio_bp: int
    baseline_winner_id: str | None = None
    baseline_runner_up_id: str | None = None
    score_margin_bp: int | None = None
    flipped_under_trials: list[str] = Field(default_factory=list)
    fallback_triggered: bool = False
    fallback_reason: str | None = None


class DecisionEvaluationSnapshot(Record):
    evaluation_id: str = Field(min_length=1, max_length=80)
    evaluated_on: date
    state_revision: int
    catalogue_version: str
    scoring_version: str
    provisional_weights: bool
    active_urgency_class: UrgencyClass
    reason_codes: list[str] = Field(default_factory=list)
    inputs_summary: dict[str, int | str | bool | None] = Field(default_factory=dict)
    selected_candidate_id: str
    selected_action_id: str
    selected_headline: str
    selected_summary: str
    selected_amount_cents: Money = 0
    runner_up_candidate_id: str | None = None
    runner_up_action_id: str | None = None
    sensitivity: SensitivityReport
    ranked_candidates: list[ScoredCandidate] = Field(default_factory=list)


def load_scoring_policy(path: Path | None = None) -> ScoringPolicy:
    target = path or SCORING_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    return ScoringPolicy.model_validate(raw)


def _clamp_bp(value: int) -> int:
    return max(0, min(BP_SCALE, int(value)))


def _linear_anchor_bp(value: int, anchor: int) -> int:
    if value <= 0 or anchor <= 0:
        return 0
    if value >= anchor:
        return BP_SCALE
    return _clamp_bp((value * BP_SCALE) // anchor)


def check_hard_constraints(
    candidate: CandidateAction,
    state: State,
    today: date,
) -> tuple[bool, list[str]]:
    """Stage D1: Enforces hard horizon affordability and safety constraints BEFORE any scoring.

    Hard constraint (§10):
    After an ordinary planning action, dated available money must cover known necessary
    expenses, obligations, and the agreed protected balance within the documented horizon.
    Avoid duplicate reserve subtraction. If baseline is already infeasible, use a shortfall
    policy rather than discretionary allocations.
    """
    reasons: list[str] = []
    s = state.snapshot
    avail = capacity(state) if s is not None else 0

    if candidate.moves_money or candidate.mutates_account_balance or candidate.executes_external_transfer:
        reasons.append("HARD_REJECT_MOVES_MONEY")

    if s is None:
        if candidate.action_id not in ("clarify_material_unknown", "maintain_current_plan"):
            reasons.append("HARD_REJECT_MISSING_SNAPSHOT")
        return (len(reasons) == 0, reasons)

    # If baseline is already infeasible (avail < 0), reject all ordinary discretionary allocations
    if avail < 0:
        if candidate.urgency_class != "shortfall" and candidate.action_id != "maintain_current_plan":
            reasons.append("HARD_REJECT_BASELINE_SHORTFALL")
        return (len(reasons) == 0, reasons)

    # If material unknowns exist, reject cash-reserving actions
    elig = eligibility(state, today)
    debt_unknown = any(not d.terms_known for d in state.debts)
    if (elig is not None or debt_unknown) and candidate.reserves_cash:
        reasons.append("HARD_REJECT_UNCLARIFIED_INPUTS")

    # For any action that reserves cash (unless it is already counted in `obligations`, such as
    # `prepare_required_debt` when `already_in_obligations=True`), post-action lowest projected
    # uncommitted balance must remain >= 0.
    already_in_obligations = bool(candidate.calculation_evidence.get("already_in_obligations", False))
    if candidate.reserves_cash and not already_in_obligations:
        if candidate.amount_cents <= 0:
            reasons.append("HARD_REJECT_ZERO_RESERVATION")
        elif avail - candidate.amount_cents < 0:
            reasons.append("HARD_REJECT_EXCEEDS_HORIZON_CAPACITY")

    return (len(reasons) == 0, reasons)


def classify_candidate_urgency(
    candidate: CandidateAction,
    state: State,
    today: date,
    anchors: ScoringAnchors,
) -> tuple[UrgencyClass, list[str]]:
    """Stage D2: Determines the effective urgency class of an eligible candidate.

    Urgency classes are strictly outside the weighted score:
    1. `shortfall`: active projected shortfall (`capacity < 0`).
    2. `due_obligation`: material unknown requiring clarification, or an imminent mandatory
       obligation / required debt payment due within `imminent_obligation_window_days` (or when
       uncommitted cash is tight relative to the obligation).
    3. `ordinary`: standard multi-criteria planning class.
    """
    s = state.snapshot
    avail = capacity(state) if s is not None else 0

    if s is not None and avail < 0:
        if candidate.action_id in ("external_assistance_shortfall", "pause_optional_allocation"):
            return ("shortfall", ["URGENCY_SHORTFALL"])
        return ("ordinary", [])

    if candidate.action_id == "clarify_material_unknown":
        return ("due_obligation", ["URGENCY_CLARIFY_UNKNOWN"])

    if candidate.action_id in ("prepare_required_debt", "reserve_necessary_expense", "preserve_cash_until_payment") and s is not None:
        window_end = today + timedelta(days=anchors.imminent_obligation_window_days)
        target_ob = next((o for o in s.obligations if o.id == candidate.target_id), None)
        already_protected = bool(candidate.calculation_evidence.get("already_in_obligations", False))

        # Unprotected required debt payment not yet in obligations is always an urgent due obligation
        if candidate.action_id == "prepare_required_debt" and not already_protected:
            return ("due_obligation", ["URGENCY_UNPROTECTED_REQUIRED_DEBT"])

        if target_ob is not None:
            is_imminent = target_ob.due <= window_end
            # Tight capacity: available headroom is <= 25% of the obligation amount
            is_tight = (avail * BP_SCALE) <= (target_ob.amount * anchors.imminent_obligation_tight_capacity_ratio_bp)
            if is_imminent and is_tight:
                return ("due_obligation", ["URGENCY_IMMINENT_OBLIGATION_TIGHT_HEADROOM"])

    return ("ordinary", ["URGENCY_ORDINARY_PLANNING"])


@dataclass(frozen=True)
class UtilityContext:
    """Explicit calculation facts, without requiring a legacy Snapshot."""
    available_cents: int | None
    has_planned: bool
    deferred: bool


def compute_utilities(
    candidate: CandidateAction,
    state: State,
    anchors: ScoringAnchors,
    custom_evidence: dict[str, int | str | bool | None] | None = None,
) -> CriterionUtilities:
    # Legacy wrapper retains its original missing-snapshot behaviour exactly.
    return compute_utilities_from_context(candidate, UtilityContext(
        capacity(state) if state.snapshot is not None else 0,
        any(action.status == "planned" for action in state.actions), state.deferred),
        anchors, custom_evidence)


def compute_utilities_from_context(
    candidate: CandidateAction,
    context: UtilityContext,
    anchors: ScoringAnchors,
    custom_evidence: dict[str, int | str | bool | None] | None = None,
) -> CriterionUtilities:
    """Computes anchored utility values in basis points [0..10_000] for R, F, G, M, and burden cE.

    Rules (§10):
    - Never normalize by whichever candidate happens to be best today; all utilities are anchored
      against policy parameters in `ScoringAnchors`.
    - Never convert unknown (`None`) to `0`. If `custom_evidence` or `candidate.calculation_evidence`
      marks a criterion as `"unknown"`, its utility is `None`.
    - Do not count the same reserve benefit as full resilience and full goal benefit without
      adjusting overlap (`reserve_goal_overlap_discount_bp`).
    - Do not equate transfers or savings reservations with financial profit (`vF_bp = 0` for
      savings/reserve transfers; `vF_bp > 0` only for actual interest savings or avoided charges).
    """
    ev = {**candidate.calculation_evidence, **(custom_evidence or {})}
    if any(ev.get(k) == "unknown" for k in ("vR_bp", "vF_bp", "vG_bp", "vM_bp", "cE_bp")):
        return CriterionUtilities(
            vR_bp=None if ev.get("vR_bp") == "unknown" else 5_000,
            vF_bp=None if ev.get("vF_bp") == "unknown" else 0,
            vG_bp=None if ev.get("vG_bp") == "unknown" else 0,
            vM_bp=None if ev.get("vM_bp") == "unknown" else 5_000,
            cE_bp=None if ev.get("cE_bp") == "unknown" else 2_000,
        )

    avail = context.available_cents
    aid = candidate.action_id
    if avail is None and aid in ('external_assistance_shortfall', 'preserve_cash_until_payment'):
        # Current canonical unknown capacity must not turn into zero resilience.
        return CriterionUtilities(vR_bp=None, vF_bp=0, vG_bp=0, vM_bp=8_000,
                                  cE_bp=2_500 if aid == 'external_assistance_shortfall' else 500)
    overlap_keep_bp = BP_SCALE - anchors.reserve_goal_overlap_discount_bp

    # Default baseline values
    vR = 0
    vF = 0
    vG = 0
    vM = 5_000
    cE = 2_000

    if aid == "external_assistance_shortfall":
        shortfall_cents = int(ev.get("shortfall_cents") or abs(avail))
        vR = _linear_anchor_bp(shortfall_cents, anchors.resilience_target_cents)
        vR = max(8_500, vR)
        vF = 0
        vG = 0
        vM = 8_000
        cE = 2_500

    elif aid == "pause_optional_allocation":
        paused_cents = int(ev.get("paused_amount_cents") or 0)
        vR = max(7_000, _linear_anchor_bp(paused_cents * 4, anchors.resilience_target_cents))
        vF = 0
        vG = 0
        vM = 8_500
        cE = 1_000

    elif aid == "clarify_material_unknown":
        vR = 8_000
        vF = 0
        vG = 0
        vM = 9_000
        cE = 1_000

    elif aid == "prepare_required_debt":
        req_cents = int(ev.get("required_payment_cents") or candidate.amount_cents)
        vR = max(7_500, _linear_anchor_bp(req_cents * 4, anchors.resilience_target_cents))
        # Avoiding late payment fees / default interest on a required debt obligation
        vF = 4_000
        vG = 0
        vM = 8_500
        cE = 1_500

    elif aid == "reserve_necessary_expense":
        ob_cents = int(ev.get("obligation_amount_cents") or candidate.amount_cents)
        vR = _linear_anchor_bp(ob_cents, anchors.resilience_target_cents)
        vF = 0
        vG = 0
        vM = 7_500
        cE = 1_500

    elif aid == "preserve_cash_until_payment":
        vR = _linear_anchor_bp(max(0, avail), anchors.resilience_target_cents)
        vF = 0
        vG = 0
        vM = 8_000
        cE = 500

    elif aid == "contribute_savings_goal":
        amt = candidate.amount_cents
        # Goal progress anchored against step anchor + share of remaining goal
        raw_step_g = _linear_anchor_bp(amt, anchors.goal_progress_step_anchor_cents)
        vG = max(5_500, raw_step_g) if amt > 0 else 0
        # Resilience benefit is discounted by `reserve_goal_overlap_discount_bp` so the same euro is not double-counted
        raw_r = _linear_anchor_bp(amt * 5, anchors.resilience_target_cents)
        vR = (max(6_000, raw_r) * overlap_keep_bp) // BP_SCALE
        # Internal transfer / savings reservation is NOT profit (`vF = 0`)
        vF = 0
        vM = 8_000
        cE = 1_500

    elif aid == "build_reserve":
        amt = candidate.amount_cents
        raw_r = _linear_anchor_bp(amt * 5, anchors.resilience_target_cents)
        vR = max(6_500, raw_r) if amt > 0 else 0
        # Goal benefit is discounted by `reserve_goal_overlap_discount_bp` to avoid overlap double-counting
        raw_g = _linear_anchor_bp(amt, anchors.goal_progress_step_anchor_cents)
        vG = (max(4_500, raw_g) * overlap_keep_bp) // BP_SCALE
        vF = 0
        vM = 7_500
        cE = 1_500

    elif aid == "extra_debt_payment_one_off":
        int_saved = int(ev.get("interest_saved_cents") or 0)
        rem_cap = int(ev.get("remaining_capacity_cents") or 0)
        vF = _linear_anchor_bp(int_saved, anchors.financial_benefit_anchor_cents)
        vR = _linear_anchor_bp(rem_cap * 3, anchors.resilience_target_cents)
        vG = 2_500
        vM = 7_000
        cE = 2_500

    elif aid == "extra_debt_payment_recurring":
        int_saved = int(ev.get("interest_saved_cents") or 0)
        # Recurring commitments span multiple periods; scale financial benefit over compatible 12-month horizon
        vF = _linear_anchor_bp(int_saved, anchors.financial_benefit_anchor_cents)
        vR = 3_500
        vG = 3_000
        vM = 6_000
        cE = 3_500

    elif aid == "compare_repayment_strategies":
        av_i = int(ev.get("avalanche_interest_cents") or 0)
        sn_i = int(ev.get("snowball_interest_cents") or 0)
        diff = max(0, sn_i - av_i)
        vF = _linear_anchor_bp(diff, anchors.financial_benefit_anchor_cents)
        vR = 3_000
        vG = 2_000
        vM = 7_500
        cE = 1_000

    elif aid == "adjust_contribution":
        rem_cap = int(ev.get("remaining_capacity_cents") or 0)
        adj_amt = int(ev.get("adjusted_amount_cents") or candidate.amount_cents)
        vR = _linear_anchor_bp(rem_cap * 4, anchors.resilience_target_cents)
        vG = (_linear_anchor_bp(adj_amt, anchors.goal_progress_step_anchor_cents) * overlap_keep_bp) // BP_SCALE
        vF = 0
        vM = 6_500
        cE = 2_000

    elif aid == "adjust_goal_timeline":
        vR = 4_000
        vF = 0
        vG = 2_500
        vM = 7_000
        cE = 1_500

    elif aid == "review_recurring_charge":
        charge_cents = int(ev.get("recurring_charge_cents") or 0)
        # Annualized 12-month potential savings from reviewing a recurring monthly charge
        annual_cents = charge_cents * 12
        vF = _linear_anchor_bp(annual_cents, anchors.financial_benefit_anchor_cents)
        vR = 3_500
        vG = 2_000
        vM = 6_500
        cE = 3_000

    elif aid == "maintain_current_plan":
        has_planned = context.has_planned
        if has_planned or context.deferred:
            vR = 7_500
            vF = 0
            vG = 6_500 if has_planned else 2_000
            vM = 9_500
            cE = 0
        else:
            vR = 2_500
            vF = 0
            vG = 0
            vM = 8_000
            cE = 0

    return CriterionUtilities(
        vR_bp=_clamp_bp(vR),
        vF_bp=_clamp_bp(vF),
        vG_bp=_clamp_bp(vG),
        vM_bp=_clamp_bp(vM),
        cE_bp=_clamp_bp(cE),
    )


def compute_weighted_score_bp(
    utilities: CriterionUtilities,
    weights: ScoringWeights,
) -> tuple[int | None, bool]:
    """Stage E: Computes S(a) = wR*vR(a) + wF*vF(a) + wG*vG(a) + wM*vM(a) + wE*(1 - cE(a))
    scaled to basis points [0..10_000].

    Never converts unknown (`None`) to `0` or silently renormalizes differently per candidate.
    If any criterion with a positive weight is `None`, returns `(None, True)`.
    """
    pairs = [
        (weights.R, utilities.vR_bp),
        (weights.F, utilities.vF_bp),
        (weights.G, utilities.vG_bp),
        (weights.M, utilities.vM_bp),
        (
            weights.E,
            (BP_SCALE - utilities.cE_bp) if utilities.cE_bp is not None else None,
        ),
    ]
    for w, val in pairs:
        if w > 0 and val is None:
            return (None, True)

    numerator = sum(w * (val or 0) for w, val in pairs)
    return ((numerator + (BP_SCALE // 2)) // BP_SCALE, False)


def _tie_break_key(scored: ScoredCandidate) -> tuple:
    """Stable deterministic tie-breaking within the same urgency class (§10):
    1. Candidates with known scores before unknown-criterion candidates.
    2. Higher `weighted_score_bp` first.
    3. Lower `catalog_number` (canonical §9 order).
    4. Lexicographical `candidate_id`.
    """
    has_score = 0 if (scored.weighted_score_bp is not None and not scored.has_unknown_criterion) else 1
    score = scored.weighted_score_bp if scored.weighted_score_bp is not None else -1
    return (
        URGENCY_PRECEDENCE[scored.active_urgency_tier],
        has_score,
        -score,
        scored.candidate.catalog_number,
        scored.candidate.candidate_id,
    )


def _perturbed_weight_profiles(
    base: ScoringWeights,
    perturbation_ratio_bp: int,
) -> list[ tuple[str, ScoringWeights] ]:
    """Generates ±20% (or configured `perturbation_ratio_bp`) single-criterion swing profiles,
    renormalized identically across all candidates to `BP_SCALE = 10_000`.
    """
    dims = ("R", "F", "G", "M", "E")
    base_map = {"R": base.R, "F": base.F, "G": base.G, "M": base.M, "E": base.E}
    profiles: list[tuple[str, ScoringWeights]] = []

    for dim in dims:
        for sign, label in ((1, f"{dim}+20%"), (-1, f"{dim}-20%")):
            raw = dict(base_map)
            delta = (raw[dim] * perturbation_ratio_bp) // BP_SCALE
            raw[dim] = max(0, raw[dim] + sign * delta)
            total = sum(raw.values())
            if total <= 0:
                continue
            norm = {k: (v * BP_SCALE) // total for k, v in raw.items()}
            remainder = BP_SCALE - sum(norm.values())
            norm[dim] += remainder
            profiles.append((label, ScoringWeights(**norm)))
    return profiles


def run_sensitivity_analysis(
    tier_candidates: list[ScoredCandidate],
    scoring: ScoringPolicy,
) -> SensitivityReport:
    """Stage F: Checks whether the top recommendation in the active urgency class is stable
    under ±20% weight perturbations and minimum margin checks.
    """
    valid = [
        sc
        for sc in tier_candidates
        if sc.passed_hard_constraints and not sc.has_unknown_criterion and sc.weighted_score_bp is not None
    ]
    if not valid:
        return SensitivityReport(
            stable=False,
            perturbation_ratio_bp=scoring.sensitivity.perturbation_ratio_bp,
            fallback_triggered=True,
            fallback_reason="NO_SCORABLE_CANDIDATES_WITHOUT_UNKNOWN_CRITERIA",
        )

    ordered = sorted(valid, key=_tie_break_key)
    winner = ordered[0]
    runner_up = ordered[1] if len(ordered) > 1 else None
    margin = (
        (winner.weighted_score_bp or 0) - (runner_up.weighted_score_bp or 0)
        if runner_up is not None
        else BP_SCALE
    )

    # If there is only 1 candidate in the active urgency tier (e.g. urgent shortfall or single due_obligation),
    # it is unconditionally stable.
    if runner_up is None:
        return SensitivityReport(
            stable=True,
            perturbation_ratio_bp=scoring.sensitivity.perturbation_ratio_bp,
            baseline_winner_id=winner.candidate.candidate_id,
            baseline_runner_up_id=None,
            score_margin_bp=margin,
            flipped_under_trials=[],
            fallback_triggered=False,
        )

    flipped: list[str] = []
    for label, w_prof in _perturbed_weight_profiles(
        scoring.weights_bp,
        scoring.sensitivity.perturbation_ratio_bp,
    ):
        rescored: list[tuple[int, int, str]] = []
        for sc in valid:
            s_bp, _ = compute_weighted_score_bp(sc.utilities, w_prof)
            rescored.append(
                (
                    -(s_bp if s_bp is not None else -1),
                    sc.candidate.catalog_number,
                    sc.candidate.candidate_id,
                )
            )
        rescored.sort()
        top_id = rescored[0][2]
        if top_id != winner.candidate.candidate_id:
            flipped.append(f"{label}->{top_id}")

    is_stable = (len(flipped) == 0) and (margin >= scoring.sensitivity.min_top_margin_bp)
    fallback_reason = None
    if not is_stable:
        if flipped:
            fallback_reason = "RANKING_FLIPPED_UNDER_WEIGHT_PERTURBATION"
        else:
            fallback_reason = "TOP_SCORE_MARGIN_BELOW_THRESHOLD"

    return SensitivityReport(
        stable=is_stable,
        perturbation_ratio_bp=scoring.sensitivity.perturbation_ratio_bp,
        baseline_winner_id=winner.candidate.candidate_id,
        baseline_runner_up_id=runner_up.candidate.candidate_id,
        score_margin_bp=margin,
        flipped_under_trials=flipped,
        fallback_triggered=not is_stable,
        fallback_reason=fallback_reason,
    )


def evaluate_decision(
    state: State,
    today: date,
    policy: str = "fifth-of-available-v1",
    catalogue: ActionCataloguePolicy | None = None,
    scoring: ScoringPolicy | None = None,
    candidates_override: list[CandidateAction] | None = None,
) -> DecisionEvaluationSnapshot:
    """Executes the full Section 10 decision pipeline (Stages A through G) and returns
    a deterministic `DecisionEvaluationSnapshot`.
    """
    cat = catalogue if catalogue is not None else load_catalogue()
    scr = scoring if scoring is not None else load_scoring_policy()
    raw_candidates = (
        candidates_override
        if candidates_override is not None
        else generate_candidates(state, today, policy=policy, catalogue=cat)
    )

    reason_codes: list[str] = []
    scored_list: list[ScoredCandidate] = []

    for cand in raw_candidates:
        passed, hc_reasons = check_hard_constraints(cand, state, today)
        tier, urg_reasons = classify_candidate_urgency(cand, state, today, scr.anchors)
        utils = compute_utilities(cand, state, scr.anchors)
        score_bp, has_unknown = compute_weighted_score_bp(utils, scr.weights_bp)
        if has_unknown:
            reason_codes.append(f"UNKNOWN_CRITERION:{cand.action_id}")
        scored_list.append(
            ScoredCandidate(
                candidate=cand,
                passed_hard_constraints=passed,
                hard_constraint_reasons=hc_reasons,
                active_urgency_tier=tier,
                utilities=utils,
                has_unknown_criterion=has_unknown,
                weighted_score_bp=score_bp if passed else None,
            )
        )

    feasible = [sc for sc in scored_list if sc.passed_hard_constraints]
    if not feasible:
        # Fallback to baseline maintain_current_plan if all else was rejected
        baseline_candidates = [
            c for c in generate_candidates(state, today, policy=policy, catalogue=cat)
            if c.action_id == "maintain_current_plan"
        ]
        fallback_cand = baseline_candidates[0]
        utils = compute_utilities(fallback_cand, state, scr.anchors)
        score_bp, _ = compute_weighted_score_bp(utils, scr.weights_bp)
        feasible = [
            ScoredCandidate(
                candidate=fallback_cand,
                passed_hard_constraints=True,
                hard_constraint_reasons=[],
                active_urgency_tier="ordinary",
                utilities=utils,
                has_unknown_criterion=False,
                weighted_score_bp=score_bp,
            )
        ]

    # Determine highest urgency tier present among feasible candidates (shortfall > due_obligation > ordinary)
    best_tier_num = min(URGENCY_PRECEDENCE[sc.active_urgency_tier] for sc in feasible)
    active_tier: UrgencyClass = next(
        t for t, num in URGENCY_PRECEDENCE.items() if num == best_tier_num
    )
    reason_codes.append(f"ACTIVE_URGENCY_CLASS:{active_tier}")

    # Sort all scored candidates deterministically (feasible in active tier first, then lower tiers, then rejected)
    scored_list.sort(
        key=lambda sc: (
            0 if sc.passed_hard_constraints else 1,
            *_tie_break_key(sc),
        )
    )
    for idx, sc in enumerate(scored_list, start=1):
        if sc.passed_hard_constraints and not sc.has_unknown_criterion:
            sc.rank = idx

    tier_candidates = [sc for sc in scored_list if sc.passed_hard_constraints and sc.active_urgency_tier == active_tier]
    sensitivity = run_sensitivity_analysis(tier_candidates, scr)

    scorable_in_tier = [
        sc for sc in tier_candidates if not sc.has_unknown_criterion and sc.weighted_score_bp is not None
    ]

    if sensitivity.stable and scorable_in_tier:
        winner = scorable_in_tier[0]
        runner_up = scorable_in_tier[1] if len(scorable_in_tier) > 1 else None
        selected_cand = winner.candidate
        reason_codes.append(f"SELECTED_BY_MCDA:{selected_cand.action_id}")
    else:
        # Unstable ranking or unknown criteria -> preserve still-eligible current plan or ask one useful question
        reason_codes.append(f"SENSITIVITY_FALLBACK:{sensitivity.fallback_reason or 'UNSTABLE'}")
        runner_up = scorable_in_tier[0] if scorable_in_tier else None
        clarify_sc = next(
            (sc for sc in feasible if sc.candidate.action_id == "clarify_material_unknown"),
            None,
        )
        maintain_sc = next(
            (sc for sc in feasible if sc.candidate.action_id == "maintain_current_plan"),
            None,
        )
        if clarify_sc is not None:
            selected_cand = clarify_sc.candidate
            reason_codes.append("FALLBACK_TO_CLARIFY")
        elif maintain_sc is not None:
            selected_cand = maintain_sc.candidate
            reason_codes.append("FALLBACK_TO_MAINTAIN_CURRENT_PLAN")
        else:
            selected_cand = feasible[0].candidate

    s = state.snapshot
    avail = capacity(state) if s is not None else 0
    inputs_summary: dict[str, int | str | bool | None] = {
        "snapshot_present": s is not None,
        "as_of": s.as_of.isoformat() if s else None,
        "horizon": s.horizon.isoformat() if s else None,
        "cash_cents": s.cash if s else 0,
        "saved_cents": s.saved if s else 0,
        "protected_cents": s.protected if s else 0,
        "available_capacity_cents": avail,
        "obligations_count": len(s.obligations) if s else 0,
        "debts_count": len(state.debts),
        "planned_actions_count": sum(1 for a in state.actions if a.status == "planned"),
        "policy": policy,
    }

    return DecisionEvaluationSnapshot(
        evaluation_id=f"eval-{state.revision}-{uuid4().hex[:8]}",
        evaluated_on=today,
        state_revision=state.revision,
        catalogue_version=cat.version,
        scoring_version=scr.version,
        provisional_weights=scr.provisional,
        active_urgency_class=active_tier,
        reason_codes=reason_codes,
        inputs_summary=inputs_summary,
        selected_candidate_id=selected_cand.candidate_id,
        selected_action_id=selected_cand.action_id,
        selected_headline=selected_cand.headline,
        selected_summary=selected_cand.summary,
        selected_amount_cents=selected_cand.amount_cents,
        runner_up_candidate_id=runner_up.candidate.candidate_id if runner_up else None,
        runner_up_action_id=runner_up.candidate.action_id if runner_up else None,
        sensitivity=sensitivity,
        ranked_candidates=scored_list,
    )
