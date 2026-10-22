from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from finagent.api.app import create_app
from finagent.persistence.store import put


@pytest.fixture
def client(tmp_path):
    app = create_app("sqlite:///" + str(tmp_path / "test.db"))
    with TestClient(app) as client:
        assert client.post("/api/v1/demo/P2").status_code == 200
        yield client


def test_full_flow_and_persistence(client):
    today = client.get("/api/v1/today").json()
    rec = today["recommendation"]
    assert rec["chosen"]["type"] == "extra_debt"
    assert (
        client.post(
            f"/api/v1/recommendations/{rec['id']}/adjust", json={"amount": 99999999}
        ).status_code
        == 422
    )
    response = client.post(f"/api/v1/recommendations/{rec['id']}/accept", json={})
    assert response.status_code == 200
    assert client.post(f"/api/v1/recommendations/{rec['id']}/accept", json={}).status_code == 422
    rules = client.get("/api/v1/rules").json()
    assert len(rules) == 1
    assert (
        client.patch("/api/v1/rules/" + rules[0]["id"], json={"status": "paused"}).status_code
        == 200
    )
    assert (
        client.patch(
            "/api/v1/rules/" + rules[0]["id"], json={"status": "active", "amount": 5000}
        ).status_code
        == 200
    )
    assert client.post("/api/v1/replay/advance", json={"days": 14}).status_code == 200
    events = client.get("/api/v1/history").json()
    assert any(e["type"] == "rule_run" for e in events)
    reopened = TestClient(create_app(str(client.app.state.service.store.engine.url)))
    assert reopened.get("/api/v1/profile").json()["name"] == "Alex"


def test_guard_and_daily_limit(client):
    rec = client.get("/api/v1/today").json()["recommendation"]
    assert (
        client.post("/api/v1/recommendations/refresh").json()["recommendation"]["id"] == rec["id"]
    )
    p = client.get("/api/v1/profile").json()
    p["cash_balance"] = 0
    assert client.put("/api/v1/profile", json=p).status_code == 200
    today = client.get("/api/v1/today").json()
    assert today["guard"] and today["recommendation"] is None and today["lesson"] is None
    assert client.post("/api/v1/recommendations/refresh").json()["recommendation"] is None
    p["cash_balance"] = 500000
    client.put("/api/v1/profile", json=p)
    assert client.get("/api/v1/today").json()["guard"]
    assert len(client.get("/api/v1/history?type=guard_suppression").json()) == 1


