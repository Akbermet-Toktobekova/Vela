# T67 routes independent review — 2026-10-29

- Reviewer: Codex independent delegated context (not T67 implementation context).
- Verdict: **ACCEPT — bounded authenticated read-only API wiring**.
- Scope: `services/api/vela/fx_routes.py`, `services/api/tests/test_fx_routes.py`, three T67 registration deltas in main.py (import, injectable factory argument, one installer call). Existing FX service acceptance and T32 JWT implementation were context dependencies, not reopened or self-accepted here.

## Source review

`GET /v2/valuations/accounts` receives its owner solely through `Depends(owner)` and reads one owner-scoped State payload. It accepts only an optional reference date; request body/query owner strings cannot select another user's records. The exact factory owner dependency is passed to the installer, so the route shares T32 verification rather than defining another trust path. No mutation, receipt creation, revision increment, balance update, planning call or account data transfer occurs in this route.

Original amounts/currencies remain explicit. Conversion and rate Decimal values are serialized as strings, avoiding a binary-float JSON boundary. The total is an integer within the JS-safe range or null for incomplete data; unknown balances and rate outages are distinguished from an empty known list. Unsafe aggregation errors return422. Source/publication/request dates survive into quote evidence. Explicit historical dates are labelled `historical_reference` with `balance_basis=current_confirmed_balances`; neither code nor contract asserts historical balance reconstruction.

The default provider adapter opens a buffered httpx client within a context manager per cache miss; its response body is available after connection closure, and only the already-reviewed public quote cache survives. Currency/date are the only provider inputs. There is no account/owner/body/PII parameter sent to the provider. Client closure is directly asserted in the focused test. No new background task or long-lived client shutdown obligation was introduced.

## Actual independent evidence

```text
$env:PYTHONPATH='services/api'
.venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_fx_routes.py -q
Ran 7 tests in 1.606s
OK
exit0
```

Captured output: ignored `.local/t67-routes-independent.txt`. Tests use freshly created disposable synthetic SQLite files and injected public-rate transport. Independently executed controls cover two owner tokens and identical account IDs/query spoof, missing/foreign credentials401, one revision/read-only payload and receipt parity, original amounts/Decimal strings/dates/source, unknown/no-rate/empty states, labelled historical reference/future-invalid date, overflow422, closed default provider client, and real factory registration using its existing local owner dependency. The installer-level A/B seam is not claimed as independent JWT verification; T32 owns that evidence.

Reviewed source hashes (SHA256):

- fx_routes.py: `EE391523FF71AF7699266A1DF30567DA6EB15EE8C8109D3D78C4426CDB851949`
- test_fx_routes.py: `7D6335273D47E68B80AFB877C270D74BDA46D9E110383EB96A5BEAE50829EDA5`

No actionable route defect found in this bounded review. Root still owns full-backend/generated-contract drift integration and canonical T67 status. Live public-provider availability, browser/device rendering and cloud acceptance were not tested or inferred. No demo.db, ports8000–8003, live data, cloud request, paid service, source edit, shared status or commit occurred during review.

## Separate authorized documentation action

Before this review, parent explicitly authorized appending the mobile session section to `docs/product/authentication.md`. Existing backend text was preserved; added exports/configuration, native-versus-web credential boundaries,17 mock-test proof and T52 UI/cache limitations. Scoped diff check exit0. This documentation action does not change the independent T67 source review verdict.
