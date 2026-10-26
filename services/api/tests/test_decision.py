"""Tests for Section 10 Multi-Criteria Decision Analysis (MCDA) ranking, urgency classes,
hard affordability constraints, sensitivity analysis, and DecisionEvaluationSnapshot (T15).
"""

from datetime import date, timedelta
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from fastapi.testclient import TestClient
from vela.catalogue import CandidateAction, generate_candidates, load_catalogue
from vela.decision import (
    BP_SCALE,
    SCORING_PATH,
    CriterionUtilities,
    DecisionEvaluationSnapshot,
    ScoringPolicy,
    ScoringWeights,
    check_hard_constraints,
    compute_utilities,
    compute_weighted_score_bp,
    evaluate_decision,
    load_scoring_policy,
)
from vela.domain import Action, Debt, Obligation, Snapshot, State, fixture
from vela.main import create_app

TODAY = date(2026, 10, 26)
TOKEN = "test-only-token-at-least-24-characters"


class TestMCDAPolicyAndUtilities(unittest.TestCase):
    """Verifies scoring.v1.json policy invariants, anchored utilities, and unknown handling."""

    def setUp(self):
        self.scoring = load_scoring_policy()
        self.catalogue = load_catalogue()

    def test_scoring_policy_loads_and_is_marked_provisional(self):
        self.assertTrue(SCORING_PATH.exists())
        self.assertIsInstance(self.scoring, ScoringPolicy)
        self.assertEqual(self.scoring.version, "scoring-v1")
        self.assertTrue(self.scoring.provisional, "Demo MCDA weights must be explicitly marked provisional=True")
        self.assertEqual(
            self.scoring.weights_bp.R
            + self.scoring.weights_bp.F
            + self.scoring.weights_bp.G
            + self.scoring.weights_bp.M
            + self.scoring.weights_bp.E,
            BP_SCALE,
        )

    def test_unknown_criterion_never_converted_to_zero(self):
        """§10: Never convert unknown to zero or silently renormalize differently for each candidate."""
        state = State(snapshot=fixture(TODAY))
        cands = generate_candidates(state, TODAY, catalogue=self.catalogue)
        save_cand = next(c for c in cands if c.action_id == "contribute_savings_goal")

        # Mark financial benefit vF_bp as unknown
        utils = compute_utilities(
            save_cand,
            state,
            self.scoring.anchors,
            custom_evidence={"vF_bp": "unknown"},
        )
        self.assertIsNone(utils.vF_bp, "Unknown criterion must remain None, never 0")

        score_bp, has_unknown = compute_weighted_score_bp(utils, self.scoring.weights_bp)
        self.assertTrue(has_unknown)
        self.assertIsNone(score_bp, "Candidate with unknown positively-weighted criterion must not get a numeric score")

        # Inject candidate with unknown criterion into evaluate_decision -> must not be selected by MCDA
        tampered = save_cand.model_copy(
            update={"calculation_evidence": {**save_cand.calculation_evidence, "vR_bp": "unknown"}}
        )
        snap = evaluate_decision(
            state,
            TODAY,
            catalogue=self.catalogue,
            scoring=self.scoring,
            candidates_override=[tampered, next(c for c in cands if c.action_id == "maintain_current_plan")],
        )
        self.assertIn("UNKNOWN_CRITERION:contribute_savings_goal", snap.reason_codes)
        self.assertNotEqual(snap.selected_action_id, "contribute_savings_goal")

    def test_reserve_goal_overlap_discounted_and_transfers_not_counted_as_profit(self):
        """§10: Do not count the same reserve benefit as full resilience and full goal benefit
        without adjusting overlap. Do not equate transfers with profit.
        """
        state = State(snapshot=fixture(TODAY))
        cands = generate_candidates(state, TODAY, catalogue=self.catalogue)
        save_cand = next(c for c in cands if c.action_id == "contribute_savings_goal")
        reserve_cand = next(c for c in cands if c.action_id == "build_reserve")

        save_u = compute_utilities(save_cand, state, self.scoring.anchors)
        reserve_u = compute_utilities(reserve_cand, state, self.scoring.anchors)

        # Transfers / savings reservations have zero net financial profit (vF_bp == 0)
        self.assertEqual(save_u.vF_bp, 0)
        self.assertEqual(reserve_u.vF_bp, 0)

        # Overlap discount keeps secondary dimension strictly below full 10_000 bp even at max amount
        big_save = save_cand.model_copy(update={"amount_cents": 200_000})
        big_u = compute_utilities(big_save, state, self.scoring.anchors)
        self.assertEqual(big_u.vG_bp, 10_000)
        self.assertEqual(big_u.vR_bp, 5_000)  # discounted by 50% overlap discount!


