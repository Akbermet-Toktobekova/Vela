# Verification and phase status

This is a working local prototype, not a claim that every thesis acceptance gate has passed.

## Phase reports

| Phase | Delivered | Verification | Remaining gate |
|---|---|---|---|
| 0 Foundation | package layout, pinned dependencies, Makefile, CI, pre-commit, ADR | local installation/build/lint/typecheck | GitLab remote and hosted CI run unavailable |
| 1 Domain/data | validated records, exact rounded maths, 4 personas, adapters, recurring/trends/shortfalls | validator/property/fixture/seed identity tests; coverage gate | richer recurring intervals are not modeled |
| 2 Agents/coordinator | three specialists, deterministic scores, facts and alternative | golden actions for all personas; properties and fallback cases | independent policy validation not performed |
| 3 Decisions/safety | atomic decisions/rules/history, daily limit, cooldown, blackout | API acceptance flow; concurrency; schedule; guard tests | manual adversarial review beyond test corpus |
| 4 UI | Today, Assistant, My Plan, responsive themes, controls | TypeScript production build; React component tests | browser permission declined, so no visual or manual AA sign-off |
| 5 Import/replay | local CSV normalization, mapping, errors, batch replay | three synthetic formats and replay API tests | real-statement demo requires a supplied statement |
| 6 Assistant/LLM | bounded read-only scenarios, provider/cache, two coordinators | fake-provider tool/refusal/fallback tests | live smoke test opt-in; bounded English correction commands documented |
| 7 Learning/adaptive | 20 lessons, progression, recompute/supersession | lesson selection/nonrepeat and batch tests | manual review of contextual lesson copy |
| 8 Evaluation/docs | reproducible JSON, report, latency, diagrams, ethics, traceability | `make eval` reports zero unsafe choices; fake-mode guard/faithfulness/determinism pass | live/expert evaluation; hosted CI |

Run commands and demo steps are in README. `make test` prints the current exact test counts and coverage. `eval/results/results.json` excludes timing so repeated offline runs can be byte-identical; `latency.json` and its report table intentionally vary with runtime measurements.

## Completed follow-through

Explicit chat commands can confirm a recurring expense and update monthly income. What-if messages remain read-only. Lessons score relevant debt, absent-emergency-fund, weekend-habit, and subscription conditions within the chosen priority. Goal projections compute a calendar estimate, compare it with a supplied deadline, and persist before/after timeline changes for display in My Plan.

Current verified local results: **121 backend tests passed**, **1 opt-in live-provider test skipped**, **99.51%** coverage on required modules, **6 frontend tests passed**, strict domain typing and Ruff checks passed, and production frontend compilation passed. The live provider test is skipped by default and was not run.

Outstanding gates are external or manual: browser visual/accessibility review, ELTE GitLab pipeline run, live Anthropic evaluation, and a real-statement demo. No real statement was supplied or imported during the build.
