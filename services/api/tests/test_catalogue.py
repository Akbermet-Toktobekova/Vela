"""Tests for the Section 9 versioned 15-action catalogue and candidate generator (T14)."""

from datetime import date, timedelta
import json
from pathlib import Path
import random
import sys
import unittest

api_root = Path(__file__).resolve().parents[1]
repo_root = api_root.parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from vela.catalogue import (
    CATALOGUE_PATH,
    SECTION9_ACTION_TITLES,
    ActionCataloguePolicy,
    CandidateAction,
    evaluate_action_eligibility,
    evaluate_predicates,
    generate_candidates,
    load_catalogue,
)
from vela.domain import Action, Debt, Obligation, Snapshot, State, Transaction, fixture

TODAY = date(2026, 10, 26)


class TestActionCataloguePolicy(unittest.TestCase):
    """Verifies the structure, invariants, and lesson alignment of policies/action-catalogue.v1.json."""

    def setUp(self):
        self.catalogue = load_catalogue()

    def test_catalogue_file_exists_and_loads(self):
        self.assertTrue(CATALOGUE_PATH.exists(), f"Missing {CATALOGUE_PATH}")
        self.assertIsInstance(self.catalogue, ActionCataloguePolicy)
        self.assertEqual(self.catalogue.version, "action-catalogue-v1")
        self.assertEqual(self.catalogue.currency, "EUR")

    def test_all_15_section9_actions_present_in_exact_order(self):
        self.assertEqual(len(self.catalogue.actions), 15)
        numbers = [a.catalog_number for a in self.catalogue.actions]
        self.assertEqual(numbers, list(range(1, 16)))
        titles = tuple(a.title for a in self.catalogue.actions)
        self.assertEqual(titles, SECTION9_ACTION_TITLES)

    def test_every_action_defines_required_section9_metadata(self):
        for action in self.catalogue.actions:
            self.assertTrue(action.id)
            self.assertTrue(action.scope_jurisdiction)
            self.assertGreater(len(action.calculation_support), 0, f"{action.id} missing calculation_support")
            self.assertIsInstance(action.prerequisites, list)
            self.assertIsInstance(action.contraindications, list)
            self.assertTrue(action.effects.description, f"{action.id} missing effects.description")
            self.assertTrue(action.lesson_id, f"{action.id} missing lesson_id")
            self.assertIn(action.lesson_id, action.related_lesson_ids)
            self.assertTrue(action.presentation.headline_template)
            self.assertTrue(action.presentation.summary_template)
            self.assertTrue(action.presentation.cta_label)
            self.assertTrue(action.presentation.disclaimer)

    def test_no_action_moves_money_or_contacts_third_parties(self):
        self.assertFalse(self.catalogue.executes_money_movement)
        self.assertFalse(self.catalogue.auto_cancels_services)
        self.assertFalse(self.catalogue.auto_contacts_lenders)
        for action in self.catalogue.actions:
            self.assertFalse(action.moves_money, f"{action.id} must not move money")
            self.assertFalse(action.auto_cancels_services, f"{action.id} must not auto-cancel services")
            self.assertFalse(action.auto_contacts_lenders, f"{action.id} must not auto-contact lenders")
            self.assertFalse(action.effects.mutates_account_balance, f"{action.id} must not mutate account balance")
            self.assertFalse(
                action.effects.executes_external_transfer,
                f"{action.id} must not execute external transfers",
            )

    def test_catalogue_synchronized_with_lessons_index(self):
        lessons_path = repo_root / "content" / "lessons" / "index.json"
        self.assertTrue(lessons_path.exists())
        lessons = json.loads(lessons_path.read_text(encoding="utf-8"))
        valid_lesson_ids = {item["id"] for item in lessons}
        catalogue_action_ids = {a.id for a in self.catalogue.actions}

        # Every lesson_id referenced in the catalogue must exist in content/lessons/index.json
        for action in self.catalogue.actions:
            self.assertIn(action.lesson_id, valid_lesson_ids, f"Unknown lesson_id {action.lesson_id} on {action.id}")
            for rel_id in action.related_lesson_ids:
                self.assertIn(rel_id, valid_lesson_ids, f"Unknown related_lesson_id {rel_id} on {action.id}")

        # Every related_action referenced in content/lessons/index.json must exist in the catalogue
        for lesson in lessons:
            for related_action in lesson.get("related_actions", []):
                self.assertIn(
                    related_action,
                    catalogue_action_ids,
                    f"Lesson {lesson['id']} references unknown action {related_action}",
                )


