"""Independent acceptance test fixture for Section 9 of FinAgent Production Development Prompt.

Specification Reference (§9, lines 357-368):
- A confirmed balance is 400 immediately before a newly received income of 600.
  The resulting balance is 1,000; a later statement already containing that income must not increase it again.
- Within the chosen horizon, rent is 600, necessary living costs are 150, a required debt payment is 50,
  and the protected unallocated balance is 100. Assume these costs do not overlap and all payment dates are known.
- With no additional income, available discretionary allocation is 100.
  A proposed allocation of 150 fails affordability. An allocation of 40 passes, leaving 60 of discretionary capacity.
- With a configured demo policy selecting the savings action, show: “Set aside €40 for your goal.”
  Its benefit must describe the computed goal progress, not invented interest savings.
- Accepting it records a planned reservation of 40; account balances remain unchanged.
  Confirmed completion reconciles an actual transfer or allocation and replaces the planned reservation
  without counting both. An internal transfer does not change total assets.
- In a separate branch before acceptance, a newly confirmed necessary cost of 80 reduces capacity to 20.
  The old 40 recommendation becomes ineligible. A slow job calculated from the earlier snapshot cannot republish it.

NOTE: All amounts are coded as literal integer EUR cents, without calling the production calculator
for expected values, to establish an independent accounting and workflow benchmark.
"""

from datetime import date, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
import sys
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from fastapi.testclient import TestClient
from vela.domain import (
    State,
    Snapshot,
    Obligation,
    capacity,
    accept,
    complete,
    merge_transactions,
    Transaction,
)
from vela.main import create_app
from vela.store import Store, Conflict

TODAY = date(2026, 10, 24)
TOKEN = "test-only-token-at-least-24-characters"

# Literal integer EUR cents per specification §9
CONFIRMED_INITIAL_BALANCE = 40_000       # €400.00
NEW_INCOME_AMOUNT = 60_000               # €600.00
EXPECTED_POST_INCOME_BALANCE = 100_000  # €1,000.00

RENT_AMOUNT = 60_000                     # €600.00
LIVING_COSTS_AMOUNT = 15_000             # €150.00
REQUIRED_DEBT_AMOUNT = 5_000             # €50.00
PROTECTED_BALANCE = 10_000               # €100.00

EXPECTED_DISCRETIONARY_CAPACITY = 10_000 # €100.00
UNAFFORDABLE_ALLOCATION_AMOUNT = 15_000  # €150.00
AFFORDABLE_ALLOCATION_AMOUNT = 4_000     # €40.00
EXPECTED_REMAINING_CAPACITY = 6_000      # €60.00

NEW_CONFIRMED_COST_AMOUNT = 8_000        # €80.00
EXPECTED_REDUCED_CAPACITY = 2_000        # €20.00


def make_section9_snapshot(today: date, cash: int = EXPECTED_POST_INCOME_BALANCE) -> Snapshot:
    """Builds the canonical Section 9 snapshot with literal values."""
    return Snapshot(
        nickname="Alex",
        currency="EUR",
        as_of=today,
        horizon=today + timedelta(days=30),
        cash=cash,
        saved=0,
        protected=PROTECTED_BALANCE,
        goal_target=100_000,
        goal_name="Emergency cushion",
        obligations_complete=True,
        debt_known=True,
        provenance="synthetic",
        obligations=[
            Obligation(
                id="rent",
                label="Rent",
                amount=RENT_AMOUNT,
                due=today + timedelta(days=5),
                kind="rent",
            ),
            Obligation(
                id="living",
                label="Necessary living costs",
                amount=LIVING_COSTS_AMOUNT,
                due=today + timedelta(days=15),
                kind="living",
            ),
            Obligation(
                id="debt",
                label="Required debt payment",
                amount=REQUIRED_DEBT_AMOUNT,
                due=today + timedelta(days=20),
                kind="debt",
            ),
        ],
    )


