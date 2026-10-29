"""Pure weighted decisions over current account facts, never legacy money."""
from datetime import date, timedelta
import hashlib
import json
from typing import Literal

from pydantic import Field

from .catalogue import CandidateAction, load_catalogue
from .decision import (BP_SCALE, CriterionUtilities, ScoredCandidate, ScoringPolicy,
                       SensitivityReport, UtilityContext, compute_utilities_from_context,
                       compute_weighted_score_bp, load_scoring_policy, run_sensitivity_analysis)
from .domain import Record, suggested_amount
from .planning import canonical_plan_facts, chosen_account


ENGINE_VERSION = 'canonical-account-mcda-v1'
AMOUNT_POLICY = 'fifth-of-available-v1-provisional'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


class CriterionContribution(Record):
    weight_bp: int
    utility_bp: int | None
    weighted_numerator: int | None
    denominator: int = BP_SCALE


class CandidateEvaluation(Record):
    score: ScoredCandidate
    contributions: dict[str, CriterionContribution]
    reason_codes: list[str] = Field(default_factory=list)


class CanonicalDecision(Record):
    engine_version: str = ENGINE_VERSION
    as_of: date
    state_revision: int
    currency: Literal['EUR'] = 'EUR'
    input_fingerprint: str
    policy_fingerprint: str
    catalogue_fingerprint: str
    inputs: dict
    policy: ScoringPolicy
    catalogue_version: str
    amount_policy: str = AMOUNT_POLICY
    outcome: Literal['clarify', 'shortfall', 'planned', 'maintain', 'goal_reached', 'save']
    message: str
    selected_candidate_id: str
    selected_action_id: str
    selected_amount_cents: int | None
    can_reserve: bool
    preserved_step_id: str | None = None
    sensitivity: SensitivityReport
    reason_codes: list[str]
    candidates: list[CandidateEvaluation]
    unavailable_candidates: dict[str, str]


def recommendation_identity(decision):
    """Stable relevant-input identity; shared revision is calculation metadata."""
    return 'canonical-'+fingerprint({
        'engine_version': decision.engine_version,
        'input_fingerprint': decision.input_fingerprint,
        'policy_fingerprint': decision.policy_fingerprint,
        'catalogue_fingerprint': decision.catalogue_fingerprint,
        'amount_policy': decision.amount_policy,
    })


def contributions(utilities, weights):
    values = {'R': utilities.vR_bp, 'F': utilities.vF_bp, 'G': utilities.vG_bp,
              'M': utilities.vM_bp,
              'E': None if utilities.cE_bp is None else BP_SCALE-utilities.cE_bp}
    return {key: CriterionContribution(weight_bp=getattr(weights, key), utility_bp=value,
                weighted_numerator=None if value is None else value*getattr(weights, key))
            for key, value in values.items()}


