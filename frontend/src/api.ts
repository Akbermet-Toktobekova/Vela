export type Profile = {
  id: string;
  name: string;
  currency: string;
  monthly_income: number;
  cash_balance: number;
  min_cash_buffer: number;
  income_day: number;
  priority: string;
  auto_save_pct: number;
  emergency_months: number;
  fixed_costs: {
    name: string;
    amount: number;
    due_day: number;
    category: string;
  }[];
  debts: {
    name: string;
    balance: number;
    annual_rate: string;
    min_payment: number;
  }[];
  savings: {
    name: string;
    balance: number;
    kind: string;
    target_amount?: number | null;
    target_date?: string | null;
  }[];
  goal: Record<string, unknown>;
  declined_transaction: boolean;
  created_at: string;
};
export type Rec = {
  id: string;
  status: string;
  chosen: {
    title: string;
    type: string;
    agent: string;
    params: { amount: number; schedule_day: number };
    facts: Record<string, number>;
  };
  reason_facts: Record<string, number>;
  explanation_text: string;
  alternative: string;
  alternative_reason: string;
  do_nothing: string;
  considered: { candidate: { title: string }; score: string }[];
};
export type Rule = {
  id: string;
  name: string;
  status: string;
  amount: number;
  account: string;
  trigger: { kind: string; value: string };
};
export type Lesson = {
  id: string;
  title: string;
  topic: string;
  body: string;
  question: string;
  options: string[];
  answered: boolean;
  correct: boolean;
  explanation: string;
};
export type Today = {
  profile: Profile;
  date: string;
  provider: string;
  goal_projection: {
    projected_date: string | null;
    target_date: string | null;
    on_schedule: boolean | null;
    account: string;
    months: number;
  };
  timeline_change: {
    before: { projected_date: string | null };
    after: { projected_date: string | null };
  } | null;
  overview: {
    safe_to_spend: number;
    buffer_after: number;
    reserved: number;
    days_to_income: number;
    emergency_saved: number;
    emergency_target: number;
    cushion_months: string;
  };
  recommendation: Rec | null;
  guard: { reason: string; until: string } | null;
  lesson: Lesson | null;
  rules: Rule[];
  history: {
    id: number;
    timestamp: string;
    type: string;
    payload: Record<string, unknown>;
  }[];
  analysis: {
    recurring: { merchant: string; amount: number; confirmed: boolean }[];
    categories: Record<string, number>;
  };
  disclaimer: string;
};
export async function api<T>(
  path: string,
  body?: unknown,
  method?: string,
): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    method: method || (body === undefined ? "GET" : "POST"),
    headers:
      body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(
      result.error?.message ||
        "This request could not be completed. Please try again.",
    );
  return result;
}
export function money(cents: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}
export function label(key: string) {
  return key.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
}
