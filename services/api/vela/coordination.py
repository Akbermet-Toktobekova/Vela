"""Durable coordination and waiting state machine (§10, T16).

Specification guarantees (§10 'Coordination and waiting system'):
1. Creates a durable run with `run_id`, `financial_revision`, `preference_version`, `policy_version`,
   and an immutable `State` snapshot read consistently from the database.
2. Builds an explicit specialist dependency graph:
   - `cash_flow` (affordability & horizon projection) is always mandatory.
   - `debt` is mandatory whenever a debt exists (`len(state.debts) > 0`), a debt obligation exists,
     or `not state.snapshot.debt_known` (materially uncertain). Skipping requires a recorded
     `applicability_reason`; a failed or timed-out debt task NEVER means there is no debt.
   - `explanation` is optional (if failed or timed_out, falls back to a deterministic template).
3. Collects typed `SpecialistPacket` results with `run_id`, `financial_revision`, `status`
   (`succeeded`, `failed`, `timed_out`, `not_applicable`), `candidate_actions`,
   `calculator_references`, `evidence`, `missing_inputs`, and `duration_ms`.
4. Joins at a defined barrier:
   - Rejects mismatched `run_id` or `financial_revision` packets (`ValueError`).
   - Rejects partial packets (e.g. `succeeded` without `calculator_references`).
   - Deduplicates repeated specialist completion idempotently.
   - Enforces stage (`stage_deadline_ms`) and total (`total_deadline_ms`) deadlines.
   - Missing optional `explanation` falls back to deterministic template; missing/failed/timed_out
     required `cash_flow` or `debt` evidence transitions the run to `degraded_unavailable` and
     disables unverified actionable cards (retaining history).
5. Filters candidates against the 14-day `dismissed` cooldown (`DISMISSED_COOLDOWN_DAYS = 14`),
   unless a safety urgency class (`shortfall` or `due_obligation`) overrides ordinary stability.
6. Evaluates recalculation triggers (`check_recalculation_triggers`):
   - Cash drop > 20% (`CASH_DROP_THRESHOLD_BP = 2000`),
   - Planned step overdue > 7 days (`OVERDUE_STEP_DAYS = 7`),
   - Safety urgency change (e.g. new shortfall or due obligation),
   - Coalesces non-material updates so an existing valid recommendation is not spammed.
7. Separates `calculate()` and `publish()` stages so a crash between calculation and publication
   can be resumed from the durable store without re-running specialists or losing idempotency.
   Publication validates `financial_revision` atomically in `Store.publish_atomic` with a unique
   `publication_key` (`Conflict` on stale revision, idempotent return on duplicate key).
"""

from datetime import date, timedelta
from typing import Annotated, Literal
from uuid import uuid4
from pydantic import Field

from .catalogue import (
    CATALOGUE_PATH,
    CandidateAction,
    generate_candidates,
    load_catalogue,
)
from .debt import compare_and_simulate
from .decision import (
    DecisionEvaluationSnapshot,
    evaluate_decision,
    load_scoring_policy,
)
from .domain import Money, Record, State, capacity, eligibility
from .store import Conflict, Store

DISMISSED_COOLDOWN_DAYS = 14
CASH_DROP_THRESHOLD_BP = 2_000  # 20.00%
OVERDUE_STEP_DAYS = 7
DEFAULT_STAGE_DEADLINE_MS = 4_000
DEFAULT_TOTAL_DEADLINE_MS = 10_000

SpecialistName = Literal["cash_flow", "debt", "explanation"]
TaskStatus = Literal["pending", "succeeded", "failed", "timed_out", "not_applicable"]
RunStatus = Literal[
    "waiting",
    "ready_to_calculate",
    "calculated",
    "published",
    "degraded_unavailable",
    "superseded",
]


class DismissedRecord(Record):
    action_id: str = Field(min_length=1, max_length=80)
    dismissed_on: date
    target_id: str | None = None


