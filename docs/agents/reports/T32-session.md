# T32 session adapter — delegated implementation

- Status: review (bounded mobile adapter part of T32; no independent acceptance).
- Date: 2026-10-29.
- Model: Codex delegated executor.
- Parent owns canonical T32 status, integration checks and commits.

## Delivered

`session.ts` provides Supabase email OTP request/verify, refresh and local-scope provider sign-out using existing fetch. Trusted configuration requires an HTTPS `/auth/v1` URL and a public publishable or legacy anon key; secret/service-role keys, credentials/query/fragment URLs and cleartext provider URLs are rejected. This client does not authenticate financial ownership: API JWT verification remains authoritative.

The adapter exposes sanitized invalid-code, expired-code, rate-limited, unavailable and signed-out errors. Retry-After seconds are used only if supplied by the provider; no invented resend cooldown. Provider requests have a bounded timeout and reject redirects. Rotation uses single-flight refresh, including concurrent late401 responses. A failed refresh or repeated401 clears credentials. Logout clears locally before attempting remote logout and returns `remoteSignedOut:false` when remote delivery fails. Generation checks prevent an in-flight refresh or old-account API response from reviving a signed-out session.

`api.ts` exports `configureCloudSession({apiUrl,authUrl,publicKey})`, `requestSignInCode`, `verifySignInCode`, `restoreCloudSession`, and `signOutCloudSession`. Existing local Connection/connect/restore/disconnect interfaces remain. Cloud API requests and both upload paths use the current access token. One401 refresh/retry preserves the already-serialized financial body and caller-supplied idempotency key;409 and503 do not trigger refresh or duplicate requests. Web upload reuses the same FormData object. Cloud API URLs require trusted HTTPS and request paths stay relative.

Native storage uses existing SecureStore for the refresh credential only, scoped to the configured provider and API URL. Access tokens stay in memory. Web stores neither credential in localStorage/sessionStorage; reload requires sign-in again. Native process restoration receives public deployment config then exchanges its stored refresh credential with the provider. No credentials are embedded in code or shown in reports.

## Changed files

- apps/mobile/src/lib/session.ts — provider/session implementation with injectable transport, clock and refresh storage.
- apps/mobile/src/lib/api.ts — explicit cloud adapter and authenticated request/upload wiring.
- apps/mobile/src/lib/session.test.cjs —17 focused deterministic tests, TypeScript transpiled with existing installed compiler and native Node test runner.
- scripts/check-ui-regressions.cjs — parent-authorized one-line loader support for the new `./session` import; existing assertions/test count and historical `--baseline` support preserved.
- This report.

No dependency, API schema, UI screen, backend code, financial rule or deployment changed by this delegate. The sibling backend delegate owns docs/product/authentication.md; this report provides the mobile integration contract for parent incorporation.

## Actual checks

```text
node --test apps/mobile/src/lib/session.test.cjs
17 tests;17 pass;0 fail;0 cancelled;0 skipped
 duration_ms 2532.873

npm run typecheck --prefix apps/mobile
> vela-mobile@0.1.0 typecheck
> tsc --noEmit
exit0

node scripts/check-ui-regressions.cjs
6/6 PASS

node scripts/check-ui-regressions.cjs --baseline HEAD
6/6 PASS

 git diff --check -- apps/mobile/src/lib/api.ts apps/mobile/src/lib/session.ts apps/mobile/src/lib/session.test.cjs scripts/check-ui-regressions.cjs
exit0
```

The17 checks cover actual provider paths/bodies/public headers, config/secret rejection, sanitized error/rate metadata, expiry and8 concurrent refresh consumers, late401 rotation, failed refresh/repeated401, native restore/web nonpersistence, remote logout failure and stale-refresh race, malformed provider success, API immutable financial retry identity, web FormData retry/current token, native base64/current token, local compatibility, sign-out during an API response, provider timeout,503 nonretry, and cross-deployment refresh rejection.

Two early test-harness failures were corrected: the local TypeScript require path initially traversed one directory too far; a cross-VM deepStrictEqual of a structurally identical logout result needed scalar comparison. The initial failed race test exited after its outstanding mocked timer; subsequent full focused run above passed. No implementation failure or result is omitted. Typecheck passed both runs. Parent requested centralized full backend after all delegates freeze; this delegate did not run it or claim new backend totals.

## Primary-source protocol verification

Official Supabase documentation and SDK source were read for wire semantics (no live provider request):

- [Email OTP](https://supabase.com/docs/reference/javascript/auth-signinwithotp), [verification](https://supabase.com/docs/reference/javascript/auth-verifyotp), [refresh](https://supabase.com/docs/reference/javascript/auth-refreshsession), [sign-out](https://supabase.com/docs/reference/javascript/auth-signout).
- [GoTrueClient source](https://github.com/supabase/auth-js/blob/master/src/GoTrueClient.ts): `/otp` with email/create_user; `/verify` with email/token/type=email; `/token?grant_type=refresh_token` with refresh_token.
- [GoTrueAdminApi source](https://github.com/supabase/auth-js/blob/master/src/GoTrueAdminApi.ts): POST `/logout?scope=local` with the current access JWT.

## Limits and orchestrator handoff

No live OTP email, provider session, real account, device keystore or cloud database was exercised; all network responses were injected mocks. Public deployment configuration/SMTP/template/CAPTCHA requirements remain actual activation evidence. Token revocation on other servers is not promised: already issued JWT validity follows provider/backend policy. `remoteSignedOut:false` means local sign-out completed but remote sign-out was not confirmed.

T52 still owns visible sign-in/resend/change-email flows and account-specific query-cache clearing. This adapter is a testable prerequisite, not a claim that those screens or complete J02 are delivered. Cloud configure/session functions must be called by that future path; existing local screens remain local. No background auto-refresh timer is introduced; access tokens refresh when needed by requests or explicit restore/refresh. A storage-device failure can prevent physical deletion and is surfaced rather than claiming secure erasure.

No demo.db, API8000–8003, standalone HTML, live account data, paid service, global package installation, other process or git staging/commit was touched. Source frozen for independent T32 security/integration review.
