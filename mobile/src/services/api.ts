import { ChatMessage, UserProfile, MicroLesson, ExpenseSummary, Transaction, TransactionSource } from "../types";

const API_BASE_URL = "http://127.0.0.1:8000";

const DEFAULT_PROFILE: UserProfile = {
  user_id: "user_default",
  monthly_income: 3500,
  currency: "EUR",
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

let localTransactions: Transaction[] = [
  {
    id: "tx_01",
    amount: 38.50,
    currency: "EUR",
    raw_merchant: "POS 0923 SPAR CORVIN BUDAPEST HU",
    clean_merchant: "SPAR",
    category: "Groceries",
    icon: "🛒",
    bucket: "needs",
    is_essential: true,
    source: "apple_pay",
    account_name: "Revolut Standard",
    timestamp: "Today, 14:23",
  },
  {
    id: "tx_02",
    amount: 4.80,
    currency: "EUR",
    raw_merchant: "STARBUCKS #1024 DEAK FERENC",
    clean_merchant: "Starbucks",
    category: "Coffee & Cafes",
    icon: "☕",
    bucket: "wants",
    is_essential: false,
    source: "nfc_tap",
    account_name: "OTP Master Card",
    timestamp: "Today, 11:15",
  },
  {
    id: "tx_03",
    amount: 14.99,
    currency: "EUR",
    raw_merchant: "NETFLIX.COM PAYMENT AMSTERDAM",
    clean_merchant: "Netflix",
    category: "Subscriptions",
    icon: "🎬",
    bucket: "wants",
    is_essential: false,
    source: "open_banking",
    account_name: "OTP Master Card",
    timestamp: "Yesterday, 09:00",
  },
  {
    id: "tx_04",
    amount: 9.50,
    currency: "EUR",
    raw_merchant: "BKK BUDAPEST MOBILJEGY",
    clean_merchant: "BKK Public Transit",
    category: "Transportation",
    icon: "🚇",
    bucket: "needs",
    is_essential: true,
    source: "google_wallet",
    account_name: "Wise Account",
    timestamp: "Yesterday, 18:40",
  },
  {
    id: "tx_05",
    amount: 54.20,
    currency: "EUR",
    raw_merchant: "ZARA FASHION VACI UTCA",
    clean_merchant: "Clothing & Apparel",
    category: "Shopping",
    icon: "👗",
    bucket: "wants",
    is_essential: false,
    source: "apple_pay",
    account_name: "Revolut Standard",
    timestamp: "2 days ago",
  },
  {
    id: "tx_06",
    amount: 62.00,
    currency: "EUR",
    raw_merchant: "LIDL HU BP 042 CORVIN",
    clean_merchant: "Lidl",
    category: "Groceries",
    icon: "🛒",
    bucket: "needs",
    is_essential: true,
    source: "nfc_tap",
    account_name: "OTP Master Card",
    timestamp: "3 days ago",
  },
];

export const api = {
  async getExpensesSummary(): Promise<ExpenseSummary> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/expenses/summary`);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Local fallback
    }

    const total_spent = localTransactions.reduce((acc, t) => acc + t.amount, 0);
    const needs_total = localTransactions.filter(t => t.bucket === "needs").reduce((acc, t) => acc + t.amount, 0);
    const wants_total = localTransactions.filter(t => t.bucket === "wants").reduce((acc, t) => acc + t.amount, 0);
    const savings_total = localTransactions.filter(t => t.bucket === "savings").reduce((acc, t) => acc + t.amount, 0);

    const catMap: Record<string, { amount: number; icon: string; bucket: any }> = {};
    localTransactions.forEach(t => {
      if (!catMap[t.category]) {
        catMap[t.category] = { amount: 0, icon: t.icon, bucket: t.bucket };
      }
      catMap[t.category].amount += t.amount;
    });

    const category_breakdown = Object.keys(catMap).map(cat => ({
      category: cat,
      amount: parseFloat(catMap[cat].amount.toFixed(2)),
      percentage: parseFloat(((catMap[cat].amount / total_spent) * 100).toFixed(1)),
      icon: catMap[cat].icon,
      bucket: catMap[cat].bucket,
    })).sort((a, b) => b.amount - a.amount);

    return {
      total_spent: parseFloat(total_spent.toFixed(2)),
      currency: "EUR",
      needs_total: parseFloat(needs_total.toFixed(2)),
      wants_total: parseFloat(wants_total.toFixed(2)),
      savings_total: parseFloat(savings_total.toFixed(2)),
      needs_percentage: parseFloat(((needs_total / total_spent) * 100).toFixed(1)),
      wants_percentage: parseFloat(((wants_total / total_spent) * 100).toFixed(1)),
      savings_percentage: parseFloat(((savings_total / total_spent) * 100).toFixed(1)),
      category_breakdown,
      recent_transactions: localTransactions,
    };
  },

  async simulateTapToPay(merchant: string, amount: number, source: TransactionSource = "nfc_tap"): Promise<Transaction> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/expenses/simulate?merchant=${encodeURIComponent(merchant)}&amount=${amount}&source=${source}`, {
        method: "POST",
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Local fallback
    }

    const isGroceries = merchant.toLowerCase().includes("spar") || merchant.toLowerCase().includes("lidl") || merchant.toLowerCase().includes("tesco");
    const isCoffee = merchant.toLowerCase().includes("coffee") || merchant.toLowerCase().includes("starbucks");
    const isFood = merchant.toLowerCase().includes("burger") || merchant.toLowerCase().includes("wolt") || merchant.toLowerCase().includes("food");
    
    const category = isGroceries ? "Groceries" : isCoffee ? "Coffee & Cafes" : isFood ? "Fast Food" : "General Spending";
    const icon = isGroceries ? "🛒" : isCoffee ? "☕" : isFood ? "🍔" : "💳";
    const bucket = isGroceries ? "needs" : "wants";

    const newTx: Transaction = {
      id: `tx_${Date.now()}`,
      amount,
      currency: "EUR",
      raw_merchant: merchant,
      clean_merchant: merchant,
      category,
      icon,
      bucket: bucket as any,
      is_essential: isGroceries,
      source,
      account_name: "Apple Pay / Revolut",
      timestamp: "Just now",
    };

    localTransactions = [newTx, ...localTransactions];
    return newTx;
  },

  async getProfile(): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/profile/user_default`);
      if (response.ok) return await response.json();
    } catch {}
    return DEFAULT_PROFILE;
  },

  async updateProfile(profile: UserProfile): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (response.ok) return await response.json();
    } catch {}
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
    } catch {}

    const q = message.toLowerCase();
    if (q.includes("debt") || q.includes("loan") || q.includes("credit card") || q.includes("pay off")) {
      return {
        content: "💳 **Debt Elimination Strategy (Avalanche Mode)**\n\nFocus extra cash on **Credit Card A (€2,400 @ 21.5% APR)** while paying minimums (€150) on Student Loans. This saves the maximum amount of accrued interest.",
        agent: "debt_optimizer",
        agentName: "Debt Optimizer",
        actionItems: [
          "Direct €200 extra per month to Credit Card A to finish in ~10 months.",
          "Keep student loan on standard autopay."
        ]
      };
    } else if (q.includes("budget") || q.includes("spend") || q.includes("income") || q.includes("groceries")) {
      return {
        content: "📊 **Budget Analysis (50/30/20 Benchmark)**\n\n• **Needs:** €1,830 (52.3%)\n• **Wants:** €430 (12.3%)\n• **Net Surplus:** €1,240 (35.4%)\n\n✅ You have a healthy monthly surplus. Allocate at least €600 to high-interest debt and €400 to savings.",
        agent: "budget_specialist",
        agentName: "Budget Specialist",
        actionItems: ["Review food delivery subscriptions", "Automate savings on the 1st of every month"]
      };
    } else if (q.includes("save") || q.includes("goal") || q.includes("japan") || q.includes("emergency")) {
      return {
        content: "🌱 **Savings & Goal Trajectory**\n\n• **Emergency Fund:** €2,800 / €6,000 (46.7%)\n• **Trip to Japan:** €950 / €3,000 (31.7%)\n\n💡 With your current €1,240 surplus, splitting €500/mo into HYSA will complete your Emergency Fund by December 2026!",
        agent: "savings_coach",
        agentName: "Savings Coach",
        actionItems: ["Automate €500 monthly deposit into HYSA", "Set travel milestone notification"]
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
    return {
      id: "lesson_1",
      title: "The 50/30/20 Rule: Building Your Blueprint",
      category: "Budgeting Basics",
      read_time_minutes: 2,
      content: "The 50/30/20 framework divides your after-tax income into three buckets:\n\n• 50% for Needs (rent, utilities, groceries)\n• 30% for Wants (dining out, hobbies, shopping)\n• 20% for Savings & Extra Debt Repayment",
      key_takeaway: "Prioritize your 50% Needs first, automate your 20% Savings on payday, and enjoy your 30% guilt-free.",
      quiz: {
        question: "If your net monthly income is €3,500, how much should be dedicated to Needs under 50/30/20?",
        options: [
          { id: "a", text: "€1,050", is_correct: false },
          { id: "b", text: "€1,750", is_correct: true },
          { id: "c", text: "€700", is_correct: false },
        ],
        explanation: "50% of €3,500 is €1,750 dedicated to essential expenses."
      }
    };
  }
};
