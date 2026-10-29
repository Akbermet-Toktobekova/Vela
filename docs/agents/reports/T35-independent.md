# T35 independent review — 2026-10-29

**Verdict: REWORK — one browser error-path gap.** Independent delegated reviewer: Codex GPT-6. Only this report authored; root owns statuses/commits.

## R1 — unexpected500 response bypasses CORS

`main.py` registers CORSMiddleware as user middleware, while `logging_setup.py` installs the generic Exception handler. Inspection of the installed Starlette `build_middleware_stack` and `ServerErrorMiddleware.__call__` confirms ServerErrorMiddleware wraps all user middleware and sends that handler's response directly through its own outer send. Consequently an unexpected500 has X-Correlation-ID but no Access-Control-Allow-Origin or Access-Control-Expose-Headers: the new JSONResponse sets only the correlation header. An allowed-origin browser cannot read that response/correlation ID, unlike handled errors and health responses.

The focused test checks CORS on preflight/health and500 parity without Origin, so it does not cover their intersection. Expected bounded fix: preserve the configured origin restrictions while making unexpected500 responses readable with the correlation header from allowed origins; add an Origin-bearing500 regression and disallowed-origin control. Do not solve by reflecting arbitrary origins or globally reconfiguring logs. This finding is source-confirmed, not claimed as an additional runtime probe.

## Verified evidence

Requested command: `$env:PYTHONPATH='services/api'; .venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_correlation.py -q`.

Actual result: **Ran5 tests in1.653s; OK; exit0**. Covers12 concurrent contexts/reset, generated/provided/invalid/duplicate IDs, handled401/422/409/404, generic500 response/log ID parity, template-only paths and payload/token/exception exclusion, root handler preservation, ordinary CORS preflight/exposure.

Source inspection confirms a private per-factory logger with propagation disabled, no root/uvicorn/global logger-registry mutation, six-field JSON allowlist, removal of arbitrary message/exception content, request-local ContextVar reset in nested finally, and no request-body logging. Existing external server logging is explicitly outside this sink's guarantee. No further material issue found within reviewed scope.

Reviewed logging_setup.py, main.py diff, test_correlation.py and T35.md. Attempted direct Starlette source-path reads found no files at the assumed virtualenv path; used `inspect.getsource` through the requested interpreter to read the actual installed middleware implementation instead. No extra test suite, backend/browser/eval run, product edit, database access, demo.db/ports8000–8003 interaction or live service call.

## Independent R1 re-review — 2026-10-29

**Final verdict: ACCEPT.** This supersedes the initial REWORK above; historical finding retained.

Inspected frozen unexpected500 fix in logging_setup.py and the focused regression, including main.py passing the same configured origins to installation. The handler uses an immutable exact allowlist, supplies ACAO and exposes X-Correlation-ID only for a matching origin, and sets Vary: Origin. No wildcard, suffix matching or arbitrary-origin reflection. Existing generic error body, response/log correlation identity, request isolation and private logger behaviour remain intact.

Independent requested rerun: `$env:PYTHONPATH='services/api'; .venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_correlation.py -q` — **Ran5 tests in1.839s; OK; exit0**. The500 test now uses an explicitly configured origin and checks ACAO/exposure/Vary/correlation. Untrusted origin, allowed-origin suffix attack, nonconfigured localhost and null receive no ACAO/exposure. Existing privacy/context/500 parity tests also pass.

No unresolved material T35 finding. No full suite repeated; root's centralized259-test integration result is separate evidence, not this reviewer's run. Only report updated; no source/status/commit/database/server changes or demo.db/ports8000–8003 access.
