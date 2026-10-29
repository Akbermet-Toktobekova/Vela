# UI-TEST-05 — Full workflow attempt and coverage inventory

Date: 2026-10-29. Model: GPT-6.1 Sol. Status: verification report / review; integrated end-to-end acceptance BLOCKED.
Starting revision: dc61cd3. Skills: uxpeak, verify-and-stop. Product code unchanged. No task promoted to done.

## Environment and isolation

Windows, real Chrome extension browser, Expo SDK58 development web at localhost:8081. Dedicated API127.0.0.1:8001, ENABLE_GEMINI=false, newly created .local/ui-test-05.db and a separate random local token. Existing API8000 and its data were not stopped/modified. Only synthetic UI5 accounts were created. No paid calls, real documents, deployments or dependencies.

Purpose: follow the complete approved pilot journey, not just the T71 income form. Sources: PILOT_SPEC, PRODUCT_PLAN J01-J12, USER_MANUAL U01-U22, TEST_RUNBOOK. Distinguish persistent /personal, isolated /pilot prototype and legacy /v1; they are not one accepted workflow.

## Blocking finding — saved data cannot reach the rest of the workflow

Reproduction: Connect -> Open Vela -> /personal. Available actions: account/income/balance, Edit profile, Refresh. No My Plan/Assistant/settings/import/learn navigation. Directly opening / resets the in-memory web connection and redirects to Connect. Successful Connect always replaces route with /personal again. Browser Back did not restore a connected legacy workflow. The development /_sitemap exposes old screens, but its links replace the route; using it did not provide an authenticated ordinary-user path.

Expected: saved accounts lead onward to obligations/goals, one persisted recommendation, action lifecycle, contextual explanation, documents and data management.
Observed: /personal explicitly says planning is not connected. Authenticated read-only /v1/state after the run still has snapshot=null, actions=[], transactions=0; v2 has two accounts and four income records. This is a product integration/navigation blocker, not a failed calculator. Do not mark old-module or prototype results as proof of J03-J12 with personal data.

## Persistent UI exercises actually run

- P01 PASS: short token keeps Open Vela disabled; long invalid token rejected on Connect with local-token guidance. Correct token opens empty /personal.
- P02 PASS: optional profile Not sure yet / Not sure yet saves without goal or statement; onboarding prompt disappears and stays absent after reload/reconnect.
- P03 PASS: UI5 EUR account1000; UI5 HUF unknown with blank balance -> Not provided / Balance not confirmed. No synthetic zero or cross-currency total.
- P04 PASS: HUF income100 / No-add rejected because balance unknown; draft retained. Switching to record-only saves income while balance remains unknown.
- P05 PASS: EUR income10 / No-add / rapid double-click Save -> EUR1010 and income count2 (one HUF record plus one EUR record). One observed effect; not proof of response-lost-after-commit retry.
- P06 PASS: draft EUR5 / No-add, stop only owned API8001, Save -> Failed to fetch, draft5 retained, no success transition. Restart same API/database, Save -> EUR1015, count3. Server restart preserved EUR1010/unknown-HUF and earlier records.
- P07 PASS: first tab draftEUR7 at balance1015. Second tab replaces balance1200. First tab Save -> Your information changed. Refresh and try again, draft7 preserved. Refresh after a conflict shows1200; resubmit -> EUR1207, count4. No lost update or silent overwrite observed.
- P08 PARTIAL: actual360x800 browser viewport, document width360 with no horizontal overflow. Income form labels and Save fit; all five measured buttons48px high. Native keyboard, scaling, contrast and screen-reader operation unrun. Browser-level viewport override initially did not affect the intended tab; actual dimensions were verified before capturing narrow evidence via tab-scoped emulation. All overrides reset.
- P09 FAIL accessibility detail: both Not sure yet options expose role=button but no aria-pressed or aria-selected. Selected choices are not conveyed by these DOM attributes; native screen-reader behaviour not exercised.
- P10 PASS: browser reload requires reconnect as documented; same two accounts, EUR1207, HUFunknown, four incomes restored. No new setup prompt.

Prior UI-TEST-04 results for all three EUR income modes, decimal comma, balance replacement and invalid precision remain separately identified evidence at the same product-code revision; not rerun wholesale here.

## Complete reachable prototype path — synthetic only

Ran Connect -> Open design preview -> first-time journey -> Not sure yet -> skip account balance -> unknown income type -> Today. Unknown remains Not provided. Add balance1200 -> My Plan -> accept review -> cancel -> accept again -> complete -> Today shows completed copy and EUR1200 unchanged. No goal required; upcoming commitments remain unknown.

Information icon -> Assistant -> supporting transactions: three dated EUR12.99 example payments and example-subscriptions-v1. Back -> smaller-step what-if gives a read-only explanation. Statement entry -> unsupported-file error -> retry -> Reading disabled state -> three-transaction review -> reject subscription -> Save example analysis -> saved notice. Return Today EUR1200 unchanged. These interactions are preview-only and do not upload a file, call AI or persist an import/action.

Settings -> Reminders initially off -> enable -> invalid time25:61 rejected -> Every N days with0 rejected ->3 days18:30 saves preview preference -> off saves. No OS permission or notification scheduled. Preview settings explicitly say export/deletion/cloud/FX are future integrations.

Clicked simulated offline/stale/conflict/AI-unavailable controls; corresponding explanatory notices appeared. Offline income10 / No-add / Save blocked with draft retained; back after ready leaves EUR1200. These simulations supplement, not replace, P06/P07 real server failure/concurrency tests.

Browser prefers-dark emulation returned matchMedia=true but the current rendered form remained light in the immediate capture; dark-theme PASS not established. Reset emulation. No native dark-theme claim.

## U01-U22 checklist disposition for this run

