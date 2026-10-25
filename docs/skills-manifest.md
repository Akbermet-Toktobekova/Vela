# Skills Manifest (`docs/skills-manifest.md`)

Updated: 2026-10-25  
Specification Reference: `FinAgent_Production_Development_Prompt.md` (§3)  

This document tracks all agent skills installed in `.agents/skills/`, their source, purpose, and installation status, as well as upstream skills recommended by the project specification that are currently uninstalled.

---

## 1. Installed Agent Skills (`.agents/skills/*`)

Total directories: **26**. All skills listed below are locally present in the repository.

| # | Directory / Name | Purpose | Location | Source / Upstream | Status |
|---|---|---|---|---|---|
| 1 | `cavecrew` | When to delegate to `cavecrew-investigator` (locate code), `cavecrew-builder` (1-2 file edit) or `cavecrew-reviewer` (diff review) instead of working inline or using `Explore`. Their output is compressed, so main context lasts longer. | `.agents/skills/cavecrew` | caveman (local upstream) | Active |
| 2 | `caveman` | Terse caveman voice: answer first, fluff gone, every technical fact kept. Use for /caveman, "caveman mode", "talk like caveman", "be brief", "less tokens". Stays on until "stop caveman" or "normal mode". | `.agents/skills/caveman` | caveman (local upstream) | Active |
| 3 | `caveman-commit` | Write a Conventional Commits message compressed to intent only. Use for "write a commit", "commit message", /commit or /caveman-commit. | `.agents/skills/caveman-commit` | caveman (local upstream) | Active |
| 4 | `caveman-compress` | Compress a memory file such as CLAUDE.md or a todo list into caveman format to save input tokens, keeping a readable backup. Sends the file's text to the configured model provider. Trigger: /caveman-compress. | `.agents/skills/caveman-compress` | caveman (local upstream) | Active |
| 5 | `caveman-discover` | Find and label every LLM workflow in the repository so Caveman Cloud groups spend by workflow instead of one bucket. Use for "discover workflows" or breaking LLM spend down by workflow. | `.agents/skills/caveman-discover` | caveman (local upstream) | Active |
| 6 | `caveman-evidence-review` | Read-only review of Caveman Cloud evidence: cost, Cave Score, workflows, traces, latency, errors, routing, savings. Use when asked what Caveman found or where LLM spend goes. | `.agents/skills/caveman-evidence-review` | caveman (local upstream) | Active |
| 7 | `caveman-explore` | Read-only repository explorer for cold-start orientation, broad cross-file localization, or when a direct search failed. Skip it when the exact file or symbol is already named. Returns path:line citations only; its reads stay out of main context. | `.agents/skills/caveman-explore` | caveman (local upstream) | Active |
| 8 | `caveman-help` | Quick-reference card for the three caveman skills and their commands. Trigger: /caveman-help or "caveman help". | `.agents/skills/caveman-help` | caveman (local upstream) | Active |
| 9 | `caveman-learn` | Act on a Caveman learn report - review the ranked token sinks, apply cost-lowering fixes with per-edit consent, and report what those fixes returned. Use when asked to lower an agent's token cost, what caveman has saved, to trim a heavy CLAUDE.md, or to offload re-pasted context into cavemem. | `.agents/skills/caveman-learn` | caveman (local upstream) | Active |
| 10 | `caveman-manage` | Inspect Caveman Cloud's experiment lifecycle and block unsafe execution. Use when asked to start, approve, cancel, promote or roll back a Caveman experiment. | `.agents/skills/caveman-manage` | caveman (local upstream) | Active |
| 11 | `caveman-optimize` | Turn a Caveman optimization observation into an operator-chosen candidate with a paired baseline evaluation. Use when asked to inspect or evaluate a Caveman optimization report. Needs explicit approval. | `.agents/skills/caveman-optimize` | caveman (local upstream) | Active |
| 12 | `caveman-review` | Compressed code review - one line per finding with location, problem and fix. Use for /caveman-review, "review this PR", or "review the diff". | `.agents/skills/caveman-review` | caveman (local upstream) | Active |
| 13 | `caveman-setup` | Wire a repository through the Caveman Cloud gateway so every LLM request is measured, with no behavior change. Use for "set up caveman" or adding LLM spend observability. | `.agents/skills/caveman-setup` | caveman (local upstream) | Active |
| 14 | `caveman-stats` | Show recorded output and cache-read token usage and mode attribution for the current Claude Code session, or locate the host's native usage report. Trigger: /caveman-stats. | `.agents/skills/caveman-stats` | caveman (local upstream) | Active |
| 15 | `generated` | Compiled skill distribution packs for multiple agent targets (aider, claude, codex, gemini, hermes, opencode). | `.agents/skills/generated` | caveman (local upstream / build output) | Active |
| 16 | `investigate-first` | Diagnose ambiguous failures before editing. Use for unknown causes, intermittent behavior, performance regressions, or investigations needing evidence-ranked hypotheses. | `.agents/skills/investigate-first` | native-core / specialized workflow skills (local) | Active |
| 17 | `lean-build` | Build feature work with high overbuilding risk. Use for new behavior, product slices, or integrations where repository reuse, strict scope, and an explicit stop condition matter. | `.agents/skills/lean-build` | native-core / specialized workflow skills (local) | Active |
| 18 | `megacave` | Caveman in Classical Chinese: 文言文 register, far fewer characters, technical terms verbatim. Invoke only with /megacave or /caveman wenyan. Stays on until "stop caveman" or "normal mode". | `.agents/skills/megacave` | caveman (local upstream) | Active |
| 19 | `migration` | Implement reversible compatibility-safe transitions. Use for schema, data, API, protocol, configuration, or dependency migrations requiring rollback and preservation proof. | `.agents/skills/migration` | native-core / specialized workflow skills (local) | Active |
| 20 | `native` | Core native system instructions and shared prompt budget definitions (`native-core.md`). | `.agents/skills/native` | caveman (local upstream / native pack) | Active |
| 21 | `safe-refactor` | Restructure code while preserving behavior. Use for extraction, consolidation, ownership moves, or cleanup where verification must bracket structural edits. | `.agents/skills/safe-refactor` | native-core / specialized workflow skills (local) | Active |
| 22 | `surgical-patch` | Fix bugs and small behavior changes at the narrowest responsible layer. Use when regression proof, preserved surrounding behavior, and task-relevant tests matter. | `.agents/skills/surgical-patch` | native-core / specialized workflow skills (local) | Active |
| 23 | `ultracave` | Caveman at maximum compression: fragments, one word when one word is enough, each fact once. Invoke only with /ultracave or /caveman ultra. Stays on until "stop caveman" or "normal mode". | `.agents/skills/ultracave` | caveman (local upstream) | Active |
| 24 | `vela-executor` | Execute exactly one Vela backlog task (T<NN>) as Gemini 4 Argon or Gemini Flash 3.8. Use when the user says "Выполни T<NN>" or asks to implement a backlog item. Covers scope control, verification, report writing and escalation. | `.agents/skills/vela-executor` | Vela project team protocol (local) | Active |
| 25 | `vela-orchestrator` | Orchestrate the Vela multi-model team (Claude Opus primary, Gemini 4 Argon fallback). Use when the user says "Проверь T<NN>", "Что дальше?", "Чекпоинт фазы <N>" or "Прими роль оркестратора". Covers review, accept/reject, next-task selection, phase checkpoints and role inheritance. | `.agents/skills/vela-orchestrator` | Vela project team protocol (local) | Active |
| 26 | `verify-and-stop` | Prove existing work meets acceptance conditions without expanding scope. Use for validation-only tasks, completion checks, focused gate runs, and last-mile proof. | `.agents/skills/verify-and-stop` | native-core / specialized workflow skills (local) | Active |

