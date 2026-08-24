# Vela: CrewAI Multi-Agent System Design & Implementation Plan

**Project:** Vela — Intelligent Financial Advisor & Ingestion Engine  
**Framework:** CrewAI (Flows + Specialist Agents + Structured Pydantic Outputs)  
**Standard:** Built according to the official `crewaiinc/skills` methodology  

---

## 1. Multi-Agent Design Architecture

Following CrewAI best practices, we use **Specialist Agents** with dedicated roles, goals, backstories, and focused tools, orchestrated via a **Conversational Flow**.

```
                           [ Incoming User Chat / Transaction Ingestion ]
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  Vela Financial Flow  │
                                     │ (Routing & Lifecycle) │
                                     └───────────────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
       ┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
       │   Budget Specialist   │     │     Debt Optimizer    │     │     Savings Coach     │
       ├───────────────────────┤     ├───────────────────────┤     ├───────────────────────┤
       │ Role: Cash Flow Master│     │ Role: Liability Slayer│     │ Role: Wealth Builder  │
       │ Goal: Optimize 50/30/20│    │ Goal: Eliminate Debt  │     │ Goal: Milestone Reach │
       │ Tool: BudgetAnalyzer  │     │ Tool: AvalancheCalc   │     │ Tool: HYSAProjector   │
       └───────────────────────┘     └───────────────────────┘     └───────────────────────┘
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 ▼
                                     ┌───────────────────────┐
                                     │ Structured Response   │
                                     │ (Pydantic Output)     │
                                     └───────────────────────┘
```

---

## 2. Agent Specifications (`config/agents.yaml`)

### 2.1 Budget Specialist Agent
```yaml
budget_specialist:
  role: >
    Senior Cash Flow & Budgeting Strategist
  goal: >
    Analyze user income, recurring expenses, and live discretionary spending
    against the 50/30/20 benchmark to optimize monthly savings capacity.
  backstory: >
    You are a Certified Financial Planner (CFP) with 12 years of experience
    helping individuals achieve positive cash flow. You specialize in identifying
    hidden subscription leaks, categorizing point-of-sale transactions into
    Needs vs. Wants, and providing actionable, guilt-free spending limits.
  max_iter: 10
  allow_delegation: false
```

### 2.2 Debt Optimizer Agent
```yaml
debt_optimizer:
  role: >
    Quantitative Debt & Liability Elimination Specialist
  goal: >
    Formulate mathematically optimal debt payoff schedules (Debt Avalanche & Snowball)
    that minimize total compound interest paid across all active liabilities.
  backstory: >
    You are an expert credit analyst and consumer debt strategist. You evaluate
    credit cards, student loans, and mortgages by their APR, minimum commitments,
    and amortization curves to engineer the fastest possible path to debt freedom.
  max_iter: 10
  allow_delegation: false
```

### 2.3 Savings Coach Agent
```yaml
savings_coach:
  role: >
    Personal Wealth Accumulation & Liquidity Advisor
  goal: >
    Construct resilient emergency reserves (3-6 months HYSA) and project
    attainable timelines for medium and long-term milestone goals.
  backstory: >
    You are a behavioral finance and wealth building coach. You believe in
    automated "pay yourself first" systems, capital preservation, and harnessing
    compound yield while preventing emotional investing pitfalls.
  max_iter: 10
  allow_delegation: false
```

---

## 3. Tasks Specifications (`config/tasks.yaml`)

### 3.1 Task 1: Budget Analysis & Live Cash Burn Evaluation
```yaml
analyze_budget_task:
  description: >
    Analyze the user's monthly income ({monthly_income} {currency}), fixed essential expenses
    ({essential_expenses}), and discretionary spending ({discretionary_expenses}).
    Evaluate compliance with the 50/30/20 framework, identify potential spending leaks,
    and recommend concrete adjustments.
  expected_output: >
    A structured JSON response conforming to BudgetAnalysisOutput with exact ratios,
    surplus calculation, identified leaks, and 2-3 prioritized action steps.
  agent: budget_specialist
```

