# T75 — Independent review

- Date: 2026-10-29 (Europe/Budapest)
- Reviewer: Codex, independent new chat; vela-orchestrator workflow.
- Reviewed commit: `458ecac8e9a842af41eef8d7c8d5aecc0d8db968` — T75: prepare canonical frontend API and isolated integration kit.
- Verdict: **ACCEPT** for the bounded local frontend integration kit.
- No product changes. Shared statuses and commits remain root's responsibility as expressly delegated. T72/T24b/T73 are not accepted by this review.

## Evidence

Read task acceptance/scope, executor report, frontend guide, committed API/client/launcher/test changes and orchestrator skill. Bootstrap calls store.read exactly once; personal, plan, observations and lessons derive from that state. Both new reads require owner authentication. Existing planning command/store revision and fingerprint handling also protects resume. No new financial policy/dependencies or HTML integration were introduced.

Independently rerun commands and actual output:

```text
$env:PYTHONPATH='services/api'; python -m unittest discover -s services/api/tests -p test_frontend.py -v
Ran 7 tests in 6.358s
OK

node scripts/test-frontend-client.mjs
Frontend client: retry identity, immutable payload, paths, preview, auth, conflict and non-JSON error checks PASS.

python scripts/check.py
Ran 242 tests in 38.638s
OK
exit 0

python scripts/generate-contracts.py
Generated OpenAPI and TypeScript schemas.
python scripts/generate-contracts.py --check
Contract check passed.

npm run typecheck [apps/mobile]
tsc --noEmit
exit 0
```

Full suite runs against the shared checkout, which also had concurrent chat/security changes; its 242 tests are not attributed solely to T75. Harness tests deliberately print rejected samples; final unittest result above is OK.

Focused suite independently proves unknown versus zero, optional/no goal, single state read and matching nested revisions, canonical Assistant context, preview/export immutability, resume retry and changed/stale revision409, authenticated reads, exact CORS and invalid-origin rejection before database creation, erase and database reopen persistence.

Client tests exercise a lost response with mutated original form payload: retry retains serialized4000 and original key; a new action receives another key. Preview has no write key; path encoding,409 and non-JSON503 preserve useful failure handling.

## Independent real launcher + native ES-module HTTP

Created an owned child of `scripts/frontend-sandbox.py --origin http://localhost:5173` from an inline Python probe. Read only that child's newly created connection.json; invoked the actual `contracts/frontend-client.mjs` with Node native fetch, without mocks. No executor probe script was reused.

```text
Independent native ES-module HTTP PASS: reserve40 + income100 + complete40 => cash1100/saved40/available160; preview, retry, stale409, resume, CORS/auth.
Independent launcher PASS: port=55922; AI=false; unique directory=synthetic-k_cu91at
Stopped only owned launcher.
```

Independent fixed integer oracle: seeded cash100000/available10000; preview4000 leaves6000 and exact export unchanged; reserve4000 repeated through the same prepared command returns the same receipt; add income10000 and complete4000 produce cash110000, saved4000, available16000. Assistant endpoint equals bootstrap Assistant. Stale resume returns409; defer/resume and identical resume retry pass. Allowed-origin preflight200 with exact origin; lookalike origin400 without allow-origin; unauthenticated bootstrap401.

Launcher inspection confirms explicit synthetic database/local quota paths and generated token override inherited service settings; APP_MODE=local and ENABLE_GEMINI=false are forced before API import; no dotenv load. Socket stays held through uvicorn handoff, loopback only, excludes8000–8003. A unique directory is created per invocation. Child was terminated by its own process handle only. demo.db, APIs8000–8003, original HTML, paid AI and deployment were not accessed or changed.

## Acceptance limits

Guide maps actual supported account, income, planning, bill, import, evidence, lesson, export and erase controls; explicitly marks persistent chat, OTP/cloud isolation, transfers, server reminders, multiple goals and plan FX unavailable. Current account questions use deterministic current context rather than legacy chat. EUR40 is an explicit example amount, not the default policy. Preview is read-only; completion earmarks and does not transfer cash.

This acceptance covers the API/client/local integration kit, not a connected visual frontend, owner/native UX acceptance, browser file-save behavior, cloud account deletion, T24b/CHECKPOINT-2 or release readiness. Recorded-activity time window and local single-owner security limitations remain accurately disclosed. No blocking T75 findings.
