# T24b parallel rework - independent review R1/R2

- Status: review pending independent acceptance; no done or CHECKPOINT-2 promotion.
- Executor: Codex GPT-6, 2026-10-29.
- Scope ownership: only chat.py, test_chat_tools.py and this report. Root orchestrator owns shared status files and explicit-file commit. No staging/commit performed.

## Changes

Extended the existing completed-financial-action gate to cover settled rent/bills/debt in active and passive forms. Added settlement verbs to clause-local negation handling, including the adverb just. Extended the investment asset vocabulary with singular/plural gilt. All previous output restrictions remain active; no changes to retry loop, production 20-second shared deadline, PII, quota accounting, cancellation or tools/numeric verification.

Three added integration methods cover seven unsafe variants on both initial/retry paths (14 subcases), eight educational/negated controls, and corrected retries for both independently reproduced claims. Unsafe responses never appear in returned local text; state remains identical, and rejected text is absent from retry contents/instructions.

## Changed files

- services/api/vela/chat.py
- services/api/tests/test_chat_tools.py
- docs/agents/reports/T24b-parallel-rework.md

ai.py did not require changes. Existing shared dirty files were preserved.

## Verification

Before implementation, the three new test methods: Ran 3 tests in 0.729s; FAILED (failures=16). Both audit claims reproduced as accepted gemini responses.

After implementation:

- PYTHONPATH=services/api python -m unittest services.api.tests.test_chat_tools.TestT24bIntegration -q: Ran 22 tests in 8.483s; OK, exit 0.
- PYTHONPATH=services/api python -m unittest services/api/tests/test_chat_tools.py -q: Ran 67 tests in 14.099s; OK, exit 0 (existing 64 retained, 3 added).
- python evals/run.py --offline --report .local/t24b-parallel-rework-evals.json: Summary: 60/60 PASS (Pass rate: 100.0%) in 1.663s, exit 0.
- python scripts/generate-contracts.py --check: Contract check passed, exit 0.
- git diff --check: exit 0 (line-ending warning in concurrently owned planning.py only).
- python scripts/check.py: Ran 242 tests in 76.597s; OK. Includes concurrent T72/T75 tests. Expected printed FAIL summaries come from negative eval-harness regression fixtures, not unittest failures.

## Deviations, risks and questions

Explicit delegation overrides routine executor shared-status/staging instructions: BACKLOG/HANDOFF and primary T24b.md not edited, shared dirty tree not staged or committed. Contract generation was check-only because schema is unchanged and generated files belong to concurrent T75 work. No new dependencies or mobile changes.

Lexical checks cover the supported ordinary-English findings and nearby forms; they are not a semantic proof for arbitrary paraphrases/languages. Offline60 covers deterministic fallback; mock integration tests cover model acceptance. All quota databases for this slice are temporary/synthetic. No demo.db access, API8000-8003/process management, live paid/cloud calls or deployment.

Next: independent new-context security review, then root explicit-scope commit/status update.