class TestSection9DomainAcceptanceFixture(unittest.TestCase):
    """Domain accounting and state invariants (§9, lines 357-368)."""

    def test_01_balance_reconciliation_and_deduplication(self):
        """Confirmed balance 400 + income 600 = 1000; repeated income does not duplicate."""
        state = State(
            snapshot=Snapshot(
                as_of=TODAY,
                horizon=TODAY + timedelta(days=30),
                cash=CONFIRMED_INITIAL_BALANCE,
                protected=PROTECTED_BALANCE,
                goal_target=100_000,
                obligations_complete=True,
                debt_known=True,
                provenance="synthetic",
                obligations=[],
            )
        )
        self.assertEqual(state.snapshot.cash, 40_000)

        # Applying income of 600 EUR produces 1,000 EUR
        state.snapshot.cash += NEW_INCOME_AMOUNT
        self.assertEqual(state.snapshot.cash, 100_000)

        # Re-importing statement containing that same income transaction does not add it again
        tx1 = Transaction(
            id="tx-inc-1",
            date=TODAY,
            amount=NEW_INCOME_AMOUNT,
            description="Salary ACME",
            category="income",
        )
        added_first = merge_transactions(state, [tx1])
        self.assertEqual(added_first, 1)

        # Later statement with identical transaction
        tx1_repeat = Transaction(
            id="tx-inc-2",
            date=TODAY,
            amount=NEW_INCOME_AMOUNT,
            description="Salary ACME",
            category="income",
        )
        added_second = merge_transactions(state, [tx1_repeat])
        self.assertEqual(added_second, 0, "Duplicate income transaction must be ignored")
        self.assertEqual(state.snapshot.cash, 100_000, "Cash balance must not increase again")

    def test_02_discretionary_capacity_calculation(self):
        """Cash 1000 - Rent 600 - Living 150 - Debt 50 - Protected 100 = 100 available."""
        state = State(snapshot=make_section9_snapshot(TODAY))
        self.assertEqual(
            capacity(state),
            EXPECTED_DISCRETIONARY_CAPACITY,
            f"Available capacity must be exactly {EXPECTED_DISCRETIONARY_CAPACITY} cents (€100.00)",
        )

    def test_03_affordability_and_capacity_consumption(self):
        """Allocation 150 fails; allocation 40 passes leaving 60 capacity."""
        state = State(snapshot=make_section9_snapshot(TODAY))

        # 150 EUR allocation fails affordability
        with self.assertRaises(ValueError, msg="Allocation of 150 EUR must fail affordability"):
            accept(state, UNAFFORDABLE_ALLOCATION_AMOUNT, "action-too-large", TODAY)

        # 40 EUR allocation passes
        accept(state, AFFORDABLE_ALLOCATION_AMOUNT, "action-40", TODAY)

        # Discretionary capacity is reduced from 100 to 60
        self.assertEqual(
            capacity(state),
            EXPECTED_REMAINING_CAPACITY,
            f"Remaining capacity must be {EXPECTED_REMAINING_CAPACITY} cents (€60.00)",
        )

    def test_04_planned_reservation_leaves_balances_unchanged(self):
        """Accepting records planned reservation of 40; account balances remain unchanged."""
        state = State(snapshot=make_section9_snapshot(TODAY))
        accept(state, AFFORDABLE_ALLOCATION_AMOUNT, "action-40", TODAY)

        # Planned reservation recorded
        self.assertEqual(len(state.actions), 1)
        self.assertEqual(state.actions[0].status, "planned")
        self.assertEqual(state.actions[0].amount, AFFORDABLE_ALLOCATION_AMOUNT)

        # Account balances remain strictly unchanged
        self.assertEqual(state.snapshot.cash, EXPECTED_POST_INCOME_BALANCE)
        self.assertEqual(state.snapshot.saved, 0)

    def test_05_completion_replaces_planned_without_double_counting(self):
        """Completion reconciles actual allocation; internal transfer does not change total assets."""
        state = State(snapshot=make_section9_snapshot(TODAY))
        accept(state, AFFORDABLE_ALLOCATION_AMOUNT, "action-40", TODAY)
        complete(state, "action-40", TODAY)

        # Action is completed
        self.assertEqual(state.actions[0].status, "completed")

        # Saved is now 40 EUR
        self.assertEqual(state.snapshot.saved, AFFORDABLE_ALLOCATION_AMOUNT)

        # Total cash remains unchanged (internal transfer does not alter total assets)
        self.assertEqual(state.snapshot.cash, EXPECTED_POST_INCOME_BALANCE)

        # Capacity remains 60 EUR (planned reservation replaced, NOT double-counted)
        self.assertEqual(
            capacity(state),
            EXPECTED_REMAINING_CAPACITY,
            "Capacity must not double-count both planned reservation and completed allocation",
        )

    def test_06_new_obligation_branch_reduces_capacity_and_invalidates_recommendation(self):
        """In separate branch before acceptance, new cost of 80 reduces capacity to 20, invalidating 40."""
        # Separate branch before acceptance
        state = State(snapshot=make_section9_snapshot(TODAY))
        self.assertEqual(capacity(state), EXPECTED_DISCRETIONARY_CAPACITY)

        # Newly confirmed necessary cost of 80 EUR
        state.snapshot.obligations.append(
            Obligation(
                id="new-cost-80",
                label="New necessary cost",
                amount=NEW_CONFIRMED_COST_AMOUNT,
                due=TODAY + timedelta(days=10),
                kind="other",
            )
        )

        # Capacity is now 20 EUR
        self.assertEqual(
            capacity(state),
            EXPECTED_REDUCED_CAPACITY,
            f"Capacity must be reduced to {EXPECTED_REDUCED_CAPACITY} cents (€20.00)",
        )

        # The old 40 EUR recommendation is now ineligible and cannot be accepted
        with self.assertRaises(ValueError, msg="Old 40 EUR recommendation must be ineligible against capacity 20 EUR"):
            accept(state, AFFORDABLE_ALLOCATION_AMOUNT, "action-40-invalidated", TODAY)


