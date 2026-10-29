# T32 backend — verified identity and owner isolation

- **Status:** review requested; backend part only, not T32 independent acceptance.
- **Executor:** delegated Codex `t72_executor`; root owns task records and commits.
- **Date:** 2026-10-29.
- **Dependencies:** root accepted T31d374a2c and T35b3b9e86; scoped T32 clarification/preflight read. Mobile adapter is separately delegated.

## Delivered and owned files

- `services/api/vela/auth.py`: explicit trusted Supabase asymmetric-JWT settings, bounded/cached/rotating JWKS lookup, signature/algorithm/issuer/audience/required claims/expiry/subject verification,401 invalid credentials versus sanitized503 unavailable verification. Token key URLs/embedded keys cannot establish trust.
- `services/api/vela/main.py`: APP_MODE local/demo/cloud selection before storage; explicit trusted configuration and database required in cloud; one verified owner dependency for all installed APIs. No cloud demo-token fallback. Existing logging middleware/correlation headers retained, health reports actual mode. No financial logic or API money shapes changed.
- `services/api/requirements.txt`: explicit `PyJWT[crypto]==2.15.1`.
- `services/api/tests/test_isolation.py`:12 generated-key/mocked-provider/temporary-DB tests.
- `docs/product/authentication.md`: backend section and limits; mobile executor may append its separate section. This execution report.

Store inspection and tests found existing owner predicates/composite keys sufficient; `store.py` and Alembic revisions were not changed. No new user/product table, driver, password system, cloud connection or schema entity.

## Actual verification

```text
> .venv/Scripts/python.exe -m pip install 'PyJWT[crypto]==2.15.1'
Successfully installed PyJWT-2.15.1
# Existing system PyJWT2.10.1 was explicitly not uninstalled outside the virtualenv.
# Existing cryptography47.0.0 reused; no global installation.

> $env:PYTHONPATH='services/api'
> .venv/Scripts/python.exe -m unittest services/api/tests/test_isolation.py -q
Ran 12 tests in 10.169s
OK

> .venv/Scripts/python.exe scripts/generate-contracts.py
Generated OpenAPI and TypeScript schemas.
> .venv/Scripts/python.exe scripts/generate-contracts.py --check
Contract check passed.
```

All exit0. First focused11-test run passed in10.919s; two transport-limit cases were then added within a new test and final12-test suite passed above. Ignored final focused log `.local/t32-backend-isolation.txt`. Generated contracts have no resulting diff because HTTP money/request response schemas remain unchanged. Scoped diffcheck exit0 (requirements LF/CRLF warning only). No preimplementation red run claimed; this is a new trusted-identity feature.

Generated ES256 and RS256 keys prove valid A/B subjects, exact trusted JWKS URL/caching, unknown-key cooldown and successful rotation/expiry refresh. Invalid signature, issuer/audience, unexpected HS/none algorithms, missing claims, expiry/iat/nbf/subject types and reserved local owner reject. Token jku/x5u/jwk/crit rejects before network transport; provider error/redirect/oversize/malformed/duplicate/unsupported JWKS never authorizes and returns sanitized503 as appropriate.

Real FastAPI TestClient route calls prove missing/malformed/local-cloud token401 across state/export/personal/planning/frontend/Assistant/observations/history/lessons. A/B can use identical command keys without sharing accounts or receipt effects; foreign account updates and body owner spoof reject without changing either export. A-only deletion leaves B export/receipts/previews/runs/publications intact. Store proofs exercise same object IDs across all five tables, owner-specific preview deletion, missing-owner lookups, current revision publication guard and one-time receipt replay. Actual multipart upload by A cannot be read/applied by B (404). Invalid cloud config/database absence/unknown mode fail before Store; explicit local/demo aliases preserve the existing local credential path.

## Boundaries and handoff

No live Supabase, email OTP delivery, real provider keys, cloud DB/PostgreSQL/RLS, deployment, paid activation, real data, demo.db or API8000–8003 access/process management. The only HTTP provider calls in tests use injected `httpx.MockTransport`. No mobile files touched; mobile executor received config/401/503 contract. No financial rules or automatic local-to-cloud ownership mapping.

Root explicitly centralizes the final backend suite after source stabilizes; executor ran focused isolation/contract checks only, not mobile/evals repeats. The verifier is bounded supported asymmetric-JWT identity, not instant global token revocation or completed T52/cross-device UX. T75 projection capabilities remain accurately local-only and no cloud-ready assertion follows. Provider key-cache/access-token lifetime semantics and actual T70 configuration/activation require later operational evidence. Independent security re-review is required before root accepts the combined T32 backend/mobile task.
