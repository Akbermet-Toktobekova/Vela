import re
from typing import Optional
from models.schemas import UserFinancialProfile, ChatResponse, AgentType, ChatRequest
from agents.budget_agent import BudgetSpecialistAgent
from agents.debt_agent import DebtOptimizerAgent
from agents.savings_agent import SavingsCoachAgent
from core.config import settings

class CoordinatorAgent:
    name: str = "Vela Coordinator"
    agent_type: AgentType = AgentType.COORDINATOR

    def __init__(self):
        self.budget_agent = BudgetSpecialistAgent()
        self.debt_agent = DebtOptimizerAgent()
        self.savings_agent = SavingsCoachAgent()

    def route_and_respond(self, request: ChatRequest, profile: UserFinancialProfile) -> ChatResponse:
        query = request.message.lower().strip()

        # Intent Classification Keyword Routing
        debt_keywords = ["debt", "credit card", "loan", "pay off", "interest", "apr", "avalanche", "snowball", "liabilities"]
        budget_keywords = ["budget", "spend", "expenses", "needs", "wants", "50/30/20", "cash flow", "income", "bills", "groceries"]
        savings_keywords = ["save", "savings", "goal", "emergency fund", "invest", "hysa", "target", "vacation", "japan"]

        if any(k in query for k in debt_keywords):
            return self.debt_agent.analyze(profile, request.message)
        elif any(k in query for k in budget_keywords):
            return self.budget_agent.analyze(profile, request.message)
        elif any(k in query for k in savings_keywords):
            return self.savings_agent.analyze(profile, request.message)
        else:
            # Holistic coordinator response
            total_expenses = sum(e.amount for e in profile.expenses)
            surplus = profile.monthly_income - total_expenses
            total_debt = sum(d.balance for d in profile.debts)
            total_savings = sum(g.current_amount for g in profile.savings_goals)

            reply = (
                f"👋 **Hello! I am Vela, your Personal Multi-Agent Financial Advisor.**\n\n"
                f"I continuously coordinate with your specialized agents to guide your financial journey:\n\n"
                f"• **Monthly Cash Flow:** ${surplus:,.2f} surplus available (`Budget Specialist`)\n"
                f"• **Outstanding Debt:** ${total_debt:,.2f} total balance (`Debt Optimizer`)\n"
                f"• **Savings Accumulated:** ${total_savings:,.2f} across all goals (`Savings Coach`)\n\n"
                f"What would you like to focus on today? You can ask me:\n"
                f"1. *\"How should I optimize my budget?\"*\n"
                f"2. *\"What is my fastest strategy to pay off debt?\"*\n"
                f"3. *\"How on track are my savings goals?\"*"
            )

            return ChatResponse(
                reply=reply,
                agent_used=self.agent_type,
                agent_name=self.name,
                reasoning="Provided holistic financial summary and directed user to specialized agent workflows.",
                action_items=[
                    "Select a financial priority to deep-dive.",
                    "Complete today's 2-minute Micro-Learning lesson."
                ]
            )

coordinator = CoordinatorAgent()