def test_concurrent_refresh_issues_once(client):
    service = client.app.state.service
    with service.store.transaction() as s:
        put(s, "recommendation", None)
        put(s, "last_issued", None)

    def refresh(_):
        with service.store.transaction() as s:
            return service.refresh(s)["id"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        ids = list(executor.map(refresh, range(8)))
    assert len(set(ids)) == 1


def test_decline_cooldown_and_adaptive(client):
    rec = client.get("/api/v1/today").json()["recommendation"]
    assert (
        client.post(
            f"/api/v1/recommendations/{rec['id']}/decline", json={"reason": "Later"}
        ).status_code
        == 200
    )
    client.post("/api/v1/replay/advance", json={"days": 1})
    new = client.post("/api/v1/recommendations/refresh").json()["recommendation"]
    if new and new["status"] == "pending":
        assert new["chosen"]["type"] != "extra_debt"
    p = client.get("/api/v1/profile").json()
    p["monthly_income"] = 390000
    client.put("/api/v1/profile", json=p)
    events = client.get("/api/v1/history?type=plan_change").json()
    assert events[0]["payload"]["recomputes"] == 1


def test_assumption_lesson_import_delete(client):
    assert (
        client.post("/api/v1/assumptions/confirm", json={"merchant": "Spotify"}).status_code == 200
    )
    p = client.get("/api/v1/profile").json()
    assert any(c["name"] == "Spotify" for c in p["fixed_costs"])
    lesson = client.get("/api/v1/lessons/today").json()["lesson"]
    assert (
        client.post("/api/v1/lessons/" + lesson["id"] + "/answer", json={"answer": 0}).status_code
        == 200
    )
    assert (
        client.post("/api/v1/lessons/" + lesson["id"] + "/answer", json={"answer": 1}).status_code
        == 200
    )
    assert len(client.get("/api/v1/history?type=lesson_completed").json()) == 1
    response = client.post(
        "/api/v1/import/statement",
        files={
            "file": (
                "statement.csv",
                b"date,amount,description\n2026-10-20,-12.50,Tesco\nbad,foo,x\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    assert response.json()["imported"] == 1 and len(response.json()["errors"]) == 1
    again = client.post(
        "/api/v1/import/statement",
        files={
            "file": (
                "statement.csv",
                b"date,amount,description\n2026-10-20,-12.50,Tesco\nbad,foo,x\n",
                "text/csv",
            )
        },
    )
    assert again.json()["imported"] == 0
    assert client.delete("/api/v1/data").json() == {"deleted": True}
    assert client.get("/api/v1/profile").status_code == 422


def test_validation_and_adjust(client):
    p = client.get("/api/v1/profile").json()
    p["monthly_income"] = -1
    assert client.put("/api/v1/profile", json=p).status_code == 422
    rec = client.get("/api/v1/today").json()["recommendation"]
    assert (
        client.post(
            f"/api/v1/recommendations/{rec['id']}/adjust", json={"amount": 5000, "schedule_day": 15}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/rules").json()[0]["trigger"]["value"] == "15"
    assert client.post(
        "/api/v1/assistant/messages", json={"message": "What if I pay $50 more toward debt?"}
    ).json()["tools"] == ["simulate_extra_payment"]


def test_adjustment_recalculates_numbers_and_schedule_runs(client):
    rec = client.get("/api/v1/today").json()["recommendation"]
    response = client.post(
        f"/api/v1/recommendations/{rec['id']}/adjust", json={"amount": 5000, "schedule_day": 25}
    )
    adjusted = response.json()
    assert adjusted["reason_facts"]["amount"] == 5000
    assert adjusted["reason_facts"]["interest_saved"] < rec["reason_facts"]["interest_saved"]
    assert client.post("/api/v1/replay/advance", json={"days": 4}).status_code == 200
    events = client.get("/api/v1/history?type=rule_run").json()
    assert len(events) == 1
    assert events[0]["payload"]["executed_at"] == "2026-10-25"
    assert events[0]["payload"]["amount"] == 5000


def test_statement_mapping_errors_are_explicit(client):
    response = client.post(
        "/api/v1/import/statement",
        files={"file": ("a.csv", b"date,amount\n2026-01-01,10\n")},
        data={"mapping": "[]"},
    )
    assert response.status_code == 422


def test_guard_persists_through_mid_batch_recovery(client):
    from finagent.domain.models import Transaction

    service = client.app.state.service
    with service.store.transaction() as s:
        p = service.profile(s)
        p.cash_balance = 50000
        put(s, "profile", p.to_dict())
        service.ingest(
            s,
            [
                Transaction(
                    "shock", "P2", "2026-10-23", -1000, "shock", "shock", "other", "replay"
                ),
                Transaction(
                    "recover", "P2", "2026-10-24", 100000, "income", "Income", "income", "replay"
                ),
            ],
            True,
        )
    today = client.get("/api/v1/today").json()
    assert today["guard"] and today["recommendation"] is None


def test_deduplicate_within_batch_and_protect_rule_account(client):
    from finagent.domain.models import Transaction

    service = client.app.state.service
    with service.store.transaction() as s:
        t = Transaction("same", "P2", "2026-10-23", 100, "income", "Income", "income", "replay")
        assert service.ingest(s, [t, t], True) == 1
    rec = client.post("/api/v1/recommendations/refresh").json()["recommendation"]
    if rec["status"] == "pending":
        client.post(f"/api/v1/recommendations/{rec['id']}/accept", json={})
        p = client.get("/api/v1/profile").json()
        p["debts"] = []
        assert client.put("/api/v1/profile", json=p).status_code == 422


def test_conversational_correction_and_adaptive_dates(client):
    response = client.post(
        "/api/v1/assistant/messages", json={"message": "Confirm Spotify is a recurring cost"}
    )
    assert response.status_code == 200
    assert response.json()["tools"] == ["confirm_recurring_assumption"]
    response = client.post(
        "/api/v1/assistant/messages", json={"message": "Set my monthly income to $5000"}
    )
    assert response.status_code == 200
    assert client.get("/api/v1/profile").json()["monthly_income"] == 500000
    today = client.get("/api/v1/today").json()
    assert (
        today["timeline_change"]["before"]["projected_date"]
        != today["timeline_change"]["after"]["projected_date"]
    )
    assert (
        client.post(
            "/api/v1/assistant/messages", json={"message": "What if my income decreases by 10%?"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/profile").json()["monthly_income"] == 500000
