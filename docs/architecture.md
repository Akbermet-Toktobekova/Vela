# Architecture

```mermaid
flowchart LR
 UI[React Today / Assistant / My Plan] --> API[FastAPI /api/v1]
 API --> S[Service unit of work]
 S --> DB[(SQLite snapshots + history)]
 S --> A[Analysis]
 S --> AG[Budget / Debt / Savings]
 A --> D[Pure domain and money maths]
 AG --> D
 AG --> C[Coordinator]
 C --> F[Affordability filters]
 F --> R[Rule scoring]
 F --> L[Optional LLM selection]
 L --> V[ID / tone / number validation]
 S --> E[Simulated rules engine]
 S --> G[Stress guard + daily limit]
 CSV[CSV / Synthetic / Replay sources] --> S
 S --> T[Read-only scenario tools]
 T --> D
 T --> X[Explanation + faithfulness fallback]
```

```mermaid
sequenceDiagram
 actor User
 participant UI
 participant Service
 participant SQLite
 participant Engine
 User->>UI: Accept or adjust
 UI->>Service: Decision + recommendation id
 Service->>SQLite: BEGIN IMMEDIATE
 Service->>Service: Check pending status, guard, amount, projection
 Service->>SQLite: Decision + approved simulated rule + history
 SQLite-->>UI: Committed result
 User->>UI: Replay a week
 UI->>Service: One chronological batch
 Service->>Engine: Match each new event and reserve obligations
 Engine-->>Service: Executed or skipped ledger result
 Service->>SQLite: Ledger, balances, batch plan change, guard
 Service->>Service: Supersede old pending action, enforce daily limit
 Service-->>UI: Updated overview and timeline
```

## Persistence model

`Record.key` names profile, transaction collection, current/archived recommendations, daily issuance marker, cooldown map, guard expiry, rules, ledger, lesson/progress, import summary, and synthetic clock. `HistoryEvent` has a monotonic primary key, UTC timestamp, event type, and immutable JSON payload. All service mutations occur in one serialized SQLite transaction; no history update endpoint exists.

## UI wireframe

Desktop: fixed left navigation; top demo/persona bar; two-column Today layout. Main column contains the primary cash figure and one recommendation. Side column contains safety-net progress and the daily lesson. My Plan contains editable profile/obligations, recurring confirmations, rules, and a filterable history. Assistant displays grounded facts and named tools below replies. Narrow viewports use a single column and bottom navigation. Modal dialogs trap keyboard focus and support Escape. Light/dark themes use teal, neutrals, and amber attention messages.
