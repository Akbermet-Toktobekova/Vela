from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentType(str, Enum):
    COORDINATOR = "coordinator"
    BUDGET = "budget_specialist"
    DEBT = "debt_optimizer"
    SAVINGS = "savings_coach"
    MICROLEARNING = "financial_educator"

class ExpenseItem(BaseModel):
    category: str
    amount: float
    is_essential: bool = True

class DebtItem(BaseModel):
    name: str
    balance: float
    interest_rate: float
    minimum_payment: float

class SavingsGoal(BaseModel):
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[str] = None

class UserFinancialProfile(BaseModel):
    user_id: str = "user_default"
    monthly_income: float = 3500.0
    currency: str = "USD"
    expenses: List[ExpenseItem] = [
        ExpenseItem(category="Rent & Utilities", amount=1200.0, is_essential=True),
        ExpenseItem(category="Groceries", amount=450.0, is_essential=True),
        ExpenseItem(category="Dining & Entertainment", amount=350.0, is_essential=False),
        ExpenseItem(category="Subscriptions & Gym", amount=80.0, is_essential=False),
        ExpenseItem(category="Transport", amount=180.0, is_essential=True),
    ]
    debts: List[DebtItem] = [
        DebtItem(name="Credit Card A", balance=2400.0, interest_rate=21.5, minimum_payment=80.0),
        DebtItem(name="Student Loan", balance=8500.0, interest_rate=5.2, minimum_payment=150.0),
    ]
    savings_goals: List[SavingsGoal] = [
        SavingsGoal(name="Emergency Fund (3 Months)", target_amount=6000.0, current_amount=2800.0, target_date="2026-12-31"),
        SavingsGoal(name="Trip to Japan", target_amount=3000.0, current_amount=950.0, target_date="2027-05-01"),
    ]
    risk_tolerance: str = "moderate"

class ChatMessage(BaseModel):
    role: str
    content: str
    agent: Optional[AgentType] = None
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []
    user_id: str = "user_default"

class ChatResponse(BaseModel):
    reply: str
    agent_used: AgentType
    agent_name: str
    reasoning: Optional[str] = None
    action_items: Optional[List[str]] = []
    metrics: Optional[Dict[str, Any]] = None

class QuizOption(BaseModel):
    id: str
    text: str
    is_correct: bool

class MicroLesson(BaseModel):
    id: str
    title: str
    category: str
    read_time_minutes: int
    content: str
    key_takeaway: str
    quiz: Optional[Dict[str, Any]] = None
