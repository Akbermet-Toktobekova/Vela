from models.schemas import UserFinancialProfile, ChatResponse, AgentType
from typing import Dict, Any

class BudgetSpecialistAgent:
    name: str = "Budget Specialist"
    agent_type: AgentType = AgentType.BUDGET
    role_description: str = "Expert in cash flow optimization, expense categorization, and the 50/30/20 budget framework."

    def analyze(self, profile: UserFinancialProfile, user_query: str) -> ChatResponse:
        total_income = profile.monthly_income
        essential_expenses = sum(e.amount for e in profile.expenses if e.is_essential)
        discretionary_expenses = sum(e.amount for e in profile.expenses if not e.is_essential)
        total_expenses = essential_expenses + discretionary_expenses
        net_cash_flow = total_income - total_expenses
        
        needs_pct = (essential_expenses / total_income * 100) if total_income > 0 else 0
        wants_pct = (discretionary_expenses / total_income * 100) if total_income > 0 else 0
        savings_available = max(0.0, net_cash_flow)
        savings_pct = (savings_available / total_income * 100) if total_income > 0 else 0

        reply = (
            f"📊 **Cash Flow & Budget Analysis**\n\n"
            f"Here is how your current monthly budget shapes up compared to the ideal **50/30/20 standard**:\n\n"
            f"• **Needs (Essentials):** ${essential_expenses:,.2f} ({needs_pct:.1f}% vs. 50% target)\n"
            f"• **Wants (Discretionary):** ${discretionary_expenses:,.2f} ({wants_pct:.1f}% vs. 30% target)\n"
            f"• **Available Cash Flow:** ${net_cash_flow:,.2f} ({savings_pct:.1f}%)\n\n"
        )

        if needs_pct > 55:
            reply += "⚠️ *Insight:* Your fixed essential costs are slightly above the 50% threshold. Consider renegotiating utility rates or recurring bills.\n"
        elif wants_pct > 35:
            reply += "💡 *Insight:* Your discretionary spending is eating into your savings capacity. Trimming $100-$150 here can accelerate your debt payoff or investments.\n"
        else:
            reply += "✅ *Great job:* Your expense ratios are well-balanced and provide a healthy monthly surplus for your financial goals!\n"

        action_items = [
            f"Allocate at least ${savings_available * 0.6:,.2f} towards high-priority debt or emergency reserve.",
            "Review non-essential subscription services this month."
        ]

        metrics = {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_surplus": net_cash_flow,
            "needs_ratio": round(needs_pct, 1),
            "wants_ratio": round(wants_pct, 1),
            "savings_ratio": round(savings_pct, 1)
        }

        return ChatResponse(
            reply=reply,
            agent_used=self.agent_type,
            agent_name=self.name,
            reasoning="Analyzed recurring expenses vs. monthly net income using 50/30/20 benchmarks.",
            action_items=action_items,
            metrics=metrics
        )
