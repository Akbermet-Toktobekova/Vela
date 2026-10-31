# Profile-aware specialist adapters (T56b)

Three read-only Gemini roles follow USER_VISION: `cash_flow` (spending and cash flow),
`debt`, `savings_goals`. `specialist_agents.analyze_bundle` runs them concurrently on
one immutable bundle with run, financial, preference and policy versions. Profile
focus, income type, explicit preferences and restrictions affect relevance. They
never imply capacity, personal weights, debt certainty or goal type.

The upstream caller supplies trusted calculator evidence, already validated candidate
references and explicit missing-input references. Each role receives only its own
references. Output contains references only, with exact version echoes; invented,
duplicate, cross-role and wrong-kind references are rejected. A candidate requires
calculator evidence. Code must render the referenced material, not model prose.
This adapter is not a financial constraint checker: the eventual coordinator must
revalidate candidates and versions against current owner data before ranking and
publication. User profile text is untrusted and cannot grant financial authority.

The existing `ai.generate` gateway owns PII masking, opt-in activation, model routing,
quota reservation and provider fallback. This slice uses the existing `chat` route
(currently configured Flash-Lite models); it does not introduce or validate a new
Gemini model ID. No paid/live calls were made. API keys remain server-side.

One request per role goes through that gateway, which can attempt its configured
fallback model. Each role has a ten-second outer deadline by default, including
gateway fallback. Failures, invalid responses, unavailability and timeouts have
distinct statuses and no proposal. A failed debt role never means no debt. The
adapter performs no state writes and has no access to the store or user DB.

## Integration boundary

This is a separately testable adapter, not a completed recommendation pipeline.
T56a owns canonical weighted evaluation; T57a owns its shared publication/API.
Parent T56/T57 still own complete calculators, specialist orchestration, mandatory
barriers, invalidation, caching and background jobs. A caller must construct the
bundle from a same-owner consistent snapshot, include approved profile fields only,
and exclude raw documents and identifying details. Those owner/API integration
checks are not established by these adapter tests. Do not wire an additional
competing primary card. No automatic transfers or model-produced financial math.

Verification: mocked provider tests cover profile propagation, role isolation,
version mismatch, malformed output, invented references, deadlines/cancellation,
immutability and disabled Gemini. Live provider schema compatibility and integrated
recommendation quality remain unverified; independent review is required.
