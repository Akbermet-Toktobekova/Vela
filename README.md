# FinAgent

A calm, proactive financial-assistant **BSc thesis prototype**. Code calculates; the assistant explains. One recommendation at a time, with a cash-buffer check, visible alternatives, user decisions, and simulated rules.

**No real bank connections, money movement, authentication, or investment advice.** The default is entirely offline. All four demo personas are synthetic.

## Quick start

Requirements: Python 3.12, Node 22.12+ (or a newer supported release), npm, and Make. Run commands from the repository root.

```sh
make setup
make seed
make run
```

Open **http://127.0.0.1:8000**. API documentation: **http://127.0.0.1:8000/docs**. Health: `/health`.

`make seed` generates deterministic persona CSV/YAML files and resets the local demo database to Alex (P2). It intentionally replaces the current demo profile and history. To load another persona, use the UI selector or:

```sh
.venv/bin/python -m finagent.cli seed --persona P1
```

The demo starts on **October 22, 2026**. “Replay a week” advances the synthetic clock. It does not use the machine date, silently progress while closed, or trigger real transactions. Restarting preserves your profile, decisions, rules, ledger, blackout, and clock.

## Try the main flow

1. Open Today; inspect the cash figure, recommendation facts, alternative, and do-nothing outcome.
2. Ask the Assistant “Why this?” or “What if I pay $50 more toward debt?” Scenarios do not modify your plan.
3. Accept or adjust the recommendation. This authorizes a **simulated rule**, not an immediate bank payment. Budget reviews are recorded as decisions without a transfer rule.
4. Open My Plan to edit your profile, confirm recurring assumptions, inspect rules, or pause them.
5. Replay a week to feed a chronological transaction batch. Rule attempts and plan changes appear in history.
6. Import a CSV from My Plan. Imported history does **not** change cash balances or execute rules; enter the statement's current cash balance explicitly in your profile.

Persona switching resets the single-user demo, including imported data. “Delete my data” clears local application records and cached explanations. Synthetic fixture files remain part of the source repository.

## Development and verification

```sh
make test       # backend coverage gate and frontend component tests
make lint       # ruff lint/format and strict mypy on the pure domain
make eval       # both coordinators, four personas, three perturbations each
make build     # production frontend build
```

For hot UI development, run the API separately and `cd frontend && npm run dev`. Vite proxies `/api` to port 8000. Production serves the built frontend directly from FastAPI.

- Backend: `src/finagent/`; framework-free calculations in `domain/`.
- Frontend: `frontend/src/`; React/TypeScript, light/dark responsive layout.
- Evaluation: [`eval/results/report.md`](eval/results/report.md).
- Coverage gate: combined coverage of `domain`, `agents`, `analysis`, and `rules` >=80%.
- The repository includes `.gitlab-ci.yml` with lint, typecheck, backend/frontend test, and build jobs. **No GitLab remote or runner was supplied, so a hosted green pipeline has not been verified.**
- Browser preview access was declined in this session. Production compilation and component/API tests passed; visual browser QA remains outstanding.

## Optional Anthropic provider

Copy `.env.example` to `.env`, set `LLM_PROVIDER=anthropic`, provide your own `ANTHROPIC_API_KEY`, and set a model available to your account. `COORDINATOR=llm` enables model-assisted selection; the default remains rule-based. `.env` and cache/database files are ignored by Git.

**Enabling Anthropic sends the assistant message and the relevant structured financial facts to Anthropic.** Keep the fake provider for offline demos and any imported data you do not intend to send. No live-provider call was made during the build. Model availability and live quality are not verified.

The provider uses temperature zero and a prompt/model/version-keyed cache. Cached calls support repeatable evaluation; temperature zero alone is not a determinism guarantee. Invalid ids, unsupported numbers, tone violations, and provider errors fall back to deterministic behavior.

```sh
FINAGENT_LIVE_SMOKE=1 .venv/bin/pytest tests/test_live_llm.py --no-cov
LLM_PROVIDER=anthropic make eval
```

## Interpretation limits

Cash projections reserve known fixed costs and debt minimums until the next income. They do not infer unknown future variable spending. Debt calculations use monthly interest with half-up cent rounding, no fees, and no additional borrowing. Goal timelines use fixed contributions. Recurring detection currently models monthly schedules. These assumptions are visible in [architecture decisions](docs/decisions/ADR-002-financial-model.md).

The Assistant supports bounded English requests, not unrestricted financial reasoning. Explicit corrections include “Confirm Spotify is a recurring cost” and “Set my monthly income to $5000”. What-if questions remain read-only. A numeric allow-list checks wording; it is not a semantic proof that a valid number was used in the right context. See [verification status](docs/verification.md) for acceptance gaps and external gates.

Only code pushed to the student's ELTE GitLab repository counts toward the stated grading requirement. This checkout has no configured remote and has not been pushed.
