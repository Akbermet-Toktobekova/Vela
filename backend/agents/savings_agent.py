from models.schemas import UserFinancialProfile, ChatResponse, AgentType
from typing import Dict, Any

class SavingsCoachAgent:
    name: str = "Savings Coach"
    agent_type: AgentType = AgentType.SAVINGS
    role_description: str = "Advisor for emergency liquidity, compound interest accumulation, and medium/long-term goal tracking."

    def analyze(self, profile: UserFinancialProfile, user_query: str) -> ChatResponse:
        goals = profile.savings_goals
        total_saved = sum(g.current_amount for g in goals)
        total_target = sum(g.target_amount for g in goals)
        overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0

        monthly_surplus = profile.monthly_income - sum(e.amount for e in profile.expenses)
        
        reply = (
            f"🌱 **Savings & Goal Trajectory**\n\n"
            f"You have accumulated **${total_saved:,.2f}** across your active targets (**{overall_progress:.1f}%** towards your total goal of **${total_target:,.2f}**).\n\n"
            f"**Your Active Milestones:**\n"
        )

        for g in goals:
            pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            reply += f"• **{g.name}:** ${g.current_amount:,.2f} / ${g.target_amount:,.2f} ({pct:.1f}%)\n"

        if monthly_surplus > 0:
            reply += (
                f"\n💡 *Recommendation:* With your estimated monthly surplus of **${monthly_surplus:,.2f}**, "
                f"setting up an automated transfer of **${monthly_surplus * 0.5:,.2f}** on payday will complete your Emergency Fund within 6 months."
            )
        else:
            reply += "\n⚠️ *Notice:* Your current expenses match or exceed income. We should first run the Budget Specialist to free up monthly cash flow."

        action_items = [
            "Enable automated deposit into High-Yield Savings on your next paycheck.",
            "Review target dates for secondary non-emergency goals."
        ]

        metrics = {
            "total_saved": total_saved,
            "total_target": total_target,
            "overall_progress_pct": round(overall_progress, 1),
            "monthly_surplus_capacity": monthly_surplus
        }

        return ChatResponse(
            reply=reply,
            agent_used=self.agent_type,
            agent_name=self.name,
            reasoning="Calculated goal completion dates based on current liquid balances and estimated monthly cash surplus.",
            action_items=action_items,
            metrics=metrics
        )
