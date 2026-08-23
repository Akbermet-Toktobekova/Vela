from models.schemas import UserFinancialProfile, MicroLesson
from typing import Dict, List

class MockDatabase:
    def __init__(self):
        self.profiles: Dict[str, UserFinancialProfile] = {
            "user_default": UserFinancialProfile()
        }
        self.lessons: List[MicroLesson] = [
            MicroLesson(
                id="lesson_1",
                title="The 50/30/20 Rule: Building Your Blueprint",
                category="Budgeting Basics",
                read_time_minutes=2,
                content="The 50/30/20 framework divides your after-tax income into three buckets: 50% for Needs (rent, utilities, groceries), 30% for Wants (dining out, hobbies, subscriptions), and 20% for Savings & Debt repayment beyond minimums. This simple benchmark protects you from lifestyle inflation while ensuring steady wealth accumulation.",
                key_takeaway="Prioritize your 50% Needs first, automate your 20% Savings on payday, and enjoy your 30% guilt-free.",
                quiz={
                    "question": "If you earn $3,000 net monthly, what is the recommended amount for Needs under 50/30/20?",
                    "options": [
                        {"id": "a", "text": "$900", "is_correct": False},
                        {"id": "b", "text": "$1,500", "is_correct": True},
                        {"id": "c", "text": "$600", "is_correct": False}
                    ],
                    "explanation": "50% of $3,000 = $1,500 dedicated to essential expenses (Needs)."
                }
            ),
            MicroLesson(
                id="lesson_2",
                title="Debt Avalanche vs. Debt Snowball",
                category="Debt Elimination",
                read_time_minutes=3,
                content="When tackling multiple debts, two main strategies stand out:\n\n1. **Debt Avalanche**: Pay minimums on everything, and aggressively funnel extra cash to the debt with the highest interest rate (APR). Mathematically saves the most money.\n2. **Debt Snowball**: Pay off the smallest balance first for psychological momentum and quick wins.",
                key_takeaway="Use Avalanche for maximum mathematical efficiency, or Snowball if you need behavioral motivation to stay consistent.",
                quiz={
                    "question": "Which debt strategy minimizes the total interest paid over time?",
                    "options": [
                        {"id": "a", "text": "Debt Avalanche (Highest APR first)", "is_correct": True},
                        {"id": "b", "text": "Debt Snowball (Smallest balance first)", "is_correct": False},
                        {"id": "c", "text": "Paying equal amounts to all debts", "is_correct": False}
                    ],
                    "explanation": "Debt Avalanche targets high-interest debt first, which directly cuts down total accumulated compound interest."
                }
            ),
            MicroLesson(
                id="lesson_3",
                title="Emergency Funds: Your Financial Shock Absorber",
                category="Savings & Safety",
                read_time_minutes=2,
                content="An emergency fund is 3 to 6 months of essential living expenses parked in a High-Yield Savings Account (HYSA). It prevents unexpected car repairs or medical bills from turning into high-interest credit card debt.",
                key_takeaway="Never invest your emergency fund in volatile assets; liquidity and capital preservation are the priorities.",
                quiz={
                    "question": "Where is the best place to keep your emergency fund?",
                    "options": [
                        {"id": "a", "text": "High-Yield Savings Account (HYSA)", "is_correct": True},
                        {"id": "b", "text": "Cryptocurrency or volatile stocks", "is_correct": False},
                        {"id": "c", "text": "Physical cash under a mattress", "is_correct": False}
                    ],
                    "explanation": "A High-Yield Savings Account keeps your cash liquid, insured, and earning yield against inflation."
                }
            )
        ]

    def get_profile(self, user_id: str) -> UserFinancialProfile:
        if user_id not in self.profiles:
            self.profiles[user_id] = UserFinancialProfile(user_id=user_id)
        return self.profiles[user_id]

    def update_profile(self, profile: UserFinancialProfile) -> UserFinancialProfile:
        self.profiles[profile.user_id] = profile
        return profile

    def get_daily_lesson(self) -> MicroLesson:
        return self.lessons[0]

    def get_all_lessons(self) -> List[MicroLesson]:
        return self.lessons

db = MockDatabase()