- U01 PASS local token route; cloud OTP absent.
- U02 PARTIAL: v2 profile/accounts pass; legacy P0 balance/bills form unreachable from ordinary saved-data navigation.
- U03 BLOCKED: persisted personal-data preview/affordability route not connected.
- U04/U05 BLOCKED integrated: reserve/cancel/complete for saved finances unavailable. Prototype review lifecycle passes only as described above.
- U06/U07 BLOCKED UI: add obligation, invalidate accepted money step, remove/pay bill unreachable from /personal.
- U08/U09 BLOCKED integrated: actual CSV import/reimport with persisted accounts unavailable. Prototype analysis does not prove parsing/deduplication.
- U10 BLOCKED UI: debt entry/simulation absent from saved-data path.
- U11 BLOCKED integrated: saved-data Assistant absent; prototype what-if only. Offline evals separately pass; live AI unrun.
- U12 PARTIAL: real owned-API restart and browser reconnect preserve v2 data. Disconnect control absent from /personal; cloud second-device auth unimplemented.
- U13 BLOCKED UI: Learn unreachable from saved-data path; no lesson/quiz progress run.
- U14 BLOCKED UI: no export entry on /personal. Read-only API export succeeded and local copy excluded connection token; this is not Share/download UI acceptance.
- U15 BLOCKED UI: delete entry absent from /personal; no synthetic records deleted and no deletion acceptance claimed.
- U16 PARTIAL: unknown-balance guard and prior EUR validation evidence; legacy bill-date cases blocked. Historical date cannot be entered in the new income/balance forms.
- U17 BLOCKED integrated: obligations/debt clarification not connected; prototype unknown commitments copy only.
- U18 PARTIAL: rapid double-save income passes; action/bill/pay duplicates blocked by navigation; response lost after successful commit unrun.
- U19 PARTIAL: real API outage/recovery and draft retry passes in web. Phone Wi-Fi/network test unrun.
- U20 PARTIAL:360x800 income form fits, no horizontal overflow; phone keyboard/landscape/long multi-field forms unrun.
- U21 PARTIAL/FAIL: text labels and measured48px buttons; choice selected-state gap noted. Native screen reader, large system text and dark theme not accepted.
- U22 BLOCKED real import: preview Reading/error/retry passes only as a simulation. No actual damaged/large-file upload performed.

## Approved product J01-J12 and remaining pilot requirements

J01 PARTIAL: optional local profile/accounts proven; full progressive onboarding/resume with income schedule/obligations absent. J02 PARTIAL: local restart/reconnect proven; cloud OTP, second user/device isolation and session restoration blocked by unimplemented integration. J03/J04 BLOCKED: import/corrections/overlap/own-transfer/manual-income matching not integrated. J05 BLOCKED: irregular expected-income delay not implemented in this path. J06 BLOCKED: multi-goal priorities/dates/allocation unavailable. J07 BLOCKED: debt clarification/scenarios not integrated. J08 BLOCKED: persisted money-action lifecycle unavailable. J09 PARTIAL: financial-command conflict tested; recommendation stale-worker publication UI unavailable. J10 PARTIAL: preview explanation/what-if only; persisted conversation and contextual lesson absent. J11 PARTIAL: actual network failure tested; real AI/FX/worker failure paths unrun/unintegrated. J12 BLOCKED UI: export/delete/restore unavailable in saved-data navigation; read-only API export is supplemental only.

Reminders and cold-start shortcut: preview scheduling controls tested; real notifications/permissions/timezone/sign-out/shortcut unavailable. HUF account original amount/unknown supported; FX rates and converted totals absent. Original retention30days, deletion races, background-job recovery and cloud migration/backup require their planned integrations and cannot be accepted by this local UI run.

## Supplemental verification — actual commands

- python scripts/check.py:217 tests,13.044s, OK, exit0; .local/ui-test-05-backend.txt. Initial same command also exited0; repeated to preserve a complete readable log after streamed output truncation. Negative-fixture FAIL text inside successful tests is not a failing final suite.
- services/api: python -m unittest discover -s tests -p test_journeys.py -v:31 tests,4.866s, OK, exit0; .local/ui-test-05-journeys.txt. Initial log redirection used a wrong parent path and failed before tests; corrected and rerun.
- mobile npm run typecheck: exit0, no TS errors.
- python scripts/generate-contracts.py --check: Contract check passed, exit0.
- python evals/run.py --offline:60/60 PASS,1.648s, exit0; generated evals/reports/latest.json updated. Not a live Gemini result.
- node scripts/check-ui-regressions.cjs:6/6 PASS, exit0. Static source assertions are not browser acceptance.
- Authenticated read-only API snapshot: revision8, EUR120700 minor units, HUFnull, four incomes; legacy snapshotnull/actions0/transactions0. API export copied to ignored .local/ui-test-05-export.json; no connection token present. No other secret scan claim.
- git initial checkpoint: nothing to commit, clean tree. Final diff check/commit performed after report writing.

## Evidence, outstanding work and stop condition

Ignored local evidence: ui-test-05-browser.txt (observed AX states), ui-test-05-personal.png, ui-test-05-preview.png, ui-test-05-mobile-width.png; API/test logs and test DB/export retained. Credentials not committed. API8001 stopped after verification; existing API8000/Expo retained.

This session exhausted the ordinary-user persistent navigation path and the reachable prototype flow. It does NOT establish full workflow PASS. First unblock integration/navigation from /personal; then run legacy P0 U02-U18 and new J03-J12 against the same saved account model, followed by Android/iPhone accessibility and reliability checks. Income/balance forms also lack date entry and income form lacks balance confirmation date (UI-TEST-04). No fixes, acceptance-status changes or release gate promotion performed.
