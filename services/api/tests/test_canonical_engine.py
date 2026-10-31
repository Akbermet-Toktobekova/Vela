"""Narrow owner-requested smoke/oracle, synthetic current account only."""
from datetime import date, timedelta
import unittest

from vela.canonical_engine import contributions, evaluate_account_plan
from vela.decision import CriterionUtilities, compute_weighted_score_bp, load_scoring_policy
from vela.domain import State, Transaction
from vela.personal import Account, IncomeEstimate, ProfileDetails
from vela.planning import Bill, Goal, PlanningState, Step, planning_view


class CanonicalEngineSmokeTests(unittest.TestCase):
    day = date(2026, 10, 31)

    def fixture(self):
        state = State()
        state.personal.accounts = [Account(id='main', name='Synthetic main', currency='EUR',
                                          balance=100000, confirmed_on=self.day)]
        state.personal.planning = PlanningState(active=True, account_id='main',
            horizon=self.day+timedelta(days=30), protected=10000, bills_confirmed=True,
            debts_confirmed=True, goal=Goal(name='Optional goal', target=100000),
            bills=[Bill(id=str(i), label='Synthetic bill', amount=amount, currency='EUR',
                        due=self.day+timedelta(days=days))
                   for i, (amount, days) in enumerate([(60000, 7), (15000, 14), (5000, 21)])])
        return state

    def test_exact_existing_weight_score_and_contributions(self):
        utilities = CriterionUtilities(vR_bp=6000, vF_bp=2000, vG_bp=4000, vM_bp=8000, cE_bp=2500)
        weights = load_scoring_policy().weights_bp
        # Independent oracle:1800+500+1000+800+750=4850.
        self.assertEqual(compute_weighted_score_bp(utilities, weights), (4850, False))
        detail = contributions(utilities, weights)
        self.assertEqual(sum(item.weighted_numerator for item in detail.values()), 48500000)
        self.assertEqual(detail['E'].utility_bp, 7500)
        self.assertEqual(compute_weighted_score_bp(utilities.model_copy(update={'vF_bp': None}), weights), (None, True))

    def test_basic_current_data_selects_2000_without_mutating_or_funding_from_imports(self):
        state = self.fixture()
        state.personal.accounts.append(Account(id='huf', name='Other currency', currency='HUF',
                                              balance=900000000, confirmed_on=self.day))
        state.personal.profile_details = ProfileDetails(income_estimate=IncomeEstimate(
            amount_minor=900000000, currency='EUR', next_expected_on=self.day+timedelta(days=1)))
        state.transactions = [Transaction(id='import', date=self.day, description='Synthetic analytical income',
                                          amount=900000000, category='income', source='import:synthetic')]
        before = state.model_dump_json()
        decision = evaluate_account_plan(state, self.day)
        self.assertEqual(decision.inputs['available_cents'], 10000)
        self.assertEqual((decision.outcome, decision.selected_action_id, decision.selected_amount_cents),
                         ('save', 'contribute_savings_goal', 2000))
        self.assertTrue(decision.can_reserve)
        self.assertTrue(decision.policy.provisional)
        self.assertTrue(decision.sensitivity.stable)
        selected = next(item for item in decision.candidates
                        if item.score.candidate.candidate_id == decision.selected_candidate_id)
        self.assertEqual(selected.score.utilities.vF_bp, 0)  # earmarking is not profit
        self.assertEqual(state.model_dump_json(), before)
        self.assertEqual(planning_view(state, self.day).available, 10000)
        self.assertIsNone(decision.inputs['debt_terms'])
        state.revision += 1  # an unrelated history write must not churn the relevant bundle
        self.assertEqual(evaluate_account_plan(state, self.day).input_fingerprint, decision.input_fingerprint)

    def test_stale_shortfall_and_existing_allocation_gates(self):
        state = self.fixture()
        state.personal.accounts[0].confirmed_on = self.day-timedelta(days=1)
        stale = evaluate_account_plan(state, self.day)
        self.assertEqual(stale.outcome, 'clarify')
        self.assertFalse(stale.can_reserve)
        state.personal.accounts[0].confirmed_on = self.day
        state.personal.accounts[0].balance = 80000
        shortfall = evaluate_account_plan(state, self.day)
        self.assertEqual(shortfall.inputs['available_cents'], -10000)
        self.assertEqual(shortfall.outcome, 'shortfall')
        self.assertFalse(shortfall.can_reserve)
        state.personal.accounts[0].balance = 100000
        state.personal.planning.goal.saved = 4000
        state.personal.planning.steps = [Step(id='accepted', account_id='main', currency='EUR',
                                            amount=4000, created_on=self.day)]
        planned = evaluate_account_plan(state, self.day)
        self.assertEqual(planned.inputs['available_cents'], 2000)
        self.assertEqual((planned.outcome, planned.preserved_step_id), ('planned', 'accepted'))
        self.assertFalse(planned.can_reserve)
