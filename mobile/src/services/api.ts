import { ChatMessage, UserProfile, MicroLesson } from "../types";

// Default localhost for backend
const API_BASE_URL = "http://127.0.0.1:8000";

const DEFAULT_PROFILE: UserProfile = {
  user_id: "user_default",
  monthly_income: 3500,
  currency: "USD",
  expenses: [
    { category: "Rent & Utilities", amount: 1200, is_essential: true },
    { category: "Groceries", amount: 450, is_essential: true },
    { category: "Dining & Entertainment", amount: 350, is_essential: false },
    { category: "Subscriptions & Gym", amount: 80, is_essential: false },
    { category: "Transport", amount: 180, is_essential: true },
  ],
  debts: [
    { name: "Credit Card A", balance: 2400, interest_rate: 21.5, minimum_payment: 80 },
    { name: "Student Loan", balance: 8500, interest_rate: 5.2, minimum_payment: 150 },
  ],
  savings_goals: [
    { name: "Emergency Fund (3 Months)", target_amount: 6000, current_amount: 2800, target_date: "2026-12-31" },
    { name: "Trip to Japan", target_amount: 3000, current_amount: 950, target_date: "2027-05-01" },
  ],
  risk_tolerance: "moderate",
};

const DEFAULT_LESSON: MicroLesson = {
  id: "lesson_1",
  title: "The 50/30/20 Rule: Building Your Blueprint",
  category: "Budgeting Basics",
  read_time_minutes: 2,
  content: "The 50/30/20 framework divides your after-tax income into three buckets:\n\n• 50% for Needs (rent, utilities, groceries)\n• 30% for Wants (dining out, hobbies, shopping)\n• 20% for Savings & Extra Debt Repayment\n\nThis simple benchmark protects you from lifestyle inflation while ensuring steady wealth accumulation without feeling deprived.",
  key_takeaway: "Prioritize your 50% Needs first, automate your 20% Savings on payday, and enjoy your 30% guilt-free.",
  quiz: {
    question: "If your net monthly income is $3,500, how much should be dedicated to Needs under the 50/30/20 rule?",
    options: [
      { id: "a", text: "$1,050", is_correct: false },
      { id: "b", text: "$1,750", is_correct: true },
      { id: "c", text: "$700", is_correct: false },
    ],
    explanation: "50% of $3,500 is $1,750 dedicated to essential expenses (rent, groceries, utilities)."
  }
};

export const api = {
  async getProfile(): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/profile/user_default`);
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Fallback
    }
    return DEFAULT_PROFILE;
  },

  async updateProfile(profile: UserProfile): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Fallback
    }
    return profile;
  },

  async sendChatMessage(message: string, history: ChatMessage[]): Promise<Partial<ChatMessage>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_history: history.map(h => ({
            role: h.role,
            content: h.content,
            agent: h.agent,
          })),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        return {
          content: data.reply,
          agent: data.agent_used,
          agentName: data.agent_name,
          actionItems: data.action_items,
          metrics: data.metrics,
        };
      }
    } catch {
      // Offline / Local Heuristic fallback
    }

    const q = message.toLowerCase();
    if (q.includes("debt") || q.includes("loan") || q.includes("credit card") || q.includes("pay off")) {
      return {
        content: "💳 **Debt Elimination Strategy (Avalanche Mode)**\n\nFocus extra cash on **Credit Card A ($2,400 @ 21.5% APR)** while paying minimums ($150) on Student Loans. This saves the maximum amount of accrued interest.",
        agent: "debt_optimizer",
        agentName: "Debt Optimizer",
        actionItems: [
          "Direct $200 extra per month to Credit Card A to finish in ~10 months.",
          "Keep student loan on standard autopay."
        ]
      };
    } else if (q.includes("budget") || q.includes("spend") || q.includes("income") || q.includes("groceries")) {
      return {
        content: "📊 **Budget Analysis (50/30/20 Benchmark)**\n\n• **Needs:** $1,830 (52.3%)\n• **Wants:** $430 (12.3%)\n• **Net Surplus:** $1,240 (35.4%)\n\n✅ You have a healthy monthly surplus. Allocate at least $600 to high-interest debt and $400 to savings.",
        agent: "budget_specialist",
        agentName: "Budget Specialist",
        actionItems: ["Review food delivery subscriptions", "Automate savings on the 1st of every month"]
      };
    } else if (q.includes("save") || q.includes("goal") || q.includes("japan") || q.includes("emergency")) {
      return {
        content: "🌱 **Savings & Goal Trajectory**\n\n• **Emergency Fund:** $2,800 / $6,000 (46.7%)\n• **Trip to Japan:** $950 / $3,000 (31.7%)\n\n💡 With your current $1,240 surplus, splitting $500/mo into HYSA will complete your Emergency Fund by December 2026!",
        agent: "savings_coach",
        agentName: "Savings Coach",
        actionItems: ["Automate $500 monthly deposit into HYSA", "Set travel milestone notification"]
      };
    }

    return {
      content: "👋 Hello! I am **Vela**, coordinating your multi-agent financial advisors.\n\nI can analyze your **budget**, optimize your **debts**, or project your **savings goals**.",
      agent: "coordinator",
      agentName: "Vela Coordinator",
      actionItems: ["Ask: 'How should I optimize my budget?'", "Ask: 'What is my debt payoff plan?'"]
    };
  },

  async getDailyLesson(): Promise<MicroLesson> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/learning/today`);
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Fallback
    }
    return DEFAULT_LESSON;
  }
};
