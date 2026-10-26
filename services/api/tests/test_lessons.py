"""Tests for Journey E: Lessons API, contextual recommendation matching, idempotent progress, and data erasure (T18)."""

from datetime import date
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from fastapi.testclient import TestClient
from vela.domain import Debt, Obligation, Snapshot, State, fixture
from vela.lessons import (
    get_lesson_detail,
    list_lessons,
    load_lessons_index,
    record_lesson_progress,
)
from vela.main import create_app

TODAY = date(2026, 10, 26)
TOKEN = "test-only-token-at-least-24-characters"


class TestLessonsDomainAndCatalog(unittest.TestCase):
    """Unit tests for lesson loading, markdown parsing, and contextual recommendation matching."""

    def test_load_all_10_lessons_and_verify_unreviewed_flag(self):
        items = load_lessons_index()
        self.assertEqual(len(items), 10)
        for item in items:
            self.assertFalse(item.reviewed, f"Lesson {item.id} must have reviewed=False until human review")
            self.assertTrue(item.title)
            self.assertTrue(item.summary)
            self.assertGreater(len(item.related_actions), 0)
            self.assertEqual(len(item.quiz.options), 3)
            self.assertIn(item.quiz.correct_index, (0, 1, 2))

    def test_contextual_lessons_match_state_recommendation(self):
        # 1. Empty snapshot -> clarify_material_unknown ->irregular-income-budget / understanding-bank-statements
        empty_state = State(snapshot=None)
        view_empty = list_lessons(empty_state, TODAY)
        self.assertEqual(view_empty.active_action_id, "clarify_material_unknown")
        self.assertIsNotNone(view_empty.recommended_lesson)
        self.assertIn(
            "clarify_material_unknown",
            view_empty.recommended_lesson.related_actions,
        )

        # 2. Shortfall state -> external_assistance_shortfall -> dealing-with-shortfall
        short_snap = fixture(TODAY)
        short_snap.cash = 50_000
        short_state = State(snapshot=short_snap)
        view_short = list_lessons(short_state, TODAY)
        self.assertEqual(view_short.active_action_id, "external_assistance_shortfall")
        self.assertIsNotNone(view_short.recommended_lesson)
        self.assertEqual(view_short.recommended_lesson.id, "dealing-with-shortfall")

        # 3. High-APR debt state -> extra_debt_payment_one_off -> apr-and-minimum-payment / avalanche-vs-snowball
        debt_state = State(
            snapshot=fixture(TODAY),
            debts=[
                Debt(
                    id="visa",
                    label="Visa",
                    balance_cents=50_000,
                    apr_bps=2400,
                    min_payment_cents=2_000,
                    due_day=25,
                    terms_known=True,
                )
            ],
        )
        view_debt = list_lessons(debt_state, TODAY)
        self.assertIsNotNone(view_debt.recommended_lesson)
        self.assertIn(
            view_debt.active_action_id,
            view_debt.recommended_lesson.related_actions,
        )

        # 4. Explicit action_id filter selects matching related_actions
        view_sub = list_lessons(empty_state, TODAY, action_id="review_recurring_charge")
        self.assertEqual(view_sub.active_action_id, "review_recurring_charge")
        self.assertEqual(
            [l.id for l in view_sub.recommended_lessons],
            ["subscriptions-and-recurring"],
        )

    def test_recommended_lesson_advances_to_next_uncompleted_related_lesson(self):
        state = State(snapshot=None)
        first_view = list_lessons(state, TODAY, action_id="contribute_savings_goal")
        related_ids = [l.id for l in first_view.recommended_lessons]
        self.assertGreaterEqual(len(related_ids), 2)
        first_rec_id = first_view.recommended_lesson.id
        self.assertEqual(first_rec_id, related_ids[0])

        # Complete the first recommended lesson; recommended_lesson should advance to the next uncompleted one
        record_lesson_progress(state, first_rec_id, TODAY, selected_index=1, completed=True)
        second_view = list_lessons(state, TODAY, action_id="contribute_savings_goal")
        self.assertEqual(second_view.completed_count, 1)
        self.assertEqual(second_view.recommended_lesson.id, related_ids[1])


