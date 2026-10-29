# EUR/HUF display valuation — T67 service slice

The read-only `vela.fx` service accepts explicit `Amount(minor, currency)` records. EUR and HUF use two minor digits. It preserves each original record, returns Decimal intermediate output-minor values, and rounds the **summed** complete result once to integer output minor units. Owner decision relayed by orchestrator on2026-10-29: nearest with `ROUND_HALF_UP`; EUR1.005 becomes EUR1.01, negative ties away from zero. Neither converted values nor reference rates are inputs to affordability, reservations, account balances or payment execution.

`ECBRates` queries only Frankfurter's ECB provider-specific pair route. It parses the HTTP JSON number directly as Decimal. Quotes retain rate, provider/source, publication date and requested date. Historical queries accept a returned preceding publication date but reject later/future dates; latest queries preserve the actual publication date rather than pretending it is today. HTTP errors, malformed/wrong-pair/nonpositive/nonfinite quotes give missing rates. Missing rates and unknown balances preserve originals and make both total fields null, with `complete=false`; they are never zero or a misleading partial sum. Unsupported currencies and unsafe integer totals fail explicitly.

The public-quote cache is bounded and process-local (default256 entries); it contains no account/user data. Latest keys include the UTC/caller-clock day; historical keys include the requested date. Successes are reused; failures are not cached. A publication arriving later the same day can remain absent until process restart or the next daily key. No within-day freshness SLA or durable shared cache is claimed. A cached Friday quote on Sunday remains labelled Friday, without a guessed staleness threshold. The caller owns an explicitly injected httpx client lifecycle. The registered API default opens/closes a buffered client per cache miss while preserving the process quote cache; each network request has a5-second timeout and does not follow redirects. Only currency/date reach the provider.

Usage:

```python
with httpx.Client() as client:
    result = value_amounts([Amount(1000, 'EUR'), Amount(40000, 'HUF')], ECBRates(client))
    # result.total_minor: integer EUR cents, or None for incomplete conversion.
    # result.lines retain originals and dated rate evidence.
```

## Authenticated API wiring

After T32 source freeze, `fx_routes.py` was registered once in `main.py` (injectable `fx_rates` factory argument). Authenticated `GET /v2/valuations/accounts?on=YYYY-MM-DD` uses only `store.read(verified_owner).personal.accounts`; target remains EUR per approved pilot. No request-body owner or currency override and no state mutation. With no `on`, use latest publication; an explicit historical `on` must be labelled as historical reference valuation of the **current confirmed balances**, never a reconstruction of historical account balances.

Response: `revision`, `balance_basis:"current_confirmed_balances"`, `target_currency:"EUR"`, `requested_on`, `rate_mode:"latest"|"historical_reference"`, `complete`, `estimated`, `total_minor:int|null`, `lines:[{account_id,original:{amount_minor:int|null,currency},converted_minor_exact:string|null,unavailable:null|"unknown_amount"|"missing_rate",quote:{base,quote,rate:string,rate_date,requested_on,source}|null}]`. Decimal fields serialize as decimal strings. Do not expose unrounded Decimal as a binary float. A missing rate remains HTTP200/incomplete; invalid date or unsupported/unsafe calculation is a validation response. Do not include this estimate in planning available amounts. Empty accounts can return zero with an empty list and must be distinguished from unknown account balances.

Implemented additional scope: `fx_routes.py` including response models, `main.py` registration/injection only, and `tests/test_fx_routes.py`. Root owns generated contracts/types and integration-guide updates. Focused HTTP tests: two owners/foreign token, exact source/date/Decimal strings, unknown/no-rate outage, HALF_UP single-round total, historical label, no revision/receipt/balance mutation, invalid/future dates. Inject mocked rate transport; root controls final backend/contracts gate. Persistent shared cache can be a separate evidence-driven improvement, not an unclaimed property of this module.

## Verification and optional smoke

Offline: `$env:PYTHONPATH='services/api'; .venv/Scripts/python.exe -m unittest discover -s services/api/tests -p test_fx.py -v`.

Opt-in live provider smoke (not run for this task): `.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'services/api'); import httpx; from vela.fx import ECBRates; c=httpx.Client(); print(ECBRates(c).get('HUF','EUR')); c.close()"`. This queries a public quote only and does not launch or contact the Vela API. Network availability is separate from deterministic acceptance.

Provider contract checked2026-10-29 against [Frankfurter documentation](https://frankfurter.dev/) and [official v2 OpenAPI](https://api.frankfurter.dev/v2/openapi.json). The documentation specifies the ECB provider route and pair/date fields; this module never uses the default blended feed. No live rate or cloud API call was made during verification.