def evaluate_account_plan(state, today, *, scoring=None, catalogue=None):
    """One immutable supported decision; no Store access or state mutation.

    The only cash authority is the selected current EUR account. Debt coverage
    is not evidence of known debt terms; imported/expected/FX/legacy money is
    deliberately absent from the input bundle and supported candidate set.
    """
    policy = scoring if scoring is not None else load_scoring_policy()
    catalogue = catalogue if catalogue is not None else load_catalogue()
    facts, account = canonical_plan_facts(state, today), chosen_account(state)
    plan = state.personal.planning
    details = state.personal.profile_details
    planned = [step for step in plan.steps if step.status == 'planned']
    active = planned[0] if planned else None
    inputs = {
        'state_revision': state.revision, 'as_of': today.isoformat(),
        'account': account.model_dump(mode='json') if account else None,
        'planning': plan.model_dump(mode='json'),
        'available_cents': facts.available, 'known_bills_cents': facts.bills,
        'reserved_cents': facts.reserved, 'earmarked_cents': facts.saved,
        'needs_input': facts.needs_input,
        'preference_version': details.preference_version if details else 0,
        'income_input_version': details.income_input_version if details else 0,
        'debt_terms': None, 'recurring_affordability': None,
        'source': 'confirmed_current_account_and_explicit_plan',
    }
    context = UtilityContext(facts.available, bool(planned), plan.deferred)
    definitions = {action.id: action for action in catalogue.actions}
    candidates, reasons = [], []
    unavailable = {action.id: 'UNSUPPORTED_BY_CURRENT_CANONICAL_FACTS' for action in catalogue.actions}
    for action_id in ('prepare_required_debt', 'extra_debt_payment_one_off',
                      'extra_debt_payment_recurring', 'compare_repayment_strategies'):
        unavailable[action_id] = 'DEBT_TERMS_NOT_ESTABLISHED_BY_PAYMENT_COVERAGE'
    unavailable['build_reserve'] = 'GOAL_TYPE_NOT_CONFIRMED_NO_NAME_INFERENCE'
    unavailable['review_recurring_charge'] = 'NO_CONFIRMED_RECURRING_BENEFIT_OR_COMPARABLE_HORIZON'

    def add(action_id, *, tier='ordinary', amount=0, headline=None, summary=None,
            evidence=None, reserves=False, target=None, rejection=None):
        definition = definitions[action_id]
        candidate = CandidateAction(candidate_id='canonical-'+action_id+(('-'+target) if target else ''),
            action_id=action_id, catalog_number=definition.catalog_number, title=definition.title,
            category=definition.category, urgency_class=tier, amount_cents=amount,
            reserves_cash=reserves, target_id=target, lesson_id=definition.lesson_id,
            related_lesson_ids=definition.related_lesson_ids,
            headline=headline or definition.title, summary=summary or definition.effects.description,
            cta_label=definition.presentation.cta_label, disclaimer=definition.presentation.disclaimer,
            policy_version=catalogue.version, calculation_evidence=evidence or {})
        hard = list(rejection or [])
        if reserves:
            if facts.needs_input is not None: hard.append('HARD_REJECT_UNCLARIFIED_INPUTS')
            if facts.available is None: hard.append('HARD_REJECT_UNKNOWN_CAPACITY')
            elif amount > facts.available: hard.append('HARD_REJECT_EXCEEDS_CANONICAL_CAPACITY')
            if amount <= 0: hard.append('HARD_REJECT_ZERO_RESERVATION')
            if planned or plan.deferred: hard.append('HARD_REJECT_ACCEPTED_OR_DEFERRED_PLAN')
        utilities = compute_utilities_from_context(candidate, context, policy.anchors)
        score, unknown = compute_weighted_score_bp(utilities, policy.weights_bp)
        scored = ScoredCandidate(candidate=candidate, passed_hard_constraints=not hard,
            hard_constraint_reasons=hard, active_urgency_tier=tier, utilities=utilities,
            has_unknown_criterion=unknown, weighted_score_bp=score if not hard else None)
        candidates.append(CandidateEvaluation(score=scored,
            contributions=contributions(utilities, policy.weights_bp),
            reason_codes=hard+(['UNKNOWN_CRITERION'] if unknown else [])))
        unavailable.pop(action_id, None)
        return scored

    baseline = add('maintain_current_plan')
    outcome, message = 'maintain', 'Keep your money available; no new action is required.'
    forced = None
    if facts.needs_input:
        outcome, message = 'clarify', facts.needs_input
        forced = add('clarify_material_unknown', tier='due_obligation', summary=message)
        reasons.append('MATERIAL_INPUT_REQUIRED')
    elif facts.available < 0:
        outcome, message = 'shortfall', 'Review your confirmed commitments and allocations before a new savings step.'
        forced = add('pause_optional_allocation', tier='shortfall', summary=message,
                     evidence={'paused_amount_cents': facts.reserved, 'shortfall_cents': -facts.available})
        reasons.append('CANONICAL_SHORTFALL')
    elif active:
        outcome, message = 'planned', 'Keep your accepted step. No new reservation has been made.'
        forced = baseline
        reasons.append('PRESERVE_ACCEPTED_STEP')
    elif plan.deferred:
        forced, message = baseline, 'Your step is deferred. Your money remains available.'
        reasons.append('PRESERVE_DEFERRED_PLAN')
    elif plan.goal is None:
        forced, message = baseline, 'No goal is required. Keep your money available.'
        reasons.append('NO_OPTIONAL_GOAL')
    elif plan.goal.saved >= plan.goal.target:
        forced, outcome, message = baseline, 'goal_reached', 'Your recorded goal allocation has reached its target.'
        reasons.append('GOAL_REACHED')
    else:
        amount = suggested_amount(facts.available, plan.goal.target-plan.goal.saved)
        if amount:
            add('contribute_savings_goal', amount=amount, reserves=True,
                evidence={'available_cents': facts.available, 'goal_remaining_cents': plan.goal.target-plan.goal.saved})
        else:
            unavailable['contribute_savings_goal'] = 'NO_SUPPORTED_POSITIVE_STEP'
        for bill in plan.bills:
            if bill.status != 'unpaid': continue
            if bill.due > min(plan.horizon, today+timedelta(days=policy.anchors.imminent_obligation_window_days)):
                continue
            if facts.available*BP_SCALE <= bill.amount*policy.anchors.imminent_obligation_tight_capacity_ratio_bp:
                add('preserve_cash_until_payment', tier='due_obligation', target=bill.id,
                    summary='Keep the confirmed bill protected. Its amount is already counted in your plan.',
                    evidence={'already_in_obligations': True, 'bill_amount_cents': bill.amount,
                              'due_date': bill.due.isoformat()})

    tier_order = {'shortfall': 0, 'due_obligation': 1, 'ordinary': 2}
    eligible = [entry.score for entry in candidates if entry.score.passed_hard_constraints]
    best = min(tier_order[item.active_urgency_tier] for item in eligible)
    tier = [item for item in eligible if tier_order[item.active_urgency_tier] == best]
    sensitivity = run_sensitivity_analysis(tier, policy)
    if forced is not None:
        selected = forced
    elif not sensitivity.stable:
        selected = baseline
        reasons.append('SENSITIVITY_FALLBACK_TO_MAINTAIN')
    else:
        selected = sorted(tier, key=lambda item: (-(item.weighted_score_bp or 0),
                          item.candidate.catalog_number, item.candidate.candidate_id))[0]
    if forced is None:
        if selected.candidate.action_id == 'contribute_savings_goal':
            outcome, message = 'save', 'A provisional weighted suggestion based on your confirmed account and plan.'
        elif selected.candidate.action_id == 'preserve_cash_until_payment':
            outcome, message = 'maintain', selected.candidate.summary
            reasons.append('PRESERVE_ALREADY_COUNTED_REQUIRED_BILL')
    reasons.extend(['SELECTED:'+selected.candidate.action_id, 'SCORING_POLICY:'+policy.version,
                    'WEIGHTS_PROVISIONAL' if policy.provisional else 'POLICY_STATUS:'+policy.domain_review_status])
    ordered = sorted(candidates, key=lambda entry: (not entry.score.passed_hard_constraints,
        tier_order[entry.score.active_urgency_tier], entry.score.has_unknown_criterion,
        -(entry.score.weighted_score_bp or 0), entry.score.candidate.catalog_number,
        entry.score.candidate.candidate_id))
    for rank, entry in enumerate(ordered, 1): entry.score.rank = rank
    return CanonicalDecision(as_of=today, state_revision=state.revision,
        input_fingerprint=fingerprint({key: value for key, value in inputs.items() if key != 'state_revision'}),
        policy_fingerprint=fingerprint(policy.model_dump(mode='json')),
        catalogue_fingerprint=fingerprint(catalogue.model_dump(mode='json')), inputs=inputs,
        policy=policy.model_copy(deep=True), catalogue_version=catalogue.version,
        outcome=outcome, message=message, selected_candidate_id=selected.candidate.candidate_id,
        selected_action_id=selected.candidate.action_id,
        selected_amount_cents=selected.candidate.amount_cents if outcome == 'save' else None,
        can_reserve=outcome == 'save' and selected.passed_hard_constraints,
        preserved_step_id=active.id if active and outcome == 'planned' else None,
        sensitivity=sensitivity, reason_codes=reasons, candidates=ordered,
        unavailable_candidates=unavailable)
