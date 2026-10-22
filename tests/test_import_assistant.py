from finagent.assistant.chat import respond
from finagent.learning.lessons import lessons, select_lesson
from finagent.llm.client import CachedLLMClient, FakeLLMClient
from finagent.sources.csv_source import parse_csv
from finagent.sources.personas import ANCHOR, persona


def test_three_statement_formats():
    fixtures = [
        b"date,amount,description\n2026-10-01,-12.34,Tesco\n",
        "Dátum;Összeg;Leírás\n2026.10.01.;-1 234,56;Tesco\n".encode("cp1250"),
        b"date,debit,credit,description\n01/10/2026,12.34,,Tesco\n02/10/2026,,1000,Salary\n",
    ]
    results = [parse_csv(f, "P2") for f in fixtures]
    assert [r.transactions[0].amount for r in results] == [-1234, -123456, -1234]
    assert all(not r.errors for r in results)
    assert results[2].transactions[1].amount == 100000


def test_chat_tools_refusal_and_fallback():
    p = persona("P2")
    fake = FakeLLMClient()
    for message, tool in [
        ("Why this?", "get_recommendation_facts"),
        ("Show my history", "get_history"),
        ("My profile", "get_profile"),
        ("What if I pay $50 more?", "simulate_extra_payment"),
        ("What if I save $25 more?", "simulate_extra_payment"),
        ("What if my income decreases by 10%?", "simulate_income_change"),
    ]:
        assert respond(message, p, {"reason_facts": {"amount": 100}}, [], ANCHOR, fake)[
            "tools"
        ] == [tool]
    assert respond("Which stock should I buy?", p, None, [], ANCHOR, fake)["tools"] == []

    class Bad:
        def complete(self, prompt):
            return "You will save 999999999 dollars. You failed."

    assert respond("Why this?", p, {"reason_facts": {"amount": 100}}, [], ANCHOR, Bad())["fallback"]


def test_cache(tmp_path):
    class Counter:
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return "hello"

    counter = Counter()
    cached = CachedLLMClient(counter, "test", str(tmp_path))
    assert cached.complete("x") == cached.complete("x") == "hello"
    assert counter.calls == 1


def test_lesson_pool_no_repeats():
    assert len(lessons()) == 20
    for key in ["P1", "P2", "P3", "P4"]:
        p = persona(key)
        seen = []
        assert select_lesson(p, seen)["topic"] == p.priority
        for _ in range(20):
            chosen = select_lesson(p, seen)
            assert chosen["id"] not in seen
            assert 120 <= len(chosen["body"].split()) <= 180
            seen.append(chosen["id"])
        assert select_lesson(p, seen)


def test_contextual_lesson_triggers():
    assert select_lesson(persona("P1"), [], {"weekend_habit": True})["id"] == "lesson-06"
    assert select_lesson(persona("P4"), [], {"subscription_creep": True})["id"] == "lesson-07"
    assert select_lesson(persona("P3"), [], {"no_emergency": True})["id"] == "lesson-12"