class SpecialistNode(Record):
    specialist: SpecialistName
    mandatory: bool
    status: TaskStatus = "pending"
    applicability_reason: str | None = None
    stage_deadline_ms: Annotated[int, Field(strict=True, gt=0)] = DEFAULT_STAGE_DEADLINE_MS


class SpecialistPacket(Record):
    run_id: str = Field(min_length=1, max_length=80)
    financial_revision: Annotated[int, Field(strict=True, ge=0)]
    specialist: SpecialistName
    status: Literal["succeeded", "failed", "timed_out", "not_applicable"]
    applicability_reason: str | None = None
    candidate_actions: list[CandidateAction] = Field(default_factory=list)
    calculator_references: list[str] = Field(default_factory=list)
    evidence: dict[str, int | str | bool | None] = Field(default_factory=dict)
    missing_inputs: list[str] = Field(default_factory=list)
    explanation_text: str | None = None
    duration_ms: Annotated[int, Field(strict=True, ge=0)] = 0


class PublishedRecommendationCard(Record):
    publication_key: str = Field(min_length=1, max_length=120)
    run_id: str = Field(min_length=1, max_length=80)
    published_on: date
    financial_revision: int
    preference_version: str
    policy_version: str
    status: Literal["active", "degraded_unavailable"]
    actionable: bool
    action_id: str
    candidate_id: str
    amount_cents: Money = 0
    headline: str
    summary: str
    explanation_source: Literal["specialist", "template_fallback"] = "template_fallback"
    reason_codes: list[str] = Field(default_factory=list)
    evaluation_snapshot_id: str | None = None


class RecalculationTriggerResult(Record):
    should_recalculate: bool
    safety_override: bool = False
    coalesced: bool = False
    triggers: list[str] = Field(default_factory=list)


class CoordinationRun(Record):
    run_id: str = Field(min_length=1, max_length=80)
    owner: str = Field(default="local-demo", min_length=1, max_length=80)
    created_on: date
    financial_revision: int
    preference_version: str = "pref-v1"
    policy_version: str = "action-catalogue-v1+scoring-v1"
    stage_deadline_ms: int = DEFAULT_STAGE_DEADLINE_MS
    total_deadline_ms: int = DEFAULT_TOTAL_DEADLINE_MS
    elapsed_ms: int = 0
    status: RunStatus = "waiting"
    snapshot_state: State
    dismissed_actions: list[DismissedRecord] = Field(default_factory=list)
    dependency_graph: dict[SpecialistName, SpecialistNode]
    packets: dict[SpecialistName, SpecialistPacket] = Field(default_factory=dict)
    duplicate_packet_count: int = 0
    evaluation_snapshot: DecisionEvaluationSnapshot | None = None
    prepared_card: PublishedRecommendationCard | None = None
    failure_reasons: list[str] = Field(default_factory=list)


def build_dependency_graph(
    state: State,
    stage_deadline_ms: int = DEFAULT_STAGE_DEADLINE_MS,
) -> dict[SpecialistName, SpecialistNode]:
    """Builds the explicit specialist dependency graph for `state` (§10 step 2).

    - `cash_flow` is always mandatory.
    - `debt` is mandatory whenever a debt exists, a debt obligation is listed, or `debt_known` is False.
      Only when `debt_known` is True and zero debts/debt obligations exist is `debt` skipped with a
      recorded `applicability_reason`.
    - `explanation` is optional (template fallback on timeout/failure).
    """
    s = state.snapshot
    has_debt_items = bool(
        len(state.debts) > 0
        or (s is not None and any(o.kind == "debt" for o in s.obligations))
    )
    debt_uncertain = bool(s is None or not s.debt_known)
    debt_mandatory = has_debt_items or debt_uncertain

    debt_node = (
        SpecialistNode(
            specialist="debt",
            mandatory=True,
            status="pending",
            stage_deadline_ms=stage_deadline_ms,
        )
        if debt_mandatory
        else SpecialistNode(
            specialist="debt",
            mandatory=False,
            status="not_applicable",
            applicability_reason="Confirmed debt_known=True with zero active debts or debt obligations.",
            stage_deadline_ms=stage_deadline_ms,
        )
    )

    return {
        "cash_flow": SpecialistNode(
            specialist="cash_flow",
            mandatory=True,
            status="pending",
            stage_deadline_ms=stage_deadline_ms,
        ),
        "debt": debt_node,
        "explanation": SpecialistNode(
            specialist="explanation",
            mandatory=False,
            status="pending",
            stage_deadline_ms=stage_deadline_ms,
        ),
    }


