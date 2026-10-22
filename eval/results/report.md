# FinAgent evaluation

Provider: `fake`. Seed: 42. Financial date: 2026-10-22.

| Mode | Top-1 | Top-3 | Unsafe | Faithful | Guard | Deterministic |
|---|---:|---:|---:|---:|---:|---|
| rule | 100% | 100% | 0 | 100% | 100% | True |
| llm_assisted | 100% | 100% | 0 | 100% | 100% | True |

## Method and limits

Each coordinator runs on four personas and three perturbations per persona. Expected action labels remain unchanged for income/debt perturbations; balance shocks expect suppression. This tests policy stability, not independent expert optimality. Top-3 for the LLM uses the shared rule ranking, because the model returns one id only.

Guard compliance here measures the guard-before-selection wrapper. API integration tests separately exercise persistent 48-hour blackouts and daily frequency. Numeric faithfulness is an allow-list check, not semantic proof.

Fake-provider agreement is a wiring test and is **not evidence of live LLM quality**. Select `LLM_PROVIDER=anthropic` with your own credential for cached provider evaluation. Cold/cache-hit latency differs. Stable results exclude measured timing; latency observations are in `latency.json`.

| Mode | Median observed latency (ms) |
|---|---:|
| rule | 0.046 |
| llm_assisted | 0.123 |
