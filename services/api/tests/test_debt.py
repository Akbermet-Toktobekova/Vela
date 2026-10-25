"""Deterministic tests and property-based invariants for Debt Engine (T12, §9, §15).

Includes:
- 4 hand-calculated reference amortization cases (literal integer EUR cents, no production calls for expected values)
- Zero-rate (`apr_bps == 0`), non-amortizing (`payment <= interest`), and unknown terms (`terms_known=False`)
- Final payment cap and one-off extra payment capped at remaining balance (`extra > balance`)
- Avalanche vs Snowball strategy comparison and savings vs minimum-only baseline
- 500-trial randomized property invariants (principal + interest == total_paid; avalanche interest <= snowball interest)
- HTTP API tests for `POST /v1/debts`, `GET /v1/debts`, `DELETE /v1/debts/{id}`, `POST /v1/debts/simulate`
  with idempotency (`Idempotency-Key`), optimistic concurrency (`revision` / 409 Conflict), and zero mutation on simulate.
"""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import random
import sys
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from fastapi.testclient import TestClient
from vela.domain import Debt
from vela.debt import (
    ROUNDING_RULE,
    amortize_single_debt,
    compare_and_simulate,
    monthly_interest_cents,
    simulate_strategy,
)
from vela.main import create_app

TODAY = date(2026, 10, 24)
TOKEN = "test-only-token-at-least-24-characters"


