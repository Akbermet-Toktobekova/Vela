export type AgentType = 
  | "coordinator"
  | "budget_specialist"
  | "debt_optimizer"
  | "savings_coach"
  | "financial_educator";

export type TransactionSource = "nfc_tap" | "apple_pay" | "google_wallet" | "open_banking" | "manual";
export type BudgetBucket = "needs" | "wants" | "savings" | "transfers";

export interface Transaction {
  id: string;
  amount: number;
  currency: string;
  raw_merchant: string;
  clean_merchant: string;
  category: string;
  icon: string;
  bucket: BudgetBucket;
  is_essential: boolean;
  source: TransactionSource;
  account_name: string;
  timestamp: string;
}

export interface CategorySpend {
  category: string;
  amount: number;
  percentage: number;
  icon: string;
  bucket: BudgetBucket;
}

export interface ExpenseSummary {
  total_spent: number;
  currency: string;
  needs_total: number;
  wants_total: number;
  savings_total: number;
  needs_percentage: number;
  wants_percentage: number;
  savings_percentage: number;
  category_breakdown: CategorySpend[];
  recent_transactions: Transaction[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: AgentType;
  agentName?: string;
  actionItems?: string[];
  metrics?: Record<string, any>;
  timestamp: string;
}

export interface ExpenseItem {
  category: string;
  amount: number;
  is_essential: boolean;
}

export interface DebtItem {
  name: string;
  balance: number;
  interest_rate: number;
  minimum_payment: number;
}

export interface SavingsGoal {
  name: string;
  target_amount: number;
  current_amount: number;
  target_date?: string;
}

export interface UserProfile {
  user_id: string;
  monthly_income: number;
  currency: string;
  expenses: ExpenseItem[];
  debts: DebtItem[];
  savings_goals: SavingsGoal[];
  risk_tolerance: string;
}

export interface MicroLesson {
  id: string;
  title: string;
  category: string;
  read_time_minutes: number;
  content: string;
  key_takeaway: string;
  quiz?: {
    question: string;
    options: { id: string; text: string; is_correct: boolean }[];
    explanation: string;
  };
}
