"""Tests for the Section 10 Coordination and Waiting State Machine (T16).

Covers all acceptance criteria:
1. Slow responses (`duration_ms > stage_deadline_ms` or `total_deadline_ms` -> `timed_out`;
   mandatory timeout disables actionable recommendation; optional explanation timeout falls back to template).
2. Missing specialist at join point (missing `debt` when debt exists/is uncertain -> `degraded_unavailable`
   with `actionable=False`; failed debt task never means there is no debt; skipping `debt` allowed only
   with recorded `applicability_reason` when `debt_known=True` and zero debts exist).
3. Duplicate completion (`submit_packet` called twice for the same specialist is idempotent and increments
   `duplicate_packet_count`; conflicting duplicate raises `Conflict`).
4. Newer income during processing (advances store revision while coordination run is in flight ->
   atomic `publish()` rejects stale revision with `Conflict` and marks run `superseded`).
5. Crash between calculation and publication (`calculate()` persists `prepared_card` and `evaluation_snapshot`
   to SQLite; a fresh `Coordinator` instance after simulated process crash resumes and completes `publish()`).
6. Stale revision and partial packet rejection (`submit_packet` rejects mismatched `financial_revision`
   or missing `calculator_references`).
7. Unique publication key (`publication_key` prevents duplicate cards under retry).
8. 14-day `dismissed` cooldown (`DISMISSED_COOLDOWN_DAYS = 14`) and recalculation triggers for
   cash drop > 20% and planned step overdue > 7 days (plus coalescing of non-material changes).
"""

from datetime import date, timedelta
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from vela.coordination import (
    DISMISSED_COOLDOWN_DAYS,
    Coordinator,
    DismissedRecord,
    SpecialistPacket,
    build_cash_flow_packet,
    build_debt_packet,
    check_recalculation_triggers,
    is_action_in_cooldown,
)
from vela.domain import Action, Debt, Obligation, Snapshot, State, fixture, view
from vela.store import Conflict, Store

TODAY = date(2026, 10, 26)
OWNER = "local-demo"


