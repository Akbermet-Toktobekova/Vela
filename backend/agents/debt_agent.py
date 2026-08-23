from models.schemas import UserFinancialProfile, ChatResponse, AgentType
from typing import Dict, Any

class DebtOptimizerAgent:
    name: str = "Debt Optimizer"
    agent_type: AgentType = AgentType.DEBT
    role_description: str = "Strategist for rapid liability elimination, comparing Avalanche vs. Snowball payoff methods."

    def analyze(self, profile: UserFinancialProfile, user_query: str) -> ChatResponse:
        debts = profile.debts
        if not debts:
            return ChatResponse(
                reply="🎉 **Congratulations!** You currently have zero recorded outstanding debts. You are in a prime position to build aggressive wealth through savings and index funds.",
                agent_used=self.agent_type,
                agent_name=self.name,
                action_items=["Maintain full payoff of all credit card statements monthly to avoid interest."]
            )

        total_debt = sum(d.balance for d in debts)
        total_minimums = sum(d.minimum_payment for d in debts)
        sorted_by_rate = sorted(debts, key=lambda d: d.interest_rate, reverse=True)
        highest_rate_debt = sorted_by_rate[0]

        reply = (
            f"💳 **Debt Elimination Strategy**\n\n"
            f"You currently have **${total_debt:,.2f}** in outstanding liabilities with minimum monthly commitments of **${total_minimums:,.2f}**.\n\n"
            f"🎯 **Recommended Action (Debt Avalanche):**\n"
            f"Focus all surplus repayment capacity on **{highest_rate_debt.name}** because it carries the highest interest rate (**{highest_rate_debt.interest_rate}% APR**).\n\n"
            f"• **Target Priority 1:** {highest_rate_debt.name} (Balance: ${highest_rate_debt.balance:,.2f} @ {highest_rate_debt.interest_rate}%)\n"
        )

        for d in sorted_by_rate[1:]:
            reply += f"• **Maintenance:** {d.name} (Balance: ${d.balance:,.2f} @ {d.interest_rate}%) — Pay minimum (${d.minimum_payment:,.2f})\n"

        reply += (
            f"\n⚡ *Impact:* Directing an extra **$200/month** towards {highest_rate_debt.name} will eliminate it in approximately "
            f"{max(1, int(highest_rate_debt.balance / 280))} months, saving hundreds in accrued compound interest!"
        )

        action_items = [
            f"Set up auto-pay minimums on all accounts to protect your credit score.",
            f"Send all discretionary bonuses directly to {highest_rate_debt.name}."
        ]

        metrics = {
            "total_debt_balance": total_debt,
            "monthly_minimum_payments": total_minimums,
            "highest_apr": highest_rate_debt.interest_rate,
            "target_debt": highest_rate_debt.name
        }

        return ChatResponse(
            reply=reply,
            agent_used=self.agent_type,
            agent_name=self.name,
            reasoning="Ranked active debts by APR to optimize for lowest total interest expense (Avalanche Algorithm).",
            action_items=action_items,
            metrics=metrics
        )