def is_action_in_cooldown(
    action_id: str,
    today: date,
    dismissed: list[DismissedRecord],
    target_id: str | None = None,
    cooldown_days: int = DISMISSED_COOLDOWN_DAYS,
) -> bool:
    """Returns True if `action_id` (and optional `target_id`) was dismissed within `cooldown_days` (14 days)."""
    for rec in dismissed:
        if rec.action_id != action_id:
            continue
        if rec.target_id is not None and target_id is not None and rec.target_id != target_id:
            continue
        days_elapsed = (today - rec.dismissed_on).days
        if 0 <= days_elapsed < cooldown_days:
            return True
    return False


def check_recalculation_triggers(
    previous_state: State | None,
    current_state: State,
    today: date,
    active_card: PublishedRecommendationCard | None = None,
) -> RecalculationTriggerResult:
    """Evaluates whether a state or time change warrants replacing a still-valid recommendation (§10 step 8):
    - Cash drop > 20% (`CASH_DROP_THRESHOLD_BP = 2000`) -> material safety trigger.
    - Planned action overdue > 7 days (`OVERDUE_STEP_DAYS = 7`) -> time-based invalidation trigger.
    - Active projected shortfall (`capacity < 0`) or unclarified material unknown -> safety override.
    - Current active card's reservation exceeds current capacity -> safety override.
    - Otherwise, if an active card exists and the change is minor (e.g. cash changed <= 20% and no
      overdue step or shortfall), coalesces the update (`should_recalculate=False, coalesced=True`).
    """
    triggers: list[str] = []
    safety_override = False

    s_curr = current_state.snapshot
    avail_curr = capacity(current_state) if s_curr is not None else 0

    if s_curr is None:
        triggers.append("SNAPSHOT_MISSING")
        safety_override = True
    else:
        if avail_curr < 0:
            triggers.append("PROJECTED_SHORTFALL")
            safety_override = True
        if eligibility(current_state, today) is not None:
            triggers.append("ELIGIBILITY_CLARIFICATION_REQUIRED")
            safety_override = True

    if previous_state is not None and previous_state.snapshot is not None and s_curr is not None:
        prev_cash = previous_state.snapshot.cash
        curr_cash = s_curr.cash
        if prev_cash > 0 and curr_cash < prev_cash:
            drop_cents = prev_cash - curr_cash
            # Strictly greater than 20%: drop_cents * 10_000 > prev_cash * 2_000
            if drop_cents * 10_000 > prev_cash * CASH_DROP_THRESHOLD_BP:
                triggers.append("CASH_DROP_OVER_20_PERCENT")
                safety_override = True

    # Check if any planned step is overdue by > 7 days
    for action in current_state.actions:
        if action.status == "planned" and (today - action.created_on).days > OVERDUE_STEP_DAYS:
            triggers.append(f"PLANNED_STEP_OVERDUE_OVER_{OVERDUE_STEP_DAYS}_DAYS:{action.id}")

    if active_card is not None and active_card.status == "active":
        if active_card.amount_cents > 0 and avail_curr < active_card.amount_cents:
            triggers.append("ACTIVE_CARD_UNAFFORDABLE")
            safety_override = True

    if not triggers and active_card is not None and active_card.status == "active":
        return RecalculationTriggerResult(
            should_recalculate=False,
            safety_override=False,
            coalesced=True,
            triggers=[],
        )

    if not triggers and active_card is None:
        triggers.append("INITIAL_EVALUATION")

    return RecalculationTriggerResult(
        should_recalculate=True,
        safety_override=safety_override,
        coalesced=False,
        triggers=triggers,
    )