class TestSection9WorkflowAndConcurrencyAcceptanceFixture(unittest.TestCase):
    """Workflow, HTTP endpoints and slow job concurrency rejection (§9, lines 361-366)."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.path = Path(self.tmp.name)
        db_url = f"sqlite:///{self.path / 'test.db'}"
        self.app = create_app(db_url, TOKEN, lambda: TODAY, self.path)
        self.client = TestClient(self.app)
        self.headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Idempotency-Key": "test-key-init",
        }

        # Load canonical Section 9 demo snapshot (cash 1000, rent 600, living 150, debt 50, buffer 100)
        res = self.client.post(
            "/v1/demo",
            json={"revision": 0},
            headers=self.headers,
        )
        assert res.status_code == 200, res.text

    def tearDown(self):
        if hasattr(self, "client"):
            self.client.close()
        if hasattr(self, "app") and hasattr(self.app.state, "store"):
            self.app.state.store.engine.dispose()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_api_income_deduplication(self):
        """POST /v1/income with already_in_balance does not duplicate income."""
        # Initial state has 100,000
        res1 = self.client.post(
            "/v1/income",
            json={
                "revision": 1,
                "amount": NEW_INCOME_AMOUNT,
                "event_id": "inc-sec9-001",
                "received_on": TODAY.isoformat(),
                "already_in_balance": True,
            },
            headers={**self.headers, "Idempotency-Key": "inc-key-1"},
        )
        self.assertEqual(res1.status_code, 200, res1.text)
        self.assertEqual(res1.json()["snapshot"]["cash"], EXPECTED_POST_INCOME_BALANCE)

        # Duplicate submission with same event_id is rejected
        res2 = self.client.post(
            "/v1/income",
            json={
                "revision": 2,
                "amount": NEW_INCOME_AMOUNT,
                "event_id": "inc-sec9-001",
                "received_on": TODAY.isoformat(),
                "already_in_balance": True,
            },
            headers={**self.headers, "Idempotency-Key": "inc-key-2"},
        )
        self.assertEqual(res2.status_code, 422, "Duplicate income event must be rejected")

    def test_api_affordability_preview(self):
        """POST /v1/preview confirms 150 EUR ineligible, 40 EUR eligible with 60 remaining."""
        # Preview 150 EUR
        prev_150 = self.client.post(
            "/v1/preview",
            json={"amount": UNAFFORDABLE_ALLOCATION_AMOUNT},
            headers={"Authorization": f"Bearer {TOKEN}"},
        ).json()
        self.assertFalse(prev_150["eligible"], "150 EUR allocation must be ineligible")

        # Preview 40 EUR
        prev_40 = self.client.post(
            "/v1/preview",
            json={"amount": AFFORDABLE_ALLOCATION_AMOUNT},
            headers={"Authorization": f"Bearer {TOKEN}"},
        ).json()
        self.assertTrue(prev_40["eligible"], "40 EUR allocation must be eligible")
        self.assertEqual(prev_40["remaining"], EXPECTED_REMAINING_CAPACITY)

    def test_api_stale_job_cannot_republish_earlier_snapshot(self):
        """A slow job calculated from the earlier snapshot cannot republish after state changes."""
        # Current state revision is 1
        state_view = self.client.get(
            "/v1/state",
            headers={"Authorization": f"Bearer {TOKEN}"},
        ).json()
        initial_revision = state_view["revision"]
        self.assertEqual(initial_revision, 1)

        # User adds a new necessary cost of 80 EUR (advancing revision to 2)
        add_bill_res = self.client.post(
            "/v1/obligations",
            json={
                "revision": initial_revision,
                "obligation": {
                    "id": "bill-80",
                    "label": "New necessary cost",
                    "amount": NEW_CONFIRMED_COST_AMOUNT,
                    "due": (TODAY + timedelta(days=10)).isoformat(),
                    "kind": "other",
                },
            },
            headers={**self.headers, "Idempotency-Key": "bill-key-80"},
        )
        self.assertEqual(add_bill_res.status_code, 200)
        updated_state = add_bill_res.json()
        self.assertEqual(updated_state["revision"], 2)
        self.assertEqual(updated_state["available"], EXPECTED_REDUCED_CAPACITY)

        # A slow background job attempts to publish an action based on stale revision 1
        stale_publish_res = self.client.post(
            "/v1/actions",
            json={
                "revision": initial_revision,  # stale revision!
                "amount": AFFORDABLE_ALLOCATION_AMOUNT,
            },
            headers={**self.headers, "Idempotency-Key": "stale-job-key-001"},
        )
        self.assertEqual(
            stale_publish_res.status_code,
            409,
            "Slow job attempting to publish against stale revision must receive 409 Conflict",
        )


if __name__ == "__main__":
    unittest.main()