---

## 2. Recommended by Spec, Not Installed

The master specification (§3) identifies external upstream skills for specific domains. Per §3 rules (*"Prefer vendor-maintained sources; do not install arbitrary 'all skills' bundles. If a skill is unavailable, use the primary documentation, record the substitution, and continue where safe"*), none of these external packages are currently installed in the workspace.

| Ecosystem / Group | Skill Name(s) | Upstream Repository / Source | Purpose Defined in Spec (§3) | Current Status & Substitution |
|---|---|---|---|---|
| **Expo** | `expo-overview`, `expo-project-structure`, `expo-router` | `https://github.com/expo/skills` | Project setup and navigation | **Not Installed**. Direct Expo SDK 58 documentation and local configuration (`apps/mobile/src/app/`) used directly. |
| **Expo** | `expo-design-system`, `expo-native-ui`, `expo-data-fetching` | `https://github.com/expo/skills` | Stitch tokens, native screens, server-state behaviour | **Not Installed**. Direct implementation via React Native, `@tanstack/react-query`, and `apps/mobile/src/theme.ts`. |
| **Expo** | `expo-dev-client` | `https://github.com/expo/skills` | Native development builds | **Not Installed**. Not required for current Expo Go workflow; to be evaluated if custom native code is needed. |
| **Expo** | `expo-animation` | `https://github.com/expo/skills` | Gestures and purposeful motion, only when needed | **Not Installed**. Native animations kept minimal and purposeful per spec. |
| **Expo / EAS** | `eas-workflows`, `eas-app-stores`, `eas-update`, `expo-upgrade` | `https://github.com/expo/skills` | CI, builds, release/rollback preparation, deliberate upgrades | **Not Installed**. EAS configuration will be driven directly from `apps/mobile/eas.json` in Phase 4. |
| **Stitch** | `stitch::react-native` | `https://github.com/google-labs-code/stitch-skills` | Extract reusable visual patterns and adapt relevant elements into native components | **Not Installed**. Static assets and reference HTML/CSS in `ui_sample/` are used directly as local reference. |
| **Stitch** | `design-md` | `https://github.com/google-labs-code/stitch-skills` | Extract visual tokens and style direction; maintain `docs/design-system.md` | **Not Installed**. Visual tokens extracted directly from `ui_sample/warm_editorial_finance/DESIGN.md` into `apps/mobile/src/theme.ts`. |
| **Gemini** | `gemini-api-dev` | `https://github.com/google-gemini/gemini-skills` | Model API, structured output, tool calls, SDK compatibility | **Not Installed**. Direct Python SDK implementation (`google-genai`) in `services/api/vela/ai.py` with quota ledger. |
| **Supabase** | `supabase-postgres-best-practices` | `https://github.com/supabase/agent-skills` | Schema, SQL, migrations, permissions, concurrency | **Not Installed**. PostgreSQL and Alembic migrations will be implemented directly using standard Alembic/SQLAlchemy patterns. |
| **Supabase** | `supabase` | `https://github.com/supabase/agent-skills` | Auth/private storage configuration | **Not Installed**. Auth and storage evaluated in Phase 3 (T30 ADR). |
