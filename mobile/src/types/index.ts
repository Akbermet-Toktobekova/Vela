export type AgentType = 
  | "coordinator"
  | "budget_specialist"
  | "debt_optimizer"
  | "savings_coach"
  | "financial_educator";

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

export interface QuizOption {
  id: string;
  text: string;
  is_correct: boolean;
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
    options: QuizOption[];
    explanation: string;
  };
}
