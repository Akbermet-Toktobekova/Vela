# Authentication contract

2026-10-29, T32. Backend implementation is subject to independent security review. Synthetic mocked-provider tests do not establish live Supabase/SMTP/PostgreSQL or cross-device readiness. Architecture: [ADR0001](../adr/0001-database-and-auth.md); owner contract: [product-data-v1](data-contract.md).

## Backend mode and trusted configuration

`APP_MODE=local` selects the existing single-user local bearer token and owner `local-demo`. Unset/`demo` remains a deprecated local compatibility alias. `APP_MODE=cloud` selects verified asymmetric Supabase JWT identity; unknown modes fail startup. `APP_ENV` has no effect. A cloud request cannot fall back to `DEMO_API_TOKEN`, and local state is never automatically relabelled as a cloud user.

Cloud startup requires an explicit database URL (factory argument or `DATABASE_URL`) and all trusted JWT settings before creating storage:

- `SUPABASE_URL`: exact HTTPS project origin, without path/query/credentials/trailing slash.
- `SUPABASE_JWT_ISSUER`: that origin plus `/auth/v1`.
- `SUPABASE_JWKS_URL`: issuer plus `/.well-known/jwks.json`.
- `SUPABASE_JWT_AUDIENCE`: explicit nonempty configured audience.
- `SUPABASE_JWT_ALGORITHMS`: explicit comma-separated supported signing algorithms, `ES256` and/or `RS256`, matching the actual project configuration.

No signing algorithm, project identifier, audience or secret is guessed. Legacy HS signing is unsupported and has no automatic fallback. Actual project settings/SMTP/activation remain T70 evidence. Never put service-role/database credentials into mobile configuration or send local user data to a cloud database automatically. Synthetic tests supply a new SQLite file and a mocked trusted-key transport explicitly; this does not validate a PostgreSQL driver, server, RLS or backup policy.

## Verification and request behaviour

All existing protected routes and installed personal/planning/frontend routes resolve the same owner from verified JWT `sub`; a request body/account path cannot choose that identity. Strict request models reject unexpected `user_id` fields. A missing/foreign child reference fails within the authenticated owner's records. Existing five tables already include owner keys/predicates, so no schema or store change is needed for this bounded implementation.

The verifier checks signature, explicitly allowed asymmetric algorithm, configured issuer/audience, required integer expiry and nonempty string subject. Optional `iat`/`nbf` must be integer timestamps no later than current server time. Reserved `local-demo` cannot be a cloud subject. Missing/expired/invalid credentials return401 with a generic sign-in message and `WWW-Authenticate: Bearer`; provider verification failure returns a sanitized503. Clients may refresh an expired session once through their provider adapter;503 is availability failure rather than proof of expired credentials. Financial conflicts remain409 and must not be converted into a new command.

The JWT cannot supply trust: `jku`, `x5u`, embedded `jwk`, unsupported critical headers and unexpected algorithms are rejected. Keys come only from the configured project JWKS over verified HTTPS, without redirects, ambient proxies or authorization credentials. Retrieval has a five-second httpx timeout and64KiB/32-key response limits. Supported public signature keys are cached for ten minutes. Unknown key IDs may refresh once, with a one-second minimum refresh interval to bound random-key floods; the next request after cooldown may resolve a rotation. Failed trusted verification never authorizes with a stale expired cache.

Local signature verification does not promise instant global logout revocation. A cached previously trusted key/access JWT can remain usable through the configured key-cache/access-token lifetime. Provider session revocation and signing-key rotation behaviour require operational review before activation; the mobile adapter must clear its own credentials immediately on sign-out regardless of remote outcome.

## Compatibility and evidence

Local API routes/financial payloads and idempotency remain compatible; `/health` reports the selected `local`/`cloud` mode. T75's `local-frontend-v1` projection and capability flags remain intentionally labelled local and disabled for cloud OTP/multi-user product readiness; T52 owns the later session-aware screens and account-cache lifecycle. A backend JWT verifier alone does not upgrade that product contract to completed cloud UX.

Declared dependency: `PyJWT[crypto]==2.15.1`, installed only in the project `.venv`; existing cryptography support is reused. Use `.venv/Scripts/python.exe` or activate with `. .\.venv\Scripts\Activate.ps1`. Implementation follows [PyJWT usage](https://pyjwt.readthedocs.io/en/stable/usage.html), [algorithm trust warning](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode) and [Supabase JWT documentation](https://supabase.com/docs/guides/auth/jwts).

`tests/test_isolation.py` uses generated EC/RSA signing keys, fixed claims/time, injected JWKS transport and disposable synthetic SQLite. It proves trusted-key cache/rotation, credential/config/header rejection, sanitized provider failure, redirect/size limits, A/B account/export/delete isolation and same-ID receipts/previews/runs/publications, plus local aliases and no cloud-token fallback. No real email, project, cloud account, provider request, paid AI or existing working database is involved. Full-backend and independent security acceptance are root-orchestrated gates.

<!-- Mobile adapter executor may append its session-adapter section below. -->

## Mobile session adapter (T32)

Configure the public deployment once with `configureCloudSession({apiUrl,authUrl,publicKey})` from `apps/mobile/src/lib/api.ts`. `apiUrl` is a trusted HTTPS Vela API address; `authUrl` is the trusted HTTPS Supabase `/auth/v1` address. `publicKey` accepts a publishable key or legacy public anon key and rejects secret/service-role keys. This configuration never contains database or service-role credentials.

The exported session operations are `requestSignInCode(email)`, `verifySignInCode(email,code)`, `restoreCloudSession()` and `signOutCloudSession()`. OTP request/verification and refresh go directly to the configured provider; only the access JWT goes to the Vela API. Provider email templates must deliver a code, and actual SMTP/CAPTCHA/deployment settings remain activation evidence. Errors expose calm invalid-code, expired-code, rate-limited, unavailable and signed-out states. A resend delay is taken only from provider Retry-After metadata; no fixed financial/product cooldown is invented.

Native SecureStore holds only the refresh credential and its provider/API scope; the access token remains in memory. After a native restart, supply the same public configuration then call `restoreCloudSession()`. A credential scoped to another deployment is cleared. Web stores both credentials only in memory and requires another sign-in after reload. Existing local `connect`, `restoreConnection` and `disconnect` behaviour remains available separately.

Requests refresh expired tokens on demand with one shared refresh operation. An API401 can refresh and retry once; the retry retains the exact serialized command and caller-provided idempotency key.409 conflicts and503 availability failures do not refresh or duplicate commands. Both upload paths take the current access token; a web retry reuses the same FormData. Logout clears local credentials before attempting provider sign-out and returns `{remoteSignedOut:false}` if that remote action cannot be confirmed. An in-flight refresh or old-account API response cannot restore a signed-out session. Immediate provider-wide JWT revocation is not promised.

Offline evidence: `node --test apps/mobile/src/lib/session.test.cjs` passed17 mocked-provider tests; `npm run typecheck --prefix apps/mobile` passed; existing `node scripts/check-ui-regressions.cjs` remains6/6. These prove session/transport mechanics, expiry/concurrency/logout races, command retry identity, error handling and storage boundaries. They do not prove actual OTP delivery, native keystore/device behaviour or cloud integration. T52 owns visible sign-in/resend/change-email screens and account-specific cache clearing; this adapter alone does not complete J02.