class TestCandidateGeneratorStates(unittest.TestCase):
    """Verifies candidate generation across financial states and eligibility rules."""

    def setUp(self):
        self.catalogue = load_catalogue()
        self.by_id = {a.id: a for a in self.catalogue.actions}

    def _assert_only_eligible_and_safe(
        self,
        state: State,
        candidates: list[CandidateAction],
        today: date = TODAY,
    ):
        self.assertGreater(len(candidates), 0)
        action_ids = [c.action_id for c in candidates]
        self.assertIn("maintain_current_plan", action_ids, "Baseline maintain_current_plan must always be a candidate")

        predicates = evaluate_predicates(state, today)
        for cand in candidates:
            self.assertIsInstance(cand.amount_cents, int)
            self.assertNotIsInstance(cand.amount_cents, bool)
            self.assertGreaterEqual(cand.amount_cents, 0)
            self.assertFalse(cand.moves_money)
            self.assertFalse(cand.mutates_account_balance)
            self.assertFalse(cand.executes_external_transfer)
            action_def = self.by_id[cand.action_id]
            elig = evaluate_action_eligibility(action_def, state, today, predicates=predicates)
            self.assertTrue(
                elig.eligible,
                f"Generator produced ineligible action {cand.action_id}: "
                f"unmet={elig.unmet_prerequisites}, contra={elig.active_contraindications}",
            )

    def test_empty_snapshot_state_yields_only_clarify_and_maintain(self):
        state = State(snapshot=None)
        candidates = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates)
        ids = {c.action_id for c in candidates}
        self.assertEqual(ids, {"clarify_material_unknown", "maintain_current_plan"})
        clarify = next(c for c in candidates if c.action_id == "clarify_material_unknown")
        self.assertEqual(clarify.clarify_field, "refresh")

    def test_stale_snapshot_or_unknown_flags_trigger_clarify_and_block_discretionary(self):
        stale_snap = fixture(TODAY - timedelta(days=10))
        state = State(snapshot=stale_snap)
        candidates = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates)
        ids = {c.action_id for c in candidates}
        self.assertIn("clarify_material_unknown", ids)
        self.assertIn("maintain_current_plan", ids)
        # Discretionary cash-allocating actions must be blocked by material_unknown_unclarified
        self.assertNotIn("contribute_savings_goal", ids)
        self.assertNotIn("build_reserve", ids)
        self.assertNotIn("extra_debt_payment_one_off", ids)

    def test_unknown_debt_terms_triggers_clarify_and_blocks_debt_strategies(self):
        state = State(
            snapshot=fixture(TODAY),
            debts=[
                Debt(
                    id="card-1",
                    label="Card",
                    balance_cents=50_000,
                    apr_bps=1800,
                    min_payment_cents=2_500,
                    terms_known=False,
                )
            ],
        )
        candidates = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates)
        ids = {c.action_id for c in candidates}
        self.assertIn("clarify_material_unknown", ids)
        self.assertNotIn("extra_debt_payment_one_off", ids)
        self.assertNotIn("extra_debt_payment_recurring", ids)
        self.assertNotIn("compare_repayment_strategies", ids)

    def test_shortfall_state_triggers_shortfall_actions_and_blocks_discretionary_outflows(self):
        snap = fixture(TODAY)
        snap.cash = 50_000  # obligations (80_000) + protected (10_000) = 90_000 -> shortfall of -40_000
        state = State(
            snapshot=snap,
            actions=[Action(id="act-1", amount=5_000, status="planned", created_on=TODAY)],
        )
        candidates = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates)
        ids = {c.action_id for c in candidates}
        self.assertIn("external_assistance_shortfall", ids)
        self.assertIn("pause_optional_allocation", ids)
        self.assertIn("maintain_current_plan", ids)
        # No discretionary outflows allowed in shortfall
        for forbidden in (
            "contribute_savings_goal",
            "build_reserve",
            "extra_debt_payment_one_off",
            "extra_debt_payment_recurring",
            "reserve_necessary_expense",
        ):
            self.assertNotIn(forbidden, ids)

    def test_section9_fixture_state_generates_expected_candidates(self):
        state = State(snapshot=fixture(TODAY))
        candidates = generate_candidates(state, TODAY, policy="section9-demo-40-v1", catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates)
        ids = {c.action_id for c in candidates}
        self.assertIn("contribute_savings_goal", ids)
        self.assertIn("build_reserve", ids)
        self.assertIn("reserve_necessary_expense", ids)
        self.assertIn("preserve_cash_until_payment", ids)
        self.assertIn("prepare_required_debt", ids)
        self.assertIn("adjust_contribution", ids)
        self.assertIn("adjust_goal_timeline", ids)
        self.assertIn("maintain_current_plan", ids)

        save_cand = next(c for c in candidates if c.action_id == "contribute_savings_goal")
        self.assertEqual(save_cand.amount_cents, 4_000)  # €40.00 in section9-demo-40-v1
        self.assertEqual(save_cand.headline, "Set aside €40 for your goal.")
        self.assertIn("Advances Emergency reserve from €0 to €40 of €500.", save_cand.summary)

    def test_debt_actions_one_off_recurring_and_strategy_comparison(self):
        state = State(
            snapshot=fixture(TODAY),
            debts=[
                Debt(
                    id="visa",
                    label="Visa Card",
                    balance_cents=40_000,
                    apr_bps=1999,
                    min_payment_cents=2_000,
                    due_day=15,
                    kind="credit_card",
                    terms_known=True,
                ),
                Debt(
                    id="loan",
                    label="Personal Loan",
                    balance_cents=80_000,
                    apr_bps=850,
                    min_payment_cents=3_000,
                    due_day=20,
                    kind="personal_loan",
                    terms_known=True,
                ),
            ],
        )
        # Without multi-period income history, one-off and strategy comparison are eligible, but recurring extra is not
        candidates_no_history = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates_no_history)
        ids_no_history = {c.action_id for c in candidates_no_history}
        self.assertIn("extra_debt_payment_one_off", ids_no_history)
        self.assertIn("compare_repayment_strategies", ids_no_history)
        self.assertNotIn("extra_debt_payment_recurring", ids_no_history)

        # Add multi-period confirmed income history (>= 2 months) and recurring charge
        state.transactions = [
            Transaction(id="inc-1", date=TODAY - timedelta(days=35), description="Salary Sep", amount=200_000, category="income"),
            Transaction(id="inc-2", date=TODAY - timedelta(days=5), description="Salary Oct", amount=200_000, category="income"),
            Transaction(id="sub-1", date=TODAY - timedelta(days=32), description="Streaming Plus", amount=-1_499, category="subscriptions"),
            Transaction(id="sub-2", date=TODAY - timedelta(days=2), description="Streaming Plus", amount=-1_499, category="subscriptions"),
        ]
        candidates_with_history = generate_candidates(state, TODAY, catalogue=self.catalogue)
        self._assert_only_eligible_and_safe(state, candidates_with_history)
        ids_with_history = {c.action_id for c in candidates_with_history}
        self.assertIn("extra_debt_payment_recurring", ids_with_history)
        self.assertIn("review_recurring_charge", ids_with_history)

    def test_all_15_actions_can_be_generated_under_valid_states(self):
        """Proves every one of the 15 actions in the catalogue is reachable and generated when its state conditions hold."""
        seen_actions: set[str] = set()

        # 1. Empty state -> clarify_material_unknown, maintain_current_plan
        s_empty = State(snapshot=None)
        seen_actions.update(c.action_id for c in generate_candidates(s_empty, TODAY, catalogue=self.catalogue))

        # 2. Shortfall with planned action -> external_assistance_shortfall, pause_optional_allocation
        snap_short = fixture(TODAY)
        snap_short.cash = 50_000
        s_short = State(
            snapshot=snap_short,
            actions=[Action(id="p1", amount=4_000, status="planned", created_on=TODAY)],
        )
        seen_actions.update(c.action_id for c in generate_candidates(s_short, TODAY, catalogue=self.catalogue))

        # 3. Healthy state with debts, multi-period income, and subscriptions -> remaining 11 actions
        s_rich = State(
            snapshot=fixture(TODAY),
            debts=[
                Debt(id="d1", label="Card A", balance_cents=30_000, apr_bps=2100, min_payment_cents=1_500, terms_known=True),
                Debt(id="d2", label="Loan B", balance_cents=60_000, apr_bps=900, min_payment_cents=2_500, terms_known=True),
            ],
            transactions=[
                Transaction(id="i1", date=TODAY - timedelta(days=40), description="Payroll", amount=180_000, category="income"),
                Transaction(id="i2", date=TODAY - timedelta(days=10), description="Payroll", amount=180_000, category="income"),
                Transaction(id="s1", date=TODAY - timedelta(days=3), description="Music Sub", amount=-999, category="subscriptions"),
            ],
        )
        seen_actions.update(c.action_id for c in generate_candidates(s_rich, TODAY, catalogue=self.catalogue))

        expected_all_15 = {a.id for a in self.catalogue.actions}
        self.assertEqual(seen_actions, expected_all_15)

    def test_property_maintain_always_present_and_only_eligible_emitted_500_trials(self):
        """Property-based invariants across 500 randomized financial states:
        1. `maintain_current_plan` (baseline) is always emitted.
        2. Every emitted candidate satisfies all prerequisites and triggers zero contraindications.
        3. No candidate moves money, mutates account balances, or executes external transfers.
        """
        rng = random.Random(20261026)
        for _ in range(500):
            cash = rng.randint(0, 300_000)
            saved = rng.randint(0, cash)
            protected = rng.randint(0, 50_000)
            rent = rng.randint(1_000, 100_000)
            debt_known = rng.choice([True, False])
            obligations_complete = rng.choice([True, False])
            has_planned = rng.choice([True, False])
            has_debt = rng.choice([True, False])
            debt_terms_known = rng.choice([True, False])

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
                    Obligation(id="rent", label="Rent", amount=rent, due=TODAY + timedelta(days=7), kind="rent"),
                ],
            )
            actions = [Action(id="a1", amount=2_000, status="planned", created_on=TODAY)] if has_planned else []
            debts = (
                [
                    Debt(
                        id="d1",
                        label="Card",
                        balance_cents=25_000,
                        apr_bps=1800,
                        min_payment_cents=1_000,
                        terms_known=debt_terms_known,
                    )
                ]
                if has_debt
                else []
            )
            state = State(snapshot=snap, actions=actions, debts=debts)
            candidates = generate_candidates(state, TODAY, catalogue=self.catalogue)
            self._assert_only_eligible_and_safe(state, candidates)


if __name__ == "__main__":
    unittest.main()
