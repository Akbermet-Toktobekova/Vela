# Frontend integration — local development contract

2026-10-29 · T75 · Local synthetic development, pending independent review.

The design prompt can be implemented in Stitch/v0/Lovable or any frontend stack. Export its code and run it locally; keep the API connection in a separate adapter. The existing standalone HTML remains disconnected. This kit does not add Supabase/OTP, multiple users, cloud deployment, persistent conversations or actual transfers.

## Start the isolated API

From the repository root:

```powershell
python scripts/frontend-sandbox.py --origin http://localhost:5173
```

Use the actual browser origin (scheme, host, port), without a path or trailing slash. Repeat `--origin` for additional exact origins. Defaults when omitted: localhost:5173, 127.0.0.1:5173 and localhost:3000 over HTTP. Ports 8000–8003 are never selected. This process binds only loopback and is not a remotely hosted API for an online design builder. An HTTPS-hosted preview may block local HTTP; export and run the frontend locally instead of disabling browser protections.

Each launch creates a new `.local/frontend-sandboxes/synthetic-*` folder with its own synthetic.db, quota.db and private connection.json. No `.env` is read, no existing database is loaded, and AI is forcibly disabled. The port is allocated and held by the OS until the server takes over. Connection details stay in the ignored folder; do not paste the token into a public builder prompt, screenshot, source bundle or URL. Ctrl+C stops this server only. The synthetic folder is retained for inspection; launching again creates a separate one. Use `--empty` to test onboarding instead of preloaded example finances.

The preloaded account is EUR1000, protected EUR100, confirmed bills EUR800, available EUR100, optional example goal. Dates are relative to the launch date. The suggestion policy is the existing provisional policy: it may suggest EUR20 initially. EUR40 in the design prompt is an explicitly chosen example amount, not a newly approved financial rule. Preview and reserve EUR40 to reproduce the prompt sequence.

## Load and connect

The authenticated `GET /v2/frontend` response is the bootstrap contract (`contract_version: local-frontend-v1`). It contains a single revision, server date, capabilities, personal data and Assistant context. Today and My Plan use `assistant.plan`; Assistant uses that same plan plus recorded activity, evidence observations and lessons. All sections come from one state read; never combine sections of different responses as if they were one snapshot.

`GET /v2/assistant/context` refreshes just that structured context. It is deterministic read-only data, not a natural-language chat service. Use fixed prompts such as “Explain my next step” to present the plan's server message and relevant facts. Use `/v2/planning/preview` for supported savings-amount what-if. Do not send current-account questions to legacy `/v1/chat`, which intentionally rejects them after shared-plan activation.

Framework-independent ES module: `contracts/frontend-client.mjs`. OpenAPI: `contracts/openapi.json`. Generated response and command types: `apps/mobile/src/lib/generated.ts`. The module uses native fetch/crypto and no package dependency. Keep the token in memory and ask for the local connection details in a development-only connection form.

```javascript
import { createVelaClient } from './frontend-client.mjs';
const api = createVelaClient({ baseUrl: enteredApiUrl, token: enteredToken });
let screen = await api.bootstrap();

// Preview only; it never reserves money.
const preview = await api.preview({ amount: 4000 });
// After an explicit confirmation, prepare this command ONCE.
const reserve = api.reserve({ revision: preview.revision, id: crypto.randomUUID(), amount: 4000 });
await reserve.send();
screen = await api.bootstrap();
// After an uncertain network outcome, retry reserve.send() with the SAME object.
// After a 409, refresh and review; prepare a NEW command only after user confirmation.
```

The module can be copied together with the generated types for a separate frontend. Its JSDoc bootstrap type import points to this repository's generated types; adjust that type-only path in the exported project. Do not modify generated response schemas manually.

## Screen and control contract

All amounts are integer minor units with the contract's currency; EUR40 is 4000. Null balance/available is unknown, not zero. Account currency is EUR or HUF, but the current shared plan and imports are EUR only. Do not sum currencies or convert HUF into spending capacity. All financial writes below require `revision` and an `Idempotency-Key` of 8–100 characters. `command.send()` supplies its captured key. Path IDs must be encoded; the client does that.

