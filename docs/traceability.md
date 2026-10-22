# Requirement traceability

Paths are relative to `src/finagent/` unless stated otherwise. Tests live in `tests/`.

| ID | Implementation | Verification / metric | Status or limit |
|---|---|---|---|
| FR1 | domain/models.py, service.py update_profile, API, ProfileForm | test_domain validators; API persistence and edits | Implemented; JSON snapshot persistence |
| FR2 | sources/personas.py, CLI, data/personas | seed byte identity, four golden selections | Implemented; 6 seeded months |
| FR3 | analysis/patterns.py, confirm | recurring precision/recall >=.9 fixture assertions, trend/projection tests | Monthly recurrence; variable-income prediction is simplified |
| FR4 | agents/specialists.py, domain/math.py | Hypothesis interest/buffer/reversibility; exact amortization fixtures | Implemented; monthly debt model |
| FR5 | agents/coordinator.py, config/coordinator.yaml | golden persona tests, deterministic ties, hard filters, numeric checks | Implemented; do-nothing is qualitative with current facts visible |
| FR6 | service.py decide, UI controls | API accept/adjust/decline, duplicate decision and cooldown tests | Amount/timing rechecked; adjusted figures recalculated |
| FR7 | rules/engine.py, service.py ingest/save_rule | branch/property tests, schedule and replay API regression | Simulated execution only |
| FR8 | persistence/store.py, history API/UI | API decision/rule/guard history assertions | No update-history API; explicit reset/delete clears history |
| FR9 | safety/checks.py, service.py guard/refresh | 60-phrase corpus, blackout/mid-batch/concurrent issuance tests | Implemented; lexical tone filter limitations documented |
| FR10 | frontend/src/main.tsx and styles.css | frontend component tests + production build | Browser visual/accessibility audit blocked by declined preview access |
| FR11 | assistant/chat.py, llm/client.py | fake tool selection, refusal, faithfulness fallback; opt-in live smoke | Bounded English scenarios and explicit recurring/income correction commands |
| FR12 | service.py recompute/ingest | one recompute per batch, supersession and daily-limit tests | Reassessment and before/after calendar goal-date projections in My Plan |
| FR13 | learning/lessons.py, data/lessons, API/UI | 20 bodies at 120–180 words, persona selection, no-repeat pool, progress idempotency | Priority plus debt, no-emergency, habit, and subscription triggers |
| FR14 | sources/csv_source.py, import API/UI | 3 formats including Hungarian, malformed rows, duplicate-file import | Synthetic fixtures verified; no real statement provided for demo |
| TR1 | agents/coordinator.py, llm/client.py | valid/invalid selection, provider error fallback | Both modes implemented; live provider not run |
| TR2 | evaluation.py, CLI, eval/results | 32 mode/scenario runs; agreement, safety, faithfulness, guard, determinism, latency | Fake-only report; no independent expert labels |
| TR3 | docs/ethics-notes.md | Technical controls and remaining gaps checklist | Complete artifact |
| TR4 | this file, architecture and ADRs | Source/test/metric links | Maintained for delivered prototype |

External/manual verification gates are listed in verification.md. No fake-provider or component-test result is represented as live-model or visual-browser evidence.