class TestDebtEngineReferenceAndBoundaryCases(unittest.TestCase):
    """Hand-calculated reference fixtures and §15 boundary conditions."""

    def test_hand_calculated_case_1_1000_eur_at_12_percent_apr(self):
        """Reference Case 1 (hand-calculated):
        Balance: €1,000.00 (100_000 cents), APR: 12.00% (1200 bps -> 1% per month), Min payment: €350.00 (35_000 cents).
        - Month 1: opening 100_000, interest = (100_000 * 1200 + 60_000) // 120_000 = 1_000,
                   payment = 35_000, principal reduction = 34_000 -> ending balance = 66_000
        - Month 2: opening 66_000, interest = 660,
                   payment = 35_000, principal reduction = 34_340 -> ending balance = 31_660
        - Month 3: opening 31_660, interest = (31_660 * 1200 + 60_000) // 120_000 = 317 (316.6 rounds half-up to 317),
                   due = 31_660 + 317 = 31_977 < 35_000 (final payment cap!),
                   payment = 31_977 -> ending balance = 0
        Total months = 3
        Total interest = 1_000 + 660 + 317 = 1_977 cents (€19.77)
        Total paid = 35_000 + 35_000 + 31_977 = 101_977 cents (€1,019.77)
        """
        debt = Debt(
            id="ref-1",
            label="Personal Loan 12%",
            balance_cents=100_000,
            apr_bps=1200,
            min_payment_cents=35_000,
            due_day=15,
            kind="personal_loan",
            terms_known=True,
        )
        res = amortize_single_debt(debt)
        self.assertEqual(res.status, "paid")
        self.assertEqual(res.months, 3)
        self.assertEqual(res.total_interest_cents, 1_977)
        self.assertEqual(res.total_paid_cents, 101_977)
        self.assertEqual(res.principal_paid_cents, 100_000)

    def test_hand_calculated_case_2_zero_apr_with_final_payment_cap(self):
        """Reference Case 2 (hand-calculated 0% APR):
        Balance: €500.00 (50_000 cents), APR: 0% (0 bps), Min payment: €150.00 (15_000 cents).
        - Months 1..3: 15_000 each = 45_000
        - Month 4: capped at remaining 5_000
        Total months = 4, Total interest = 0, Total paid = 50_000.
        """
        debt = Debt(
            id="ref-2",
            label="Zero APR Installment",
            balance_cents=50_000,
            apr_bps=0,
            min_payment_cents=15_000,
            due_day=1,
            kind="other",
            terms_known=True,
        )
        res = amortize_single_debt(debt)
        self.assertEqual(res.status, "paid")
        self.assertEqual(res.months, 4)
        self.assertEqual(res.total_interest_cents, 0)
        self.assertEqual(res.total_paid_cents, 50_000)
        self.assertEqual(res.principal_paid_cents, 50_000)

    def test_hand_calculated_case_3_avalanche_vs_snowball_multi_debt(self):
        """Reference Case 3 (hand-calculated 2-debt Avalanche vs Snowball):
        Debt A (Small, 0% APR): balance 10_000 (€100), APR 0 bps, min_payment 5_000 (€50)
        Debt B (Large, 24% APR): balance 20_000 (€200), APR 2400 bps (2%/mo), min_payment 5_000 (€50)
        Recurring extra payment: 5_000 (€50/mo) -> Total monthly budget = 15_000 (€150/mo).

        1) Minimum-only baseline (no extra, no rollover):
           - Debt A: 10_000 @ 0% with 5_000/mo -> 2 months, 0 interest
           - Debt B: 20_000 @ 2%/mo with 5_000/mo:
             * M1: 20_000 + 400 - 5_000 = 15_400 (int 400)
             * M2: 15_400 + 308 - 5_000 = 10_708 (int 308)
             * M3: 10_708 + 214 - 5_000 = 5_922  (int 214)
             * M4: 5_922  + 118 - 5_000 = 1_040  (int 118)
             * M5: 1_040  + 21  - 1_061 = 0      (int 21)
             Total baseline interest = 400 + 308 + 214 + 118 + 21 = 1_061 cents, months = 5.

        2) Avalanche (targets Debt B @ 24% first with the 5_000 extra):
           - M1: A gets min 5_000 -> 5_000; B gets 5_000 + 5_000 = 10_000 -> 20_000 + 400 - 10_000 = 10_400 (int 400)
           - M2: A gets min 5_000 -> 0;     B gets 5_000 + 5_000 = 10_000 -> 10_400 + 208 - 10_000 = 608   (int 208)
           - M3: A is 0; B gets min(15_000, 608 + 12) = 620 -> 0 (int 12)
           Total Avalanche interest = 400 + 208 + 12 = 620 cents, months = 3.
           Savings vs baseline = 1_061 - 620 = 441 cents, months saved = 5 - 3 = 2.

        3) Snowball (targets Debt A with smaller balance 10_000 first):
           - M1: A gets 5_000 + 5_000 = 10_000 -> 0; B gets min 5_000 -> 20_000 + 400 - 5_000 = 15_400 (int 400)
           - M2: A is 0; B gets full 15_000 budget -> 15_400 + 308 - 15_000 = 708 (int 308)
           - M3: A is 0; B gets min(15_000, 708 + 14) = 722 -> 0 (int 14)
           Total Snowball interest = 400 + 308 + 14 = 722 cents, months = 3.
           Savings vs baseline = 1_061 - 722 = 339 cents, months saved = 5 - 3 = 2.
        """
        debts = [
            Debt(id="debt-a", label="Small 0%", balance_cents=10_000, apr_bps=0, min_payment_cents=5_000),
            Debt(id="debt-b", label="Large 24%", balance_cents=20_000, apr_bps=2400, min_payment_cents=5_000),
        ]
        sim = compare_and_simulate(debts, revision=1, recurring_extra_cents=5_000)
        self.assertEqual(sim.rounding_rule, ROUNDING_RULE)
        self.assertEqual(sim.status, "paid")

        # Baseline
        self.assertEqual(sim.baseline.months, 5)
        self.assertEqual(sim.baseline.total_interest_cents, 1_061)
        self.assertEqual(sim.baseline.total_paid_cents, 31_061)

        # Avalanche
        self.assertEqual(sim.avalanche.months, 3)
        self.assertEqual(sim.avalanche.total_interest_cents, 620)
        self.assertEqual(sim.avalanche.total_paid_cents, 30_620)
        self.assertEqual(sim.avalanche.interest_saved_vs_baseline_cents, 441)
        self.assertEqual(sim.avalanche.months_saved_vs_baseline, 2)

        # Snowball
        self.assertEqual(sim.snowball.months, 3)
        self.assertEqual(sim.snowball.total_interest_cents, 722)
        self.assertEqual(sim.snowball.total_paid_cents, 30_722)
        self.assertEqual(sim.snowball.interest_saved_vs_baseline_cents, 339)
        self.assertEqual(sim.snowball.months_saved_vs_baseline, 2)

    def test_non_amortizing_debt_when_payment_less_or_equal_to_interest(self):
        """If payment <= monthly interest, status is 'non_amortizing' with no invented payoff horizon."""
        # 100_000 @ 12% APR accrues 1_000 cents interest in month 1
        for bad_min in (0, 500, 1_000):
            debt = Debt(
                id="non-amort",
                label="Interest-only trap",
                balance_cents=100_000,
                apr_bps=1200,
                min_payment_cents=bad_min,
            )
            res = amortize_single_debt(debt)
            self.assertEqual(res.status, "non_amortizing")
            self.assertIsNone(res.months)
            self.assertIsNone(res.total_interest_cents)
            self.assertIsNone(res.total_paid_cents)

    def test_unknown_terms_returns_needs_input_without_false_precision(self):
        """When terms_known is False, returns status='needs_input' and None metrics."""
        debt = Debt(
            id="unknown-card",
            label="Card with unknown APR",
            balance_cents=40_000,
            apr_bps=0,
            min_payment_cents=2_000,
            terms_known=False,
        )
        single = amortize_single_debt(debt)
        self.assertEqual(single.status, "needs_input")
        self.assertIsNone(single.months)
        self.assertIsNone(single.total_interest_cents)

        comp = compare_and_simulate([debt])
        self.assertEqual(comp.status, "needs_input")
        self.assertEqual(comp.avalanche.status, "needs_input")
        self.assertEqual(comp.snowball.status, "needs_input")
        self.assertIsNone(comp.avalanche.total_interest_cents)

    def test_one_off_extra_payment_larger_than_balance_is_capped(self):
        """One-off extra payment exceeding remaining balance is capped at balance."""
        debt = Debt(
            id="small-loan",
            label="Small loan",
            balance_cents=15_000,
            apr_bps=1800,
            min_payment_cents=3_000,
        )
        sim = compare_and_simulate([debt], one_off_extra_cents=50_000)
        self.assertIsNotNone(sim.one_off_preview)
        self.assertEqual(sim.one_off_preview.requested_extra_cents, 50_000)
        self.assertEqual(sim.one_off_preview.applied_extra_cents, 15_000)
        self.assertEqual(sim.one_off_preview.months, 0)
        self.assertEqual(sim.one_off_preview.total_interest_cents, 0)
        self.assertEqual(sim.one_off_preview.total_paid_cents, 15_000)

    def test_randomized_property_invariants_500_trials(self):
        """Property-based invariants across 500 randomized multi-debt portfolios:
        1. Conservation: for every paid strategy, `total_paid_cents == sum(balance_cents) + total_interest_cents`.
        2. Per-debt conservation: `d.principal_paid_cents + d.total_interest_cents == d.total_paid_cents`.
        3. Optimality: `avalanche.total_interest_cents <= snowball.total_interest_cents <= baseline.total_interest_cents`.
        4. Pace: `avalanche.months <= baseline.months` and `snowball.months <= baseline.months`.
        """
        rng = random.Random(20261025)
        for trial in range(500):
            n_debts = rng.randint(1, 4)
            debts: list[Debt] = []
            for idx in range(n_debts):
                balance = rng.randint(1_000, 200_000)
                apr_bps = rng.choice([0, 300, 600, 999, 1200, 1799, 2400, 2999])
                first_int = monthly_interest_cents(balance, apr_bps)
                # Ensure amortizing minimum payment: at least first_int + 2% of balance + 200 cents
                min_pay = first_int + max(200, balance // 40) + rng.randint(0, 5_000)
                debts.append(
                    Debt(
                        id=f"d-{trial}-{idx}",
                        label=f"Debt {idx}",
                        balance_cents=balance,
                        apr_bps=apr_bps,
                        min_payment_cents=min_pay,
                        due_day=rng.randint(1, 28),
                        kind="credit_card",
                        terms_known=True,
                    )
                )
            recurring_extra = rng.randint(0, 10_000)
            one_off_extra = rng.randint(0, 50_000)
            sim = compare_and_simulate(
                debts,
                recurring_extra_cents=recurring_extra,
                one_off_extra_cents=one_off_extra,
            )
            total_principal = sum(d.balance_cents for d in debts)

            for strat in (sim.baseline, sim.avalanche, sim.snowball):
                self.assertEqual(strat.status, "paid")
                self.assertEqual(
                    strat.total_paid_cents,
                    total_principal + (strat.total_interest_cents or 0),
                    f"Conservation failed on trial {trial} ({strat.strategy})",
                )
                for item in strat.debts:
                    self.assertEqual(
                        item.total_paid_cents,
                        (item.principal_paid_cents or 0) + (item.total_interest_cents or 0),
                    )

            # Avalanche never pays more interest than Snowball or Minimum-only baseline
            self.assertLessEqual(sim.avalanche.total_interest_cents, sim.snowball.total_interest_cents)
            self.assertLessEqual(sim.snowball.total_interest_cents, sim.baseline.total_interest_cents)
            self.assertLessEqual(sim.avalanche.months, sim.baseline.months)
            self.assertLessEqual(sim.snowball.months, sim.baseline.months)

            # One-off preview conservation and cap
            self.assertLessEqual(sim.one_off_preview.applied_extra_cents, total_principal)
            self.assertEqual(
                sim.one_off_preview.total_paid_cents,
                total_principal + (sim.one_off_preview.total_interest_cents or 0),
            )


class TestDebtAPIEndpoints(unittest.TestCase):
    """HTTP API tests for /v1/debts and /v1/debts/simulate."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.app = create_app(f"sqlite:///{self.path / 'test.db'}", TOKEN, lambda: TODAY, self.path)
        self.client = TestClient(self.app)
        self.headers = {"Authorization": f"Bearer {TOKEN}"}
        self.counter = 0

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def _key(self, prefix: str = "debt-cmd") -> dict:
        self.counter += 1
        return {**self.headers, "Idempotency-Key": f"{prefix}-{self.counter:04d}"}

    def test_crud_idempotency_concurrency_and_read_only_simulation(self):
        # 1. Initial GET /v1/debts is empty
        initial = self.client.get("/v1/debts", headers=self.headers)
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(initial.json()["debts"], [])
        self.assertEqual(initial.json()["revision"], 0)

        # 2. POST /v1/debts adds first debt and bumps revision to 1 (idempotent retry returns identical response)
        debt1_payload = {
            "revision": 0,
            "debt": {
                "id": "card-alpha",
                "label": "Alpha Card",
                "balance_cents": 20_000,
                "apr_bps": 2400,
                "min_payment_cents": 5_000,
                "due_day": 15,
                "kind": "credit_card",
                "terms_known": True,
            },
        }
        headers_same = {**self.headers, "Idempotency-Key": "add-card-alpha-001"}
        res1 = self.client.post("/v1/debts", json=debt1_payload, headers=headers_same)
        self.assertEqual(res1.status_code, 200, res1.text)
        self.assertEqual(res1.json()["revision"], 1)
        self.assertEqual(len(res1.json()["debts"]), 1)

        # Exact retry with same Idempotency-Key returns 200 without re-applying
        res1_retry = self.client.post("/v1/debts", json=debt1_payload, headers=headers_same)
        self.assertEqual(res1_retry.status_code, 200)
        self.assertEqual(res1_retry.json(), res1.json())

        # Conflicting payload with same Idempotency-Key returns 409 Conflict
        res1_conflict = self.client.post(
            "/v1/debts",
            json={**debt1_payload, "revision": 1},
            headers=headers_same,
        )
        self.assertEqual(res1_conflict.status_code, 409)

        # Stale revision with a new key returns 409 Conflict
        stale_res = self.client.post("/v1/debts", json=debt1_payload, headers=self._key())
        self.assertEqual(stale_res.status_code, 409)

        # 3. Add second debt (revision 1 -> 2)
        debt2_payload = {
            "revision": 1,
            "debt": {
                "id": "loan-beta",
                "label": "Beta Loan",
                "balance_cents": 10_000,
                "apr_bps": 0,
                "min_payment_cents": 5_000,
                "due_day": 5,
                "kind": "personal_loan",
                "terms_known": True,
            },
        }
        res2 = self.client.post("/v1/debts", json=debt2_payload, headers=self._key())
        self.assertEqual(res2.status_code, 200, res2.text)
        self.assertEqual(res2.json()["revision"], 2)

        # 4. POST /v1/debts/simulate performs calculation without mutating state or revision
        sim_res = self.client.post(
            "/v1/debts/simulate",
            json={"recurring_extra_cents": 5_000, "one_off_extra_cents": 2_000},
            headers=self.headers,
        )
        self.assertEqual(sim_res.status_code, 200, sim_res.text)
        sim_data = sim_res.json()
        self.assertEqual(sim_data["revision"], 2)
        self.assertEqual(sim_data["avalanche"]["total_interest_cents"], 620)
        self.assertEqual(sim_data["snowball"]["total_interest_cents"], 722)
        self.assertEqual(sim_data["one_off_preview"]["applied_extra_cents"], 2_000)

        # Verify state revision and debt balances were NOT mutated by simulate
        after_sim = self.client.get("/v1/debts", headers=self.headers).json()
        self.assertEqual(after_sim["revision"], 2)
        self.assertEqual(len(after_sim["debts"]), 2)

        # 5. DELETE /v1/debts/{id} with stale revision fails with 409, with current revision succeeds
        del_stale = self.client.request(
            "DELETE",
            "/v1/debts/card-alpha",
            json={"revision": 1},
            headers=self._key(),
        )
        self.assertEqual(del_stale.status_code, 409)

        del_ok = self.client.request(
            "DELETE",
            "/v1/debts/card-alpha",
            json={"revision": 2},
            headers=self._key(),
        )
        self.assertEqual(del_ok.status_code, 200, del_ok.text)
        self.assertEqual(del_ok.json()["revision"], 3)
        self.assertEqual([d["id"] for d in del_ok.json()["debts"]], ["loan-beta"])


if __name__ == "__main__":
    unittest.main()