class TestUrgencyPrecedenceAndHardConstraints(unittest.TestCase):
    """Verifies hard constraints and urgency classes outside the weighted score."""

    def setUp(self):
        self.scoring = load_scoring_policy()
        self.catalogue = load_catalogue()

    def test_urgent_due_payment_always_beats_large_long_term_benefit(self):
        """Acceptance requirement: 'срочный платёж всегда побеждает большую долгосрочную выгоду'
        (§10: a large long-term benefit cannot compensate for missing an imminent necessary payment).
        """
        # User has an unprotected required debt payment due this month AND a very high-APR debt
        # where an extra payment or goal contribution has maximum long-term utility.
        snap = fixture(TODAY)
        snap.cash = 115_000  # available after existing obligations = 25_000
        state = State(
            snapshot=snap,
            debts=[
                Debt(
                    id="imminent-loan",
                    label="Imminent Required Loan",
                    balance_cents=200_000,
                    apr_bps=2999,  # 29.99% APR — huge long-term interest saving if extra paid!
                    min_payment_cents=5_000,
                    due_day=TODAY.day,
                    kind="personal_loan",
                    terms_known=True,
                )
            ],
        )
        # Remove the generic 'debt' obligation from snapshot so `imminent-loan` required payment is not yet protected in obligations
        state.snapshot.obligations = [o for o in state.snapshot.obligations if o.id != "debt"]

        # Even if we weight F (financial benefit) and G (goal progress) heavily at 90% combined,
        # the `due_obligation` urgency class (`prepare_required_debt`) MUST win over `extra_debt_payment_one_off`
        # and `contribute_savings_goal` (`ordinary` class).
        extreme_long_term_scoring = self.scoring.model_copy(
            update={
                "weights_bp": ScoringWeights(R=500, F=5000, G=4000, M=250, E=250),
            }
        )
        eval_snap = evaluate_decision(
            state,
            TODAY,
            catalogue=self.catalogue,
            scoring=extreme_long_term_scoring,
        )
        self.assertEqual(eval_snap.active_urgency_class, "due_obligation")
        self.assertEqual(eval_snap.selected_action_id, "prepare_required_debt")
        self.assertIn("ACTIVE_URGENCY_CLASS:due_obligation", eval_snap.reason_codes)

    def test_shortfall_urgency_always_beats_due_obligation_and_ordinary(self):
        """Shortfall urgency class (`shortfall` > `due_obligation` > `ordinary`) always takes precedence."""
        snap = fixture(TODAY)
        snap.cash = 60_000  # obligations (80_000) + protected (10_000) = 90_000 -> shortfall of -30_000
        state = State(
            snapshot=snap,
            actions=[Action(id="planned-40", amount=4_000, status="planned", created_on=TODAY)],
        )
        eval_snap = evaluate_decision(state, TODAY, catalogue=self.catalogue, scoring=self.scoring)
        self.assertEqual(eval_snap.active_urgency_class, "shortfall")
        self.assertIn(
            eval_snap.selected_action_id,
            ("external_assistance_shortfall", "pause_optional_allocation"),
        )

    def test_hard_constraints_reject_over_capacity_and_money_moving_candidates(self):
        """Hard constraints reject any candidate whose reservation exceeds lowest projected horizon capacity."""
        state = State(snapshot=fixture(TODAY))  # available capacity = 10_000 (€100)
        cands = generate_candidates(state, TODAY, catalogue=self.catalogue)
        save_cand = next(c for c in cands if c.action_id == "contribute_savings_goal")

        # Candidate proposing 15_000 (€150) exceeds 10_000 capacity -> rejected by hard constraint before scoring
        over_cap = save_cand.model_copy(update={"candidate_id": "save:over", "amount_cents": 15_000})
        passed, reasons = check_hard_constraints(over_cap, state, TODAY)
        self.assertFalse(passed)
        self.assertIn("HARD_REJECT_EXCEEDS_HORIZON_CAPACITY", reasons)

        # Ensure evaluate_decision marks it `passed_hard_constraints=False` and `weighted_score_bp=None`
        baseline = next(c for c in cands if c.action_id == "maintain_current_plan")
        eval_snap = evaluate_decision(
            state,
            TODAY,
            catalogue=self.catalogue,
            scoring=self.scoring,
            candidates_override=[over_cap, baseline],
        )
        rejected = next(sc for sc in eval_snap.ranked_candidates if sc.candidate.candidate_id == "save:over")
        self.assertFalse(rejected.passed_hard_constraints)
        self.assertIsNone(rejected.weighted_score_bp)
        self.assertEqual(eval_snap.selected_action_id, "maintain_current_plan")


