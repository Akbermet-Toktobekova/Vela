"""Unit tests for autonomous chat tools and numeric verification (§9, §10, §15)."""

from datetime import date, timedelta
from pathlib import Path
import sys
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from vela.debt import compare_and_simulate
from vela.domain import Action, Debt, Obligation, Snapshot, State, Transaction, capacity
from vela.tools import (
    calculate_cash_flow,
    collect_all_tool_outputs,
    extract_tool_numbers,
    get_financial_snapshot,
    get_spending_by_category,
    simulate_debt_payment,
    verify_reply_numbers,
)


class TestChatTools(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 3, 1)
        self.snapshot = Snapshot(
            as_of=self.today,
            horizon=self.today + timedelta(days=30),
            cash=100000,  # €1,000.00
            saved=0,
            protected=10000,  # €100.00
            goal_target=50000,  # €500.00
            goal_name="Emergency fund",
            obligations_complete=True,
            debt_known=True,
            obligations=[
                Obligation(
                    id="rent",
                    label="Apartment Rent",
                    amount=60000,  # €600.00
                    due=self.today + timedelta(days=5),
                    kind="rent",
                ),
                Obligation(
                    id="groceries",
                    label="Food & essentials",
                    amount=15000,  # €150.00
                    due=self.today + timedelta(days=15),
                    kind="living",
                ),
                Obligation(
                    id="internet",
                    label="Broadband",
                    amount=5000,  # €50.00
                    due=self.today + timedelta(days=20),
                    kind="other",
                ),
            ],
        )

        self.debts = [
            Debt(
                id="card1",
                label="Visa Card",
                balance_cents=100000,  # €1,000.00
                apr_bps=1850,  # 18.50%
                min_payment_cents=5000,  # €50.00
                due_day=15,
                kind="credit_card",
            ),
            Debt(
                id="loan1",
                label="Personal Loan",
                balance_cents=150000,  # €1,500.00
                apr_bps=600,  # 6.00%
                min_payment_cents=7500,  # €75.00
                due_day=20,
                kind="personal_loan",
            ),
        ]

        self.transactions = [
            Transaction(
                id="tx1",
                date=self.today - timedelta(days=2),
                description="Salary employer AG",
                amount=240000,  # +€2,400.00
                category="income",
            ),
            Transaction(
                id="tx2",
                date=self.today - timedelta(days=5),
                description="REWE Supermarket",
                amount=-6500,  # -€65.00
                category="groceries",
            ),
            Transaction(
                id="tx3",
                date=self.today - timedelta(days=10),
                description="Netflix subscription",
                amount=-1599,  # -€15.99
                category="subscriptions",
            ),
            Transaction(
                id="tx4",
                date=self.today - timedelta(days=12),
                description="Spotify premium",
                amount=-999,  # -€9.99
                category="subscriptions",
            ),
            Transaction(
                id="tx5",
                date=self.today - timedelta(days=15),
                description="Internal savings transfer",
                amount=-10000,  # -€100.00
                category="transfers",  # Should be excluded from income/spending
            ),
        ]

        self.state = State(
            revision=1,
            snapshot=self.snapshot,
            actions=[
                Action(id="act1", amount=4000, created_on=self.today, status="planned")  # €40.00
            ],
            debts=self.debts,
            transactions=self.transactions,
        )

    def test_get_financial_snapshot_populated_state(self):
        tool_out = get_financial_snapshot(self.state)

        self.assertTrue(tool_out["has_snapshot"])
        self.assertEqual(tool_out["balance_cents"], 100000)
        self.assertEqual(tool_out["balance_eur"], "€1,000")
        self.assertEqual(tool_out["protected_buffer_cents"], 10000)
        self.assertEqual(tool_out["protected_buffer_eur"], "€100")
        self.assertEqual(tool_out["obligations_30d_cents"], 80000)
        self.assertEqual(tool_out["obligations_30d_eur"], "€800")
        self.assertEqual(tool_out["obligations_total_cents"], 80000)
        self.assertEqual(tool_out["planned_step_cents"], 4000)
        self.assertEqual(tool_out["planned_step_eur"], "€40")
        self.assertEqual(tool_out["goal_target_cents"], 50000)
        self.assertEqual(tool_out["goal_remaining_cents"], 50000)
        self.assertEqual(tool_out["goal_remaining_eur"], "€500")
        self.assertEqual(tool_out["goal_name"], "Emergency fund")
        self.assertEqual(tool_out["as_of"], "2026-03-01")

        # Capacity: cash (100000) - saved(0) - protected(10000) - planned(4000) - bills(80000) = 6000
        self.assertEqual(tool_out["available_cents"], 6000)
        self.assertEqual(tool_out["available_eur"], "€60")

    def test_get_financial_snapshot_empty_state(self):
        empty_state = State()
        tool_out = get_financial_snapshot(empty_state)

        self.assertFalse(tool_out["has_snapshot"])
        self.assertEqual(tool_out["balance_cents"], 0)
        self.assertEqual(tool_out["available_cents"], 0)
        self.assertEqual(tool_out["obligations_30d_cents"], 0)
        self.assertEqual(tool_out["planned_step_cents"], 0)
        self.assertIsNone(tool_out["as_of"])

    def test_calculate_cash_flow_populated(self):
        cf = calculate_cash_flow(self.state, days=30)

        self.assertEqual(cf["days"], 30)
        self.assertEqual(cf["income_cents"], 240000)
        self.assertEqual(cf["income_eur"], "€2,400")
        # spending = REWE (6500) + Netflix (1599) + Spotify (999) = 9098 cents; transfers excluded
        self.assertEqual(cf["spending_cents"], 9098)
        self.assertEqual(cf["spending_eur"], "€90.98")
        self.assertEqual(cf["net_cash_flow_cents"], 240000 - 9098)
        self.assertEqual(cf["min_projected_balance_cents"], 6000)
        self.assertEqual(cf["min_projected_balance_eur"], "€60")

    def test_calculate_cash_flow_empty(self):
        empty_state = State()
        cf = calculate_cash_flow(empty_state, days=30)

        self.assertEqual(cf["income_cents"], 0)
        self.assertEqual(cf["spending_cents"], 0)
        self.assertEqual(cf["net_cash_flow_cents"], 0)
        self.assertEqual(cf["min_projected_balance_cents"], 0)

    def test_simulate_debt_payment_populated(self):
        debt_out = simulate_debt_payment(self.state, extra_payment_cents=20000)

        self.assertTrue(debt_out["has_debts"])
        self.assertEqual(debt_out["debt_count"], 2)
        self.assertEqual(debt_out["total_balance_cents"], 250000)  # €2,500.00
        self.assertEqual(debt_out["total_balance_eur"], "€2,500")
        self.assertEqual(debt_out["total_min_payment_cents"], 12500)  # €125.00
        self.assertEqual(debt_out["total_min_payment_eur"], "€125")

        self.assertIn("baseline", debt_out)
        self.assertIn("avalanche", debt_out)
        self.assertIn("snowball", debt_out)
        self.assertIsNotNone(debt_out["baseline"]["months"])
        self.assertIsNotNone(debt_out["avalanche"]["months"])

        # Avalanche interest should be <= snowball interest
        self.assertLessEqual(
            debt_out["avalanche"]["total_interest_cents"],
            debt_out["snowball"]["total_interest_cents"],
        )

        # One-off extra payment preview
        self.assertIsNotNone(debt_out["one_off_preview"])
        self.assertEqual(debt_out["one_off_preview"]["requested_extra_cents"], 20000)
        self.assertEqual(debt_out["one_off_preview"]["requested_extra_eur"], "€200")

    def test_simulate_debt_payment_empty(self):
        empty_state = State()
        debt_out = simulate_debt_payment(empty_state)

        self.assertFalse(debt_out["has_debts"])
        self.assertEqual(debt_out["debt_count"], 0)
        self.assertEqual(debt_out["total_balance_cents"], 0)
        self.assertEqual(debt_out["status"], "none")

    def test_get_spending_by_category_and_subscriptions(self):
        spending_out = get_spending_by_category(self.state, limit=5)

        self.assertEqual(spending_out["total_spending_cents"], 9098)
        self.assertEqual(spending_out["total_spending_eur"], "€90.98")

        categories = {c["category"]: c["amount_cents"] for c in spending_out["top_categories"]}
        self.assertEqual(categories["groceries"], 6500)
        self.assertEqual(categories["subscriptions"], 2598)

        # Check subscriptions list
        self.assertEqual(len(spending_out["subscriptions"]), 2)
        sub_descriptions = {s["description"] for s in spending_out["subscriptions"]}
        self.assertIn("Netflix subscription", sub_descriptions)
        self.assertIn("Spotify premium", sub_descriptions)
        self.assertEqual(spending_out["subscriptions_total_cents"], 2598)
        self.assertEqual(spending_out["subscriptions_total_eur"], "€25.98")

    def test_collect_all_tool_outputs(self):
        outputs = collect_all_tool_outputs(self.state)

        self.assertIn("snapshot", outputs)
        self.assertIn("cash_flow", outputs)
        self.assertIn("debt", outputs)
        self.assertIn("spending", outputs)
        self.assertTrue(outputs["snapshot"]["has_snapshot"])
        self.assertTrue(outputs["debt"]["has_debts"])

    def test_extract_tool_numbers_accuracy(self):
        outputs = collect_all_tool_outputs(self.state)
        valid_cents, valid_percents, valid_counts = extract_tool_numbers(outputs)

        # Cash €1,000 = 100,000 cents
        self.assertIn(100000, valid_cents)
        self.assertIn(1000, valid_counts)

        # Rent €600 = 60,000 cents
        self.assertIn(60000, valid_cents)

        # Card APR 18.50%
        self.assertIn(18.5, valid_percents)

        # Loan APR 6.00%
        self.assertIn(6.0, valid_percents)

        # Netflix €15.99 = 1599 cents
        self.assertIn(1599, valid_cents)

    def test_verify_reply_numbers_grounded_reply_passes(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = (
            "You have €1,000 in cash as of 2026-03-01. "
            "Your upcoming bills are €800 and your protected buffer is €100. "
            "You have €60 available to plan right now, and €40 is planned for your Emergency fund. "
            "Your Visa card has an APR of 18.5%. "
            "Over the last 30 days, your net cash flow was €2,309.02. "
            "Consider reviewing your plan in 14 days."
        )

        ok, unconfirmed = verify_reply_numbers(reply, outputs)
        self.assertTrue(ok, f"Expected verified, got unconfirmed: {unconfirmed}")
        self.assertEqual(len(unconfirmed), 0)

    def test_verify_reply_numbers_catches_hallucinated_currency(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "You can easily afford to invest €999.00 right now into crypto."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)

        self.assertFalse(ok)
        self.assertIn("€999.00", unconfirmed)

    def test_verify_reply_numbers_catches_hallucinated_percentage(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "Your credit card has an excessive interest rate of 29.9% APR."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)

        self.assertFalse(ok)
        self.assertIn("29.9%", unconfirmed)

    def test_verify_reply_numbers_catches_unconfirmed_plain_number(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "You have 8888 extra reward points in your account."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)

        self.assertFalse(ok)
        self.assertIn("8888", unconfirmed)

    def test_verify_reply_numbers_german_formatting(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "Ihr Guthaben beträgt 1.000 € und Ihre offenen Rechnungen liegen bei 800 € mit 18,5% Zinsen."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)
        self.assertTrue(ok, f"German formatting should pass, got: {unconfirmed}")

    def test_verify_reply_numbers_catches_suffix_currency_hallucination(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "You have 999 EUR left or about 750 euros."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)
        self.assertFalse(ok)
        self.assertTrue(any("999" in u for u in unconfirmed))
        self.assertTrue(any("750" in u for u in unconfirmed))

    def test_verify_reply_numbers_multiple_hallucinations(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = "Save €999.00 today at 29.9% APR and claim 7777 bonus points."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)
        self.assertFalse(ok)
        self.assertEqual(len(unconfirmed), 3)
        self.assertIn("€999.00", unconfirmed)
        self.assertIn("29.9%", unconfirmed)
        self.assertIn("7777", unconfirmed)

    def test_verify_reply_numbers_negative_and_zero_amounts(self):
        outputs = collect_all_tool_outputs(self.state)

        # 0 is always allowed, and -€50 matches internet bill or negative transactions
        reply = "You have €0 in saved funds and paid -€50 for broadband with 0% extra fee."
        ok, unconfirmed = verify_reply_numbers(reply, outputs)
        self.assertTrue(ok, f"Zero and negative should pass, got: {unconfirmed}")

    def test_state_view_compatibility(self):
        from vela.domain import view
        v = view(self.state, self.today)

        # Pass dictionary view to tools
        snap_out = get_financial_snapshot(v)
        self.assertTrue(snap_out["has_snapshot"])
        self.assertEqual(snap_out["balance_cents"], 100000)

        debt_out = simulate_debt_payment(v)
        self.assertTrue(debt_out["has_debts"])
        self.assertEqual(debt_out["debt_count"], 2)

    def test_verify_reply_numbers_markdown_formatting_and_dates(self):
        outputs = collect_all_tool_outputs(self.state)

        reply = (
            "### Summary for 15.03.2026\n"
            "1. Cash balance: **€1,000**\n"
            "2. Available buffer: *€60*\n"
            "3. Planned step: `€40`\n"
        )
        ok, unconfirmed = verify_reply_numbers(reply, outputs)

        self.assertTrue(ok, f"Markdown and list bullets should pass, got: {unconfirmed}")

    def test_verify_reply_numbers_empty_text(self):
        outputs = collect_all_tool_outputs(self.state)

        ok, unconfirmed = verify_reply_numbers("", outputs)
        self.assertTrue(ok)
        self.assertEqual(unconfirmed, [])


if __name__ == "__main__":
    unittest.main()