def build_cash_flow_packet(
    run: CoordinationRun,
    today: date,
    policy: str = "fifth-of-available-v1",
    duration_ms: int = 50,
) -> SpecialistPacket:
    """Deterministic helper that builds a valid `cash_flow` specialist packet for `run`."""
    state = run.snapshot_state
    cat = load_catalogue(CATALOGUE_PATH)
    cands = generate_candidates(state, today, policy=policy, catalogue=cat)
    cf_cands = [c for c in cands if c.category != "debt"]
    avail = capacity(state) if state.snapshot is not None else 0
    elig = eligibility(state, today)
    return SpecialistPacket(
        run_id=run.run_id,
        financial_revision=run.financial_revision,
        specialist="cash_flow",
        status="succeeded",
        candidate_actions=cf_cands,
        calculator_references=["projected_balances", "capacity", "suggested_amount"],
        evidence={
            "available_capacity_cents": avail,
            "snapshot_present": state.snapshot is not None,
        },
        missing_inputs=[elig[0]] if elig is not None else [],
        duration_ms=duration_ms,
    )


def build_debt_packet(
    run: CoordinationRun,
    today: date,
    policy: str = "fifth-of-available-v1",
    duration_ms: int = 50,
) -> SpecialistPacket:
    """Deterministic helper that builds a valid `debt` specialist packet for `run`."""
    state = run.snapshot_state
    node = run.dependency_graph["debt"]
    if not node.mandatory and node.status == "not_applicable":
        return SpecialistPacket(
            run_id=run.run_id,
            financial_revision=run.financial_revision,
            specialist="debt",
            status="not_applicable",
            applicability_reason=node.applicability_reason,
            duration_ms=0,
        )

    cat = load_catalogue(CATALOGUE_PATH)
    cands = generate_candidates(state, today, policy=policy, catalogue=cat)
    debt_cands = [c for c in cands if c.category == "debt"]
    sim = compare_and_simulate(state.debts, revision=state.revision)
    missing: list[str] = []
    if state.snapshot is not None and not state.snapshot.debt_known:
        missing.append("debt_known")
    if any(not d.terms_known for d in state.debts):
        missing.append("debt_terms")

    return SpecialistPacket(
        run_id=run.run_id,
        financial_revision=run.financial_revision,
        specialist="debt",
        status="succeeded",
        candidate_actions=debt_cands,
        calculator_references=["amortize_single_debt", "compare_and_simulate"],
        evidence={
            "debt_count": len(state.debts),
            "simulation_status": sim.status,
            "avalanche_interest_cents": sim.avalanche.total_interest_cents,
            "snowball_interest_cents": sim.snowball.total_interest_cents,
        },
        missing_inputs=missing,
        duration_ms=duration_ms,
    )