class TestLessonsAPIEndpoints(unittest.TestCase):
    """Integration tests for GET /v1/lessons, GET /v1/lessons/{id}, POST /v1/lessons/{id}/progress, and DELETE /v1/data."""

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app(
            database_url=f"sqlite:///{Path(self.tmp.name) / 'test.db'}",
            demo_token=TOKEN,
            today=lambda: TODAY,
            local_dir=Path(self.tmp.name),
        )
        self.addCleanup(self.app.state.store.engine.dispose)
        self.client = TestClient(self.app)
        self.headers = {"Authorization": f"Bearer {TOKEN}"}

    def test_get_lessons_and_lesson_detail(self):
        res = self.client.get("/v1/lessons", headers=self.headers)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["total_count"], 10)
        self.assertEqual(body["completed_count"], 0)
        self.assertEqual(len(body["lessons"]), 10)
        self.assertIsNotNone(body["recommended_lesson"])

        # Fetch a specific lesson detail
        detail_res = self.client.get("/v1/lessons/emergency-fund", headers=self.headers)
        self.assertEqual(detail_res.status_code, 200, detail_res.text)
        detail = detail_res.json()
        self.assertEqual(detail["id"], "emergency-fund")
        self.assertFalse(detail["completed"])
        self.assertFalse(detail["reviewed"])
        self.assertIn("emergency cushion", detail["body_markdown"].lower())
        self.assertGreater(len(detail["paragraphs"]), 2)
        self.assertEqual(detail["quiz"]["correct_index"], 1)

        # Unknown lesson returns 404
        missing_res = self.client.get("/v1/lessons/non-existent-lesson", headers=self.headers)
        self.assertEqual(missing_res.status_code, 404)

    def test_post_lesson_progress_idempotency_and_persistence(self):
        # 1. Submit quiz answer and mark completed with Idempotency-Key
        idem_headers = {**self.headers, "Idempotency-Key": "lesson-prog-key-0001"}
        post1 = self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers=idem_headers,
            json={"selected_index": 1, "completed": True},
        )
        self.assertEqual(post1.status_code, 200, post1.text)
        d1 = post1.json()
        self.assertTrue(d1["completed"])
        self.assertEqual(d1["selected_index"], 1)
        self.assertTrue(d1["correct"])
        self.assertEqual(d1["completed_on"], TODAY.isoformat())

        # 2. Retry with the exact same Idempotency-Key -> returns identical response without error
        post2 = self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers=idem_headers,
            json={"selected_index": 1, "completed": True},
        )
        self.assertEqual(post2.status_code, 200, post2.text)
        self.assertEqual(post1.json(), post2.json())

        # 3. Retry with a different Idempotency-Key (or without Idempotency-Key) and same payload -> still idempotent, count stays 1
        post3 = self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers={**self.headers, "Idempotency-Key": "lesson-prog-key-0002"},
            json={"selected_index": 1, "completed": True},
        )
        self.assertEqual(post3.status_code, 200, post3.text)
        self.assertTrue(post3.json()["completed"])

        list_res = self.client.get("/v1/lessons", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.json()["completed_count"], 1)

        # 4. Reusing the first Idempotency-Key with different payload -> 409 Conflict
        conflict_res = self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers=idem_headers,
            json={"selected_index": 0, "completed": True},
        )
        self.assertEqual(conflict_res.status_code, 409)

        # 5. Out-of-range selected_index -> 422
        bad_idx = self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers={**self.headers, "Idempotency-Key": "lesson-prog-bad-idx"},
            json={"selected_index": 9, "completed": True},
        )
        self.assertEqual(bad_idx.status_code, 422)

    def test_delete_data_erases_all_lesson_progress(self):
        # Complete two lessons
        self.client.post(
            "/v1/lessons/emergency-fund/progress",
            headers={**self.headers, "Idempotency-Key": "erase-test-key-0001"},
            json={"selected_index": 1, "completed": True},
        )
        self.client.post(
            "/v1/lessons/avalanche-vs-snowball/progress",
            headers={**self.headers, "Idempotency-Key": "erase-test-key-0002"},
            json={"selected_index": 0, "completed": True},
        )

        before = self.client.get("/v1/lessons", headers=self.headers).json()
        self.assertEqual(before["completed_count"], 2)

        # Erase all user data via DELETE /v1/data
        del_res = self.client.delete("/v1/data", headers=self.headers)
        self.assertEqual(del_res.status_code, 200)

        # Verify lesson progress is completely reset
        after = self.client.get("/v1/lessons", headers=self.headers).json()
        self.assertEqual(after["completed_count"], 0)
        for lesson in after["lessons"]:
            self.assertFalse(lesson["completed"])
            self.assertIsNone(lesson["selected_index"])
            self.assertIsNone(lesson["correct"])
            self.assertIsNone(lesson["completed_on"])


if __name__ == "__main__":
    unittest.main()