### 3.2 Task 2: Debt Elimination Strategy
```yaml
optimize_debt_task:
  description: >
    Review the user's active liabilities: {debts_list}. Calculate the total balance,
    aggregate monthly minimums, and rank each liability according to the Debt Avalanche
    (highest APR first) and Debt Snowball algorithms. Recommend the optimal extra monthly
    payment allocation.
  expected_output: >
    A structured JSON response conforming to DebtStrategyOutput with target priority debt,
    payoff timeline projections, and total interest saved.
  agent: debt_optimizer
```

### 3.3 Task 3: Savings Goal Trajectory & Liquidity Planning
```yaml
project_savings_task:
  description: >
    Evaluate the user's savings goals: {savings_goals} and available monthly cash flow ({monthly_surplus}).
    Calculate target completion dates, emergency fund adequacy (minimum 3 months of essential expenses),
    and recommend automated monthly contribution splits.
  expected_output: >
    A structured JSON response conforming to SavingsPlanOutput with completion percentages,
    milestone forecast dates, and emergency fund status.
  agent: savings_coach
```

---

## 4. Custom Tools for Agents (`tools/financial_tools.py`)

Using CrewAI's `@tool` decorator to equip agents with deterministic mathematical engines:

1. **`Budget503020CalculatorTool`:**
   - Computes exact Needs/Wants/Savings percentages.
   - Flags budget category anomalies (>55% Needs or >35% Wants).

2. **`DebtAvalancheCalculatorTool`:**
   - Amortization calculation engine.
   - Computes months-to-payoff and interest saved when adding \$X extra monthly payment.

3. **`HYSAGrowthProjectorTool`:**
   - Compound interest projection for High-Yield Savings Accounts (e.g. 4.5% APY).

---

## 5. Flow Orchestration (`flows/financial_flow.py`)

Using CrewAI **Flows** for state management and route execution:

```python
from crewai.flow.flow import Flow, start, listen, router
from pydantic import BaseModel
from typing import Optional, Dict, Any

class FinancialFlowState(BaseModel):
    user_id: str = "user_default"
    query: str = ""
    intent: str = "general"
    financial_data: Dict[str, Any] = {}
    analysis_result: Dict[str, Any] = {}

class VelaFinancialFlow(Flow[FinancialFlowState]):

    @start()
    def route_intent(self):
        """Classify user intent or trigger reason."""
        q = self.state.query.lower()
        if any(k in q for k in ["debt", "loan", "card", "pay off", "interest"]):
            return "DEBT"
        elif any(k in q for k in ["budget", "spend", "expenses", "groceries", "50/30/20"]):
            return "BUDGET"
        elif any(k in q for k in ["save", "savings", "goal", "emergency", "fund"]):
            return "SAVINGS"
        return "COORDINATOR"

    @listen("BUDGET")
    def run_budget_specialist(self):
        agent = get_budget_specialist_agent()
        result = agent.kickoff(
            messages=f"Analyze cash flow for: {self.state.financial_data}",
            response_format=BudgetAnalysisOutput
        )
        self.state.analysis_result = result.pydantic.model_dump()

    @listen("DEBT")
    def run_debt_optimizer(self):
        agent = get_debt_optimizer_agent()
        result = agent.kickoff(
            messages=f"Optimize debts for: {self.state.financial_data}",
            response_format=DebtStrategyOutput
        )
        self.state.analysis_result = result.pydantic.model_dump()

    @listen("SAVINGS")
    def run_savings_coach(self):
        agent = get_savings_coach_agent()
        result = agent.kickoff(
            messages=f"Project savings for: {self.state.financial_data}",
            response_format=SavingsPlanOutput
        )
        self.state.analysis_result = result.pydantic.model_dump()
```

---

## 6. Implementation Checklist & Deliverables

- [x] Install official `crewaiinc/skills` (`design-agent`, `design-task`, `getting-started`).
- [ ] Implement `backend/agents/crew_agents.py` with YAML configurations for Agent backstories and goals.
- [ ] Implement `backend/tools/financial_tools.py` with deterministic calculation engines.
- [ ] Implement `backend/flows/financial_flow.py` for stateful multi-agent execution.
- [ ] Connect the Flow to the Ingestion Webhook pipeline so incoming transactions automatically trigger CrewAI analysis.

---
*Created in alignment with the official CrewAI Agent & Task Design specifications.*