class Coordinator:
    """Durable state machine managing specialist runs, barrier joins, calculation, and atomic publication."""

    def __init__(self, store: Store, owner: str = "local-demo"):
        self.store = store
        self.owner = owner

    def start_run(
        self,
        today: date,
        preference_version: str = "pref-v1",
        policy_version: str = "action-catalogue-v1+scoring-v1",
        dismissed_actions: list[DismissedRecord] | None = None,
        stage_deadline_ms: int = DEFAULT_STAGE_DEADLINE_MS,
        total_deadline_ms: int = DEFAULT_TOTAL_DEADLINE_MS,
        run_id: str | None = None,
    ) -> CoordinationRun:
        """Step 1 & 2: Reads an immutable `State` snapshot consistently from `Store`, builds the
        dependency graph, and persists the initial `CoordinationRun`.
        """
        state = self.store.read(self.owner)
        rid = run_id or f"run-r{state.revision}-{uuid4().hex[:8]}"
        graph = build_dependency_graph(state, stage_deadline_ms=stage_deadline_ms)
        run = CoordinationRun(
            run_id=rid,
            owner=self.owner,
            created_on=today,
            financial_revision=state.revision,
            preference_version=preference_version,
            policy_version=policy_version,
            stage_deadline_ms=stage_deadline_ms,
            total_deadline_ms=total_deadline_ms,
            status="waiting",
            snapshot_state=state,
            dismissed_actions=list(dismissed_actions or []),
            dependency_graph=graph,
        )
        self._save(run)
        return run

    def load_run(self, run_id: str) -> CoordinationRun:
        raw = self.store.get_run(self.owner, run_id)
        if not raw:
            raise ValueError(f"Coordination run '{run_id}' not found.")
        return CoordinationRun.model_validate_json(raw)

    def _save(self, run: CoordinationRun):
        self.store.save_run(
            self.owner,
            run.run_id,
            run.financial_revision,
            run.status,
            run.model_dump_json(),
        )

    def submit_packet(self, run_id: str, packet: SpecialistPacket) -> CoordinationRun:
        """Step 3, 4 & 5: Records a typed specialist packet, validating `run_id`, `financial_revision`,
        completeness, and stage/total deadlines. Duplicate completion of the same specialist with the
        same status is handled idempotently without corrupting state.
        """
        run = self.load_run(run_id)
        if packet.run_id != run.run_id:
            raise ValueError(f"Packet run_id '{packet.run_id}' does not match '{run.run_id}'.")
        if packet.financial_revision != run.financial_revision:
            raise ValueError(
                f"Mismatched packet financial_revision {packet.financial_revision} != {run.financial_revision}."
            )
        if packet.specialist not in run.dependency_graph:
            raise ValueError(f"Unknown specialist '{packet.specialist}'.")

        # Duplicate completion check: if specialist already recorded a terminal packet, ignore duplicate idempotently
        if packet.specialist in run.packets:
            existing = run.packets[packet.specialist]
            if existing.status == packet.status and existing.evidence == packet.evidence:
                run.duplicate_packet_count += 1
                self._save(run)
                return run
            raise Conflict(f"Conflicting packet already recorded for specialist '{packet.specialist}'.")

        node = run.dependency_graph[packet.specialist]

        # Reject partial packets: a succeeded cash_flow or debt specialist must include calculator_references and evidence
        if packet.status == "succeeded" and packet.specialist in ("cash_flow", "debt"):
            if not packet.calculator_references or not packet.evidence:
                raise ValueError(
                    f"Partial packet rejected for '{packet.specialist}': missing calculator_references or evidence."
                )

        # A mandatory specialist cannot claim not_applicable without a recorded reason, and a mandatory debt
        # specialist when debt exists/is uncertain cannot be skipped as not_applicable
        if packet.status == "not_applicable":
            if node.mandatory:
                raise ValueError(
                    f"Mandatory specialist '{packet.specialist}' cannot return not_applicable."
                )
            if not packet.applicability_reason:
                raise ValueError("Skipping a specialist requires a recorded applicability_reason.")

        # Enforce stage deadline and total deadline (§10 step 5)
        effective_status: TaskStatus = packet.status
        if packet.duration_ms > node.stage_deadline_ms:
            effective_status = "timed_out"
            run.failure_reasons.append(
                f"STAGE_DEADLINE_EXCEEDED:{packet.specialist}:{packet.duration_ms}ms>{node.stage_deadline_ms}ms"
            )

        run.elapsed_ms = max(run.elapsed_ms, packet.duration_ms)
        if run.elapsed_ms > run.total_deadline_ms:
            effective_status = "timed_out"
            run.failure_reasons.append(
                f"TOTAL_DEADLINE_EXCEEDED:{run.elapsed_ms}ms>{run.total_deadline_ms}ms"
            )

        stored_packet = packet.model_copy(update={"status": effective_status})
        run.packets[packet.specialist] = stored_packet
        node.status = effective_status
        run.dependency_graph[packet.specialist] = node

        self._advance_join_state(run)
        self._save(run)
        return run

    def _advance_join_state(self, run: CoordinationRun):
        """Step 4 & 6: Checks the join barrier across all required specialists."""
        if run.status in ("calculated", "published", "superseded"):
            return

        for spec_name, node in run.dependency_graph.items():
            if not node.mandatory:
                continue
            if node.status in ("failed", "timed_out"):
                run.status = "degraded_unavailable"
                reason = f"MANDATORY_SPECIALIST_{node.status.upper()}:{spec_name}"
                if reason not in run.failure_reasons:
                    run.failure_reasons.append(reason)
                return

        # Check if all mandatory nodes have succeeded
        all_mandatory_ready = all(
            node.status in ("succeeded", "not_applicable")
            for node in run.dependency_graph.values()
            if node.mandatory
        )
        if all_mandatory_ready:
            run.status = "ready_to_calculate"

    def calculate(
        self,
        run_id: str,
        today: date,
        policy: str = "fifth-of-available-v1",
        publication_key: str | None = None,
    ) -> CoordinationRun:
        """Step 6 & 7 (part 1): Executes deterministic MCDA ranking over joined specialist packets
        and stores the `DecisionEvaluationSnapshot` and `prepared_card` on the durable run BEFORE
        publication. If a crash occurs after `calculate()`, `publish()` can resume directly from disk.
        """
        run = self.load_run(run_id)
        if run.status == "calculated" and run.prepared_card is not None:
            return run

        self._advance_join_state(run)
        pub_key = publication_key or f"pub-{run.run_id}-r{run.financial_revision}"

        # If any mandatory specialist is still pending (missing specialist at join point),
        # transition to degraded_unavailable — never bypass missing cash_flow or debt evidence with a score!
        missing_mandatory = [
            name
            for name, node in run.dependency_graph.items()
            if node.mandatory and node.status == "pending"
        ]
        if missing_mandatory:
            run.status = "degraded_unavailable"
            for name in missing_mandatory:
                code = f"MISSING_MANDATORY_SPECIALIST:{name}"
                if code not in run.failure_reasons:
                    run.failure_reasons.append(code)

        if run.status == "degraded_unavailable":
            # Step 6: On material failure, retain existing history, disable unverified action (`actionable=False`),
            # and offer a calm unavailable / retry state.
            run.prepared_card = PublishedRecommendationCard(
                publication_key=pub_key,
                run_id=run.run_id,
                published_on=today,
                financial_revision=run.financial_revision,
                preference_version=run.preference_version,
                policy_version=run.policy_version,
                status="degraded_unavailable",
                actionable=False,
                action_id="maintain_current_plan",
                candidate_id="degraded:unavailable",
                amount_cents=0,
                headline="Plan check temporarily unavailable",
                summary="We could not verify all cash-flow or debt details right now. Your current plan and history are safe; please retry shortly.",
                explanation_source="template_fallback",
                reason_codes=list(run.failure_reasons),
                evaluation_snapshot_id=None,
            )
            self._save(run)
            return run

        # Combine candidates from succeeded mandatory specialists
        combined_by_id: dict[str, CandidateAction] = {}
        for spec_name in ("cash_flow", "debt"):
            pkt = run.packets.get(spec_name)
            if pkt and pkt.status == "succeeded":
                for cand in pkt.candidate_actions:
                    combined_by_id[cand.candidate_id] = cand

        all_candidates = list(combined_by_id.values())

        # Apply 14-day cooldown filter for dismissed ordinary actions (safety actions in `shortfall`
        # or `due_obligation` classes and `maintain_current_plan` are never suppressed by cooldown)
        filtered_candidates: list[CandidateAction] = []
        cooldown_suppressed: list[str] = []
        for cand in all_candidates:
            if (
                cand.urgency_class == "ordinary"
                and cand.action_id != "maintain_current_plan"
                and is_action_in_cooldown(
                    cand.action_id,
                    today,
                    run.dismissed_actions,
                    target_id=cand.target_id,
                )
            ):
                cooldown_suppressed.append(cand.action_id)
                continue
            filtered_candidates.append(cand)

        cat = load_catalogue()
        scr = load_scoring_policy()
        eval_snap = evaluate_decision(
            run.snapshot_state,
            today,
            policy=policy,
            catalogue=cat,
            scoring=scr,
            candidates_override=filtered_candidates if filtered_candidates else None,
        )
        for suppressed_id in cooldown_suppressed:
            eval_snap.reason_codes.append(f"COOLDOWN_SUPPRESSED_14D:{suppressed_id}")

        # Optional explanation specialist: if succeeded and non-empty, use it; otherwise template fallback
        exp_pkt = run.packets.get("explanation")
        if exp_pkt and exp_pkt.status == "succeeded" and exp_pkt.explanation_text:
            summary_text = exp_pkt.explanation_text
            exp_source: Literal["specialist", "template_fallback"] = "specialist"
        else:
            summary_text = eval_snap.selected_summary
            exp_source = "template_fallback"
            if exp_pkt and exp_pkt.status in ("failed", "timed_out"):
                eval_snap.reason_codes.append(f"EXPLANATION_FALLBACK_ON_{exp_pkt.status.upper()}")

        run.evaluation_snapshot = eval_snap
        run.prepared_card = PublishedRecommendationCard(
            publication_key=pub_key,
            run_id=run.run_id,
            published_on=today,
            financial_revision=run.financial_revision,
            preference_version=run.preference_version,
            policy_version=run.policy_version,
            status="active",
            actionable=True,
            action_id=eval_snap.selected_action_id,
            candidate_id=eval_snap.selected_candidate_id,
            amount_cents=eval_snap.selected_amount_cents,
            headline=eval_snap.selected_headline,
            summary=summary_text,
            explanation_source=exp_source,
            reason_codes=list(eval_snap.reason_codes),
            evaluation_snapshot_id=eval_snap.evaluation_id,
        )
        run.status = "calculated"
        self._save(run)
        return run

    def publish(
        self,
        run_id: str,
        publication_key: str | None = None,
    ) -> PublishedRecommendationCard:
        """Step 7 (part 2): Publishes the calculated recommendation atomically ONLY if the store's
        current financial revision still matches `run.financial_revision`. Uses `publication_key`
        for idempotent deduplication under retries.
        """
        run = self.load_run(run_id)
        if run.prepared_card is None:
            raise ValueError("Run must be calculated before publication.")

        card = run.prepared_card
        if publication_key is not None and publication_key != card.publication_key:
            card = card.model_copy(update={"publication_key": publication_key})
            run.prepared_card = card

        def updated_run_payload() -> str:
            run.status = "published"
            return run.model_dump_json()

        try:
            stored_dict = self.store.publish_atomic(
                owner=self.owner,
                run_id=run.run_id,
                publication_key=card.publication_key,
                expected_revision=run.financial_revision,
                run_payload_fn=updated_run_payload,
                publication_payload=card.model_dump_json(),
            )
        except Conflict:
            run.status = "superseded"
            if "SUPERSEDED_BY_NEWER_REVISION" not in run.failure_reasons:
                run.failure_reasons.append("SUPERSEDED_BY_NEWER_REVISION")
            self._save(run)
            raise

        return PublishedRecommendationCard.model_validate(stored_dict)