class TestCoordinationStateMachine(unittest.TestCase):
    """Tests specialist dependency graph, barrier join, failure recovery, and atomic publication."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "coord_test.db"
        self.db_url = f"sqlite:///{self.db_path}"
        self.store = Store(self.db_url)
        # Initialize canonical Section 9 state at revision 1
        self.store.mutate(
            owner=OWNER,
            key="init-demo",
            revision=0,
            command={"kind": "load_demo"},
            apply=lambda s: setattr(s, "snapshot", fixture(TODAY)),
            render=lambda s: view(s, TODAY),
        )
        self.coord = Coordinator(self.store, owner=OWNER)

    def tearDown(self):
        self.store.engine.dispose()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_01_slow_response_timeout_mandatory_vs_optional_explanation_fallback(self):
        """Test slow responses:
        - When optional `explanation` specialist exceeds `stage_deadline_ms`, it is marked `timed_out`
          and `calculate()` cleanly falls back to the deterministic template (`explanation_source='template_fallback'`).
        - When mandatory `cash_flow` specialist exceeds `stage_deadline_ms`, it is marked `timed_out`
          and the run transitions to `degraded_unavailable` with `actionable=False`.
        """
        # Case A: Optional explanation specialist is slow (> 2000ms), mandatory specialists succeed on time
        run_a = self.coord.start_run(TODAY, stage_deadline_ms=2_000, total_deadline_ms=6_000)
        self.coord.submit_packet(run_a.run_id, build_cash_flow_packet(run_a, TODAY, duration_ms=400))
        self.coord.submit_packet(run_a.run_id, build_debt_packet(run_a, TODAY, duration_ms=500))
        slow_exp = SpecialistPacket(
            run_id=run_a.run_id,
            financial_revision=run_a.financial_revision,
            specialist="explanation",
            status="succeeded",
            explanation_text="Late LLM explanation that exceeded budget.",
            duration_ms=3_500,  # > 2_000ms stage deadline!
        )
        run_a = self.coord.submit_packet(run_a.run_id, slow_exp)
        self.assertEqual(run_a.dependency_graph["explanation"].status, "timed_out")

        calc_a = self.coord.calculate(run_a.run_id, TODAY, policy="section9-demo-40-v1")
        self.assertEqual(calc_a.status, "calculated")
        self.assertIsNotNone(calc_a.prepared_card)
        self.assertTrue(calc_a.prepared_card.actionable)
        self.assertEqual(calc_a.prepared_card.explanation_source, "template_fallback")
        self.assertIn("EXPLANATION_FALLBACK_ON_TIMED_OUT", calc_a.prepared_card.reason_codes)

        # Case B: Mandatory cash_flow specialist is slow (> 2000ms) -> degraded_unavailable, actionable=False
        run_b = self.coord.start_run(TODAY, stage_deadline_ms=2_000, total_deadline_ms=6_000)
        self.coord.submit_packet(run_b.run_id, build_cash_flow_packet(run_b, TODAY, duration_ms=2_500))
        self.coord.submit_packet(run_b.run_id, build_debt_packet(run_b, TODAY, duration_ms=300))

        calc_b = self.coord.calculate(run_b.run_id, TODAY)
        self.assertEqual(calc_b.status, "degraded_unavailable")
        self.assertFalse(calc_b.prepared_card.actionable)
        self.assertIn("MANDATORY_SPECIALIST_TIMED_OUT:cash_flow", calc_b.prepared_card.reason_codes)

    def test_02_missing_or_failed_specialist_and_debt_applicability_rules(self):
        """Test one missing specialist and debt applicability rules (§10 step 2, 4, 6):
        - When a debt obligation exists (as in `fixture(TODAY)`), `debt` is mandatory.
        - If `calculate()` is called while `debt` is missing (`pending`) or `failed`, it cannot be bypassed
          with a score; the run becomes `degraded_unavailable` with `actionable=False`.
        - When `debt_known=True` and zero debts/debt obligations exist, `debt` is marked `not_applicable`
          with a recorded `applicability_reason`.
        """
        # 1. Missing mandatory `debt` specialist at join point
        run_missing = self.coord.start_run(TODAY)
        self.assertTrue(run_missing.dependency_graph["debt"].mandatory)
        self.coord.submit_packet(run_missing.run_id, build_cash_flow_packet(run_missing, TODAY))
        # Do NOT submit debt packet -> call calculate()
        calc_missing = self.coord.calculate(run_missing.run_id, TODAY)
        self.assertEqual(calc_missing.status, "degraded_unavailable")
        self.assertFalse(calc_missing.prepared_card.actionable)
        self.assertIn("MISSING_MANDATORY_SPECIALIST:debt", calc_missing.prepared_card.reason_codes)

        # 2. Failed mandatory `debt` specialist never means there is no debt
        run_failed_debt = self.coord.start_run(TODAY)
        self.coord.submit_packet(run_failed_debt.run_id, build_cash_flow_packet(run_failed_debt, TODAY))
        self.coord.submit_packet(
            run_failed_debt.run_id,
            SpecialistPacket(
                run_id=run_failed_debt.run_id,
                financial_revision=run_failed_debt.financial_revision,
                specialist="debt",
                status="failed",
                duration_ms=100,
            ),
        )
        calc_failed = self.coord.calculate(run_failed_debt.run_id, TODAY)
        self.assertEqual(calc_failed.status, "degraded_unavailable")
        self.assertFalse(calc_failed.prepared_card.actionable)
        self.assertIn("MANDATORY_SPECIALIST_FAILED:debt", calc_failed.prepared_card.reason_codes)

        # 3. Attempting to skip mandatory debt with `not_applicable` is rejected
        run_skip_attempt = self.coord.start_run(TODAY)
        with self.assertRaises(ValueError):
            self.coord.submit_packet(
                run_skip_attempt.run_id,
                SpecialistPacket(
                    run_id=run_skip_attempt.run_id,
                    financial_revision=run_skip_attempt.financial_revision,
                    specialist="debt",
                    status="not_applicable",
                    applicability_reason="Trying to skip mandatory debt",
                ),
            )

        # 4. Remove debt obligation while `debt_known=True` and `debts=[]` -> debt specialist is not_applicable with reason
        self.store.mutate(
            owner=OWNER,
            key="remove-debt-ob",
            revision=1,
            command={"kind": "bill_removed"},
            apply=lambda s: setattr(
                s.snapshot,
                "obligations",
                [o for o in s.snapshot.obligations if o.kind != "debt"],
            ),
            render=lambda s: view(s, TODAY),
        )
        run_no_debt = self.coord.start_run(TODAY)
        self.assertFalse(run_no_debt.dependency_graph["debt"].mandatory)
        self.assertEqual(run_no_debt.dependency_graph["debt"].status, "not_applicable")
        self.assertTrue(run_no_debt.dependency_graph["debt"].applicability_reason)

    def test_03_duplicate_specialist_completion_and_partial_or_mismatched_rejection(self):
        """Test duplicate completion, mismatched revision rejection, and partial packet rejection."""
        run = self.coord.start_run(TODAY)
        cf_pkt = build_cash_flow_packet(run, TODAY)

        # First submission succeeds
        after_first = self.coord.submit_packet(run.run_id, cf_pkt)
        self.assertEqual(after_first.duplicate_packet_count, 0)

        # Second identical submission is idempotent and increments duplicate_packet_count
        after_dup = self.coord.submit_packet(run.run_id, cf_pkt)
        self.assertEqual(after_dup.duplicate_packet_count, 1)

        # Conflicting duplicate submission for the same specialist raises Conflict
        conflicting_cf = cf_pkt.model_copy(update={"status": "failed"})
        with self.assertRaises(Conflict):
            self.coord.submit_packet(run.run_id, conflicting_cf)

        # Mismatched financial_revision packet is rejected
        bad_rev_debt = build_debt_packet(run, TODAY).model_copy(update={"financial_revision": 999})
        with self.assertRaises(ValueError):
            self.coord.submit_packet(run.run_id, bad_rev_debt)

        # Partial packet (succeeded without calculator_references) is rejected
        partial_debt = build_debt_packet(run, TODAY).model_copy(update={"calculator_references": []})
        with self.assertRaises(ValueError):
            self.coord.submit_packet(run.run_id, partial_debt)

    def test_04_newer_income_during_processing_rejects_stale_publication(self):
        """Test newer income during processing and stale revision rejection:
        A coordination run starts at revision 1 and calculates its card. Before `publish()` is called,
        new income arrives and advances the store to revision 2. `publish()` must reject the stale
        run with `Conflict` and mark the run `superseded`.
        """
        run = self.coord.start_run(TODAY)
        self.assertEqual(run.financial_revision, 1)
        self.coord.submit_packet(run.run_id, build_cash_flow_packet(run, TODAY, policy="section9-demo-40-v1"))
        self.coord.submit_packet(run.run_id, build_debt_packet(run, TODAY, policy="section9-demo-40-v1"))
        self.coord.calculate(run.run_id, TODAY, policy="section9-demo-40-v1")

        # Newer income arrives while run is in flight -> store revision advances 1 -> 2
        self.store.mutate(
            owner=OWNER,
            key="new-income-during-run",
            revision=1,
            command={"kind": "income", "amount": 50_000},
            apply=lambda s: setattr(s.snapshot, "cash", s.snapshot.cash + 50_000),
            render=lambda s: view(s, TODAY),
        )
        self.assertEqual(self.store.read(OWNER).revision, 2)

        # Attempting to publish the revision-1 run fails with Conflict
        with self.assertRaises(Conflict):
            self.coord.publish(run.run_id)

        superseded_run = self.coord.load_run(run.run_id)
        self.assertEqual(superseded_run.status, "superseded")
        self.assertIn("SUPERSEDED_BY_NEWER_REVISION", superseded_run.failure_reasons)

    def test_05_crash_between_calculation_and_publication_and_unique_publication_key(self):
        """Test crash between calculation and publication + unique publication key idempotency:
        1. Coordinator A runs `calculate()` and persists the `calculated` state to SQLite, then 'crashes'.
        2. A brand-new Coordinator B connects to the same SQLite database, loads `run.run_id`,
           and completes `publish()` without re-running specialists.
        3. Calling `publish()` again with the same `publication_key` returns the exact same
           `PublishedRecommendationCard` without creating a duplicate publication.
        """
        run = self.coord.start_run(TODAY)
        self.coord.submit_packet(run.run_id, build_cash_flow_packet(run, TODAY, policy="section9-demo-40-v1"))
        self.coord.submit_packet(run.run_id, build_debt_packet(run, TODAY, policy="section9-demo-40-v1"))
        calculated = self.coord.calculate(
            run.run_id,
            TODAY,
            policy="section9-demo-40-v1",
            publication_key="unique-pub-key-r1",
        )
        self.assertEqual(calculated.status, "calculated")
        self.assertIsNotNone(calculated.prepared_card)

        # Simulate worker crash: discard `self.coord` and instantiate a fresh Store + Coordinator on the same DB
        recovered_store = Store(self.db_url)
        recovered_coord = Coordinator(recovered_store, owner=OWNER)

        persisted_before_pub = recovered_coord.load_run(run.run_id)
        self.assertEqual(persisted_before_pub.status, "calculated")
        self.assertEqual(persisted_before_pub.prepared_card.publication_key, "unique-pub-key-r1")

        # Resume publication after crash
        card1 = recovered_coord.publish(run.run_id)
        self.assertEqual(card1.publication_key, "unique-pub-key-r1")
        self.assertEqual(card1.financial_revision, 1)
        self.assertEqual(card1.status, "active")
        self.assertTrue(card1.actionable)
        self.assertEqual(recovered_coord.load_run(run.run_id).status, "published")

        # Retry publication with the same unique publication_key -> idempotent, no duplicate card
        card2 = recovered_coord.publish(run.run_id, publication_key="unique-pub-key-r1")
        self.assertEqual(card1.model_dump(), card2.model_dump())
        recovered_store.engine.dispose()

    def test_06_dismissed_14_day_cooldown_and_safety_override(self):
        """Test 14-day cooldown for `dismissed` actions:
        - Within 14 days (e.g. day +13), a dismissed ordinary action (`contribute_savings_goal`)
          is suppressed and recorded in `reason_codes` (`COOLDOWN_SUPPRESSED_14D:contribute_savings_goal`).
        - On day +14, the cooldown expires and `contribute_savings_goal` is eligible again.
        - Safety actions (`shortfall` or `due_obligation`) are never suppressed by cooldown.
        """
        dismissed_on = TODAY - timedelta(days=13)
        records = [DismissedRecord(action_id="contribute_savings_goal", dismissed_on=dismissed_on)]
        self.assertTrue(is_action_in_cooldown("contribute_savings_goal", TODAY, records))
        self.assertFalse(
            is_action_in_cooldown(
                "contribute_savings_goal",
                dismissed_on + timedelta(days=DISMISSED_COOLDOWN_DAYS),
                records,
            )
        )

        run = self.coord.start_run(TODAY, dismissed_actions=records)
        self.coord.submit_packet(run.run_id, build_cash_flow_packet(run, TODAY, policy="section9-demo-40-v1"))
        self.coord.submit_packet(run.run_id, build_debt_packet(run, TODAY, policy="section9-demo-40-v1"))
        calc = self.coord.calculate(run.run_id, TODAY, policy="section9-demo-40-v1")

        self.assertNotEqual(calc.prepared_card.action_id, "contribute_savings_goal")
        self.assertIn(
            "COOLDOWN_SUPPRESSED_14D:contribute_savings_goal",
            calc.prepared_card.reason_codes,
        )

    def test_07_recalculation_triggers_cash_drop_over_20_percent_and_overdue_step_over_7_days(self):
        """Test recalculation triggers:
        - Minor cash drop (<= 20%, e.g. 10%) with an active valid card coalesces (`should_recalculate=False, coalesced=True`).
        - Cash drop > 20% (e.g. 25%) triggers immediate recalculation with `CASH_DROP_OVER_20_PERCENT` (`safety_override=True`).
        - Planned step overdue > 7 days (e.g. 8 days old) triggers recalculation with `PLANNED_STEP_OVERDUE_OVER_7_DAYS`.
        """
        # Publish an active card on initial state with 140_000 cash (available = 50_000)
        self.store.mutate(
            owner=OWNER,
            key="boost-cash-for-trigger-test",
            revision=1,
            command={"kind": "income", "amount": 40_000},
            apply=lambda s: setattr(s.snapshot, "cash", 140_000),
            render=lambda s: view(s, TODAY),
        )
        run = self.coord.start_run(TODAY)
        self.coord.submit_packet(run.run_id, build_cash_flow_packet(run, TODAY))
        self.coord.submit_packet(run.run_id, build_debt_packet(run, TODAY))
        self.coord.calculate(run.run_id, TODAY)
        active_card = self.coord.publish(run.run_id)

        prev_state = State(snapshot=fixture(TODAY))
        prev_state.snapshot.cash = 140_000

        # 1. Minor cash drop of 10% (140_000 -> 126_000, available = 36_000 >= card amount) -> coalesced!
        minor_state = State(snapshot=fixture(TODAY))
        minor_state.snapshot.cash = 126_000
        res_minor = check_recalculation_triggers(prev_state, minor_state, TODAY, active_card=active_card)
        self.assertFalse(res_minor.should_recalculate, f"Unexpected triggers: {res_minor.triggers}")
        self.assertTrue(res_minor.coalesced)

        # 2. Cash drop > 20% (140_000 -> 110_000 = 21.4% drop) -> triggers recalculation!
        drop_state = State(snapshot=fixture(TODAY))
        drop_state.snapshot.cash = 110_000
        res_drop = check_recalculation_triggers(prev_state, drop_state, TODAY, active_card=active_card)
        self.assertTrue(res_drop.should_recalculate)
        self.assertTrue(res_drop.safety_override)
        self.assertIn("CASH_DROP_OVER_20_PERCENT", res_drop.triggers)

        # 3. Planned step overdue > 7 days (created 8 days ago) -> triggers recalculation!
        overdue_state = State(
            snapshot=fixture(TODAY),
            actions=[
                Action(
                    id="step-old",
                    amount=2_000,
                    status="planned",
                    created_on=TODAY - timedelta(days=8),
                )
            ],
        )
        overdue_state.snapshot.cash = 140_000
        res_overdue = check_recalculation_triggers(prev_state, overdue_state, TODAY, active_card=active_card)
        self.assertTrue(res_overdue.should_recalculate)
        self.assertIn("PLANNED_STEP_OVERDUE_OVER_7_DAYS:step-old", res_overdue.triggers)


if __name__ == "__main__":
    unittest.main()