- **Tabs / refresh / reconnect:** `bootstrap()`; navigation itself does not write. Return from dialogs without Save closes them and makes no request. Read-only receipts can be older snapshots; refresh bootstrap after every acknowledged write or uncertain outcome before rendering current totals.
- **Onboarding focus/income type:** `profile({revision, focus, income_type})`, `PUT /v2/profile`. Allowed values come from generated types. Current local profile stores only these choices and onboarded marker; the full resumable cloud onboarding is not implemented. No mandatory goal or upload.
- **Add account:** `addAccount({revision,name,currency,balance,confirmed_on})`, `POST /v2/accounts`. Unknown balance is null; it never becomes zero. `confirmed_on` is a local ISO date, not a future date.
- **Update balance:** `replaceBalance(accountId,{revision,balance,confirmed_on})`, `PUT /v2/accounts/{id}/balance`. Replaces confirmed cash; its difference is not income. Show the consequence before sending.
- **Add income:** `addIncome({revision,account_id,amount,received_on,effect,current_balance?})`, `POST /v2/income`. `effect: add` adds to known cash; `included` records only; `replace` requires the reviewed current_balance and replaces cash. Do not infer an amount/date or retry with a new command identity after lost acknowledgement.
- **Configure plan / optional goal / protected money:** `configurePlan(...)`, `PUT /v2/planning`. Supply chosen EUR account, horizon, protected (nullable when unknown), bills_confirmed/debts_confirmed, and optional `{name,target}` goal. Read exact restrictions from generated ConfigurePlan. The UI must obtain explicit confirmations; no hidden completeness defaults. Existing saved allocations/active steps prevent unsafe goal removal. Account reassignment and multi-goal reconciliation are unsupported.
- **Existing legacy plan:** review `assistant.plan.legacy`; `adoptLegacy({revision,account_id,confirm_finances:true})` only after explicit reconciliation. This is never an automatic onboarding action. Original data stays exportable.
- **Adjust / what-if:** `preview({amount})`, `POST /v2/planning/preview`. Use `eligible`, `remaining`, `goal_after`, `revision`, `message`. Only a later confirmed reserve writes. A changed revision can invalidate an earlier preview.
- **Reserve:** `reserve({revision,id,amount})`, `POST /v2/planning/steps`. Creates an allocation, does not subtract cash. Needs a confirmed safe EUR plan and goal.
- **Complete earmarking:** `complete(stepId,{revision})`, `POST /v2/planning/steps/{id}/complete`. Moves reserved allocation into goal saved, keeps account cash unchanged. Confirm that the person earmarked it themselves. This is not a bank transfer or bill/debt payment.
- **Cancel:** `cancel(stepId,{revision})`, `POST /v2/planning/steps/{id}/cancel`; releases a reservation without increasing cash. Show confirmation first.
- **Not now / resume:** `defer({revision})` and `resume({revision})`, POST `/v2/planning/defer` or `/resume`. Changes the suggestion preference only; no money movement. Render the returned plan and refresh.
- **Add confirmed bill:** `addBill({revision,id,label,amount,currency:'EUR',due})`, `POST /v2/planning/bills`. This is a separate confirmation, never an import side effect. `cancelBill(id,{revision})` cancels an unpaid bill.
- **Record bill paid:** `payBill(id,{revision,effect})`, POST `/v2/planning/bills/{id}/pay`. Explicitly choose `subtract` or `already_in_balance`; show updated cash before confirming. No real payment is sent.
- **Review spending / recurring payments / evidence:** `assistant()` or `observations()` plus `transactions({offset,limit})`. Display recorded periods, suggested status, calculation version and evidence IDs. Current recorded_activity totals cover 30 days through the latest recorded row, not necessarily today; transaction_count counts all stored rows. Empty data does not establish zero spending. Observation evidence may span more months. The history response exposes total; page until covered.
- **Import:** `previewImport({filename,content_type,data_base64})`, POST `/v1/imports/base64`, then optional `importPreview(id)`. Review all preview transactions/warnings. Explicit confirmation calls `applyImport(id,{revision})`, POST `/v2/imports/{id}/apply`. Discarding the review does not apply it. Only analytics is merged. Never call the legacy `/v1/imports/{id}/apply` from the new frontend. Offline CSV/XLSX/text-PDF support follows installed parsers; scanned images/external AI processing are unavailable in this AI-disabled sandbox and must show an honest error. Durable upload jobs and row corrections remain future slices.
- **Learn:** `lessons()` / `lesson(id)`, optional `lessonProgress(id,{revision,selected_index,completed})`. Contextual content uses the current shared plan; saving quiz progress is distinct from finance writes.
- **Export:** `exportData()` returns the complete owner JSON. Prepare a local download only after response success; revoke Blob URL after use. Do not claim the OS saved it merely because data was prepared.
- **Delete data:** after explicit destructive confirmation, `eraseData()`, DELETE `/v1/data`. Clear in-memory UI data/commands, reload bootstrap and disconnect. This local API clears data but does not revoke the development token or implement cloud account deletion.
- **Sign out:** drop the in-memory client/token, data and pending commands. No local API logout/OTP route exists.
- **Reminders / cloud OTP / persistent conversation / multiple goals:** check capabilities and show unavailable or omit the write control. Never render a successful Save for a nonexistent backend operation. Local OS reminder scheduling is a separate existing mobile module, not a server endpoint in this kit.

## UI states and verification

T32 adds a separate tested Supabase session adapter; see [authentication](authentication.md). This local kit does not implement its login screens. T67 adds authenticated `GET /v2/valuations/accounts` with optional `on=YYYY-MM-DD`: [FX contract](fx.md). Use returned exact decimal strings, actual rate dates, `complete` and nullable `total_minor`; historical reference values still use current confirmed balances. This display estimate never funds a plan or changes balances. Preserve original currencies/unknown amounts and label incomplete totals.

Disable duplicate submission while a command is pending; preserve edited fields on failure. For a lost response offer retry using the same prepared object. A 409 requires refreshing facts and reviewing consequences, not silently changing revision. A 401 requires reconnecting; 422 shows a safe field/domain message; network/503/non-JSON failures keep the form and show retry. Never log tokens or raw uploaded statements. Client controls are conveniences; server authentication/revision/idempotency remain authoritative. Two browser tabs must handle conflict explicitly.

Never mark an API write successful before acknowledgement. Loading, empty, unknown, stale, ineligible, error and confirmation states belong to the frontend. Native notification permission and financial-content acceptance are not established by these API tests. No production readiness or cloud isolation claim follows from this kit.

Run from repository root: `python scripts/check.py`; `python scripts/generate-contracts.py --check`; `node scripts/test-frontend-client.mjs`. Run `npm run typecheck` in apps/mobile. Focused API suite: set PYTHONPATH to services/api, then `python -m unittest discover -s services/api/tests -p test_frontend.py -v`. T75 report records the real launcher/HTTP sequence and results.