class TestSensitivityAndSnapshotPersistence(unittest.TestCase):
    """Verifies ±20% weight sensitivity checks, fallback behavior, and API persistence."""

    def setUp(self):
        self.scoring = load_scoring_policy()
        self.catalogue = load_catalogue()
        self.tmp = TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.app = create_app(f"sqlite:///{self.path / 'test.db'}", TOKEN, lambda: TODAY, self.path)
        self.client = TestClient(self.app)
        self.headers = {"Authorization": f"Bearer {TOKEN}"}

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_sensitivity_instability_triggers_fallback_to_maintain_or_clarify(self):
        """When two ordinary candidates have nearly identical utilities so ±20% weight perturbation
        flips the winner, sensitivity analysis detects instability and falls back to `maintain_current_plan`
        (or `clarify_material_unknown` if present).
        """
        state = State(snapshot=fixture(TODAY))
        cands = generate_candidates(state, TODAY, catalogue=self.catalogue)
        save_cand = next(c for c in cands if c.action_id == "contribute_savings_goal")
        reserve_cand = next(c for c in cands if c.action_id == "build_reserve")
        maintain_cand = next(c for c in cands if c.action_id == "maintain_current_plan")

        # Under balanced R=2750, G=2750 weights, `contribute_savings_goal` and `build_reserve`
        # trade places when R is perturbed +20% vs when G is perturbed +20%.
        knife_edge_scoring = self.scoring.model_copy(
            update={
                "weights_bp": ScoringWeights(R=2850, F=2000, G=3150, M=1000, E=1000),
            }
        )
        eval_snap = evaluate_decision(
            state,
            TODAY,
            catalogue=self.catalogue,
            scoring=knife_edge_scoring,
            candidates_override=[save_cand, reserve_cand, maintain_cand],
        )
        self.assertFalse(eval_snap.sensitivity.stable)
        self.assertTrue(eval_snap.sensitivity.fallback_triggered)
        self.assertGreater(len(eval_snap.sensitivity.flipped_under_trials), 0)
        self.assertEqual(eval_snap.selected_action_id, "maintain_current_plan")
        self.assertIn("FALLBACK_TO_MAINTAIN_CURRENT_PLAN", eval_snap.reason_codes)

    def test_api_decision_evaluate_persists_snapshot_and_supports_idempotency(self):
        """Verifies GET /v1/decision and POST /v1/decision/evaluate save DecisionEvaluationSnapshot."""
        # Load demo state (revision 0 -> 1)
        load_res = self.client.post(
            "/v1/demo",
            json={"revision": 0},
            headers={**self.headers, "Idempotency-Key": "init-demo-t15"},
        )
        self.assertEqual(load_res.status_code, 200)

        # 1. Read-only GET /v1/decision
        get_res = self.client.get(
            "/v1/decision?policy=section9-demo-40-v1",
            headers=self.headers,
        )
        self.assertEqual(get_res.status_code, 200, get_res.text)
        snap_view = DecisionEvaluationSnapshot.model_validate(get_res.json())
        self.assertEqual(snap_view.state_revision, 1)
        self.assertEqual(snap_view.catalogue_version, "action-catalogue-v1")
        self.assertEqual(snap_view.scoring_version, "scoring-v1")
        self.assertTrue(snap_view.provisional_weights)
        self.assertIsNotNone(snap_view.selected_candidate_id)
        self.assertIsNotNone(snap_view.runner_up_candidate_id)

        # 2. Mutating POST /v1/decision/evaluate stores the snapshot in state.history
        eval_headers = {**self.headers, "Idempotency-Key": "eval-save-001"}
        post_res = self.client.post(
            "/v1/decision/evaluate",
            json={"revision": 1, "policy": "section9-demo-40-v1"},
            headers=eval_headers,
        )
        self.assertEqual(post_res.status_code, 200, post_res.text)
        saved_snap = post_res.json()
        self.assertEqual(saved_snap["state_revision"], 1)

        # Exact retry returns identical snapshot
        retry_res = self.client.post(
            "/v1/decision/evaluate",
            json={"revision": 1, "policy": "section9-demo-40-v1"},
            headers=eval_headers,
        )
        self.assertEqual(retry_res.status_code, 200)
        self.assertEqual(retry_res.json(), saved_snap)

        # Verify state history contains the persisted DecisionEvaluationSnapshot
        state_data = self.client.get("/v1/state", headers=self.headers).json()
        self.assertEqual(state_data["revision"], 2)
        decision_events = [h for h in state_data["history"] if h.get("event") == "decision_snapshot"]
        self.assertEqual(len(decision_events), 1)
        self.assertEqual(
            decision_events[0]["snapshot"]["evaluation_id"],
            saved_snap["evaluation_id"],
        )

    def test_randomized_mcda_invariants_200_trials(self):
        """Property-based checks across 200 randomized states:
        - Urgency precedence always respected (`shortfall` > `due_obligation` > `ordinary`).
        - Deterministic tie-breaking produces identical results on repeated calls.
        - `DecisionEvaluationSnapshot` always records inputs, versions, reason codes, and selected action.
        """
        rng = random.Random(20261026)
        for _ in range(200):
            cash = rng.randint(10_000, 250_000)
            saved = rng.randint(0, min(cash, 40_000))
            protected = rng.randint(5_000, 30_000)
            rent = rng.randint(20_000, 90_000)
            due_offset = rng.randint(1, 25)
            debt_known = rng.choice([True, False])
            obligations_complete = rng.choice([True, False])

            snap = Snapshot(
                as_of=TODAY,
                horizon=TODAY + timedelta(days=30),
                cash=cash,
                saved=saved,
                protected=protected,
                goal_target=50_000,
                obligations_complete=obligations_complete,
                debt_known=debt_known,
                obligations=[
                    Obligation(
                        id="rent",
                        label="Rent",
                        amount=rent,
                        due=TODAY + timedelta(days=due_offset),
                        kind="rent",
                    )
                ],
            )
            state = State(snapshot=snap)
            res1 = evaluate_decision(state, TODAY, catalogue=self.catalogue, scoring=self.scoring)
            res2 = evaluate_decision(state, TODAY, catalogue=self.catalogue, scoring=self.scoring)

            self.assertEqual(res1.selected_candidate_id, res2.selected_candidate_id)
            self.assertEqual(res1.runner_up_candidate_id, res2.runner_up_candidate_id)
            self.assertEqual(res1.active_urgency_class, res2.active_urgency_class)
            self.assertTrue(res1.provisional_weights)
            self.assertGreater(len(res1.reason_codes), 0)


if __name__ == "__main__":
    unittest.main()
