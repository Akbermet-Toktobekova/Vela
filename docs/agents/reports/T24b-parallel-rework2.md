# T24b structural-output rework2 — 2026-10-29

- **Status:** review requested; not independent acceptance.
- **Executor:** delegated Codex `t72_executor`, completing interrupted prior executor work under root orchestration.
- **Input:** `T24b-independent-rework.md` findings R1/R2 and inherited dirty diff in `chat.py` / `test_chat_tools.py`.
- **Changed files:** those two scoped code/test files and this report. Root owns commits and canonical statuses.

## Changes

Preserved the interrupted executor's bounded `_unsafe_model_output` repair: normalize whitespace before splitting semantic clauses, so newline/tab formatting does not detach a completed-action verb from its financial object or negation. Retain restricted-asset context across sentence boundaries for explicit pronoun directives (`it/them/those/these`), without treating an unrelated groceries purchase as investment advice. Existing per-clause negation, disclaimer handling, numeric verification, shared deadline, retry count, quotas, PII and chat pipeline remain intact.

Preserved its integration regressions for newline settlement/payment claims, cross-sentence gilt/bond directives, reversed sentence order and mixed disclaimer directives. Each unsafe case is checked as the first and second model attempt, must fall back locally, and must preserve full State. Extended the inherited safe controls to run both as first answers and as retries after an invalid amount: multiline negation, educational descriptions, negative guidance, unrelated groceries and grounded cash must remain accepted with unchanged State. No additional production edit was needed after validating the inherited repair.

## Actual checks

- `$env:PYTHONPATH='services/api'; python -m unittest services/api/tests/test_chat_tools.py -q`: inherited-diff validation **69 tests in10.128s; OK**, exit0. After extending safe retry controls: **69 tests in11.968s; OK**, exit0. Captured final output `.local/t24b-rework2-focused.txt`.
- `python evals/run.py --offline --report .local/t24b-parallel-rework2-evals.json`: **60/60 PASS, 100.0%, 1.087s**, exit0. This was run after the production repair and before the test-only safe-control extension; production source unchanged afterward.
- `python scripts/generate-contracts.py --check`: **Contract check passed**, exit0.
- `git diff --check -- services/api/vela/chat.py services/api/tests/test_chat_tools.py`: exit0 before final report; final scope diff checked separately by executor.

## Limits and handoff

No full backend rerun here: root explicitly centralizes that gate after parallel edits stabilize. No live provider calls: mocked model integration and offline fallback evidence do not establish arbitrary-language semantic safety. No API shape change, new dependency, policy value, paid activation or deployment. No demo.db or API8000–8003 access/process management. No new red run is claimed: the independent input report contains the concrete failing integration reproductions, and this delegate inherited an already-partially-fixed dirty diff. Both findings are ready for independent Astra re-review; CHECKPOINT-2 and release status are not promoted by this execution report.
