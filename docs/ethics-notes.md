# Technical ethics checklist

- [x] Four synthetic personas; no real financial or personal records committed.
- [x] Every transfer is simulated; no bank/payment API integration.
- [x] Educational disclaimer shown in the application and assistant replies.
- [x] Decision controls: accept, adjust, decline; rule edit/pause/resume.
- [x] Affordability hard filters and execution-time cash-floor checks.
- [x] Stress guard persists blackout expiry; recommendation frequency is serialized in SQLite.
- [x] Structured numeric facts accompany explanations; unsupported numbers trigger fallback.
- [x] LLM-selected candidate ids are constrained to the affordable set.
- [x] Tone filter has 30 accepted and 30 rejected phrase tests; UI has no red alarm styling.
- [x] Default fake provider works offline; optional external-provider data flow is disclosed.
- [x] Imports are processed locally; delete-data clears application records and the LLM cache.
- [x] Historical decisions and rule outcomes are append-only through application APIs.
- [ ] Manual WCAG AA audit and assistive-technology/browser validation remain outstanding.
- [ ] Live-model tone/faithfulness evaluation remains outstanding; fake results cannot establish it.
- [ ] Numeric token matching cannot establish semantic correctness or eliminate misleading context.
- [ ] SQLite/cache storage is not encrypted; deletion is not secure erasure of filesystem remnants.
- [ ] User study / independent expert action labels have not been produced.

This is an implementation checklist, not thesis prose, a legal assessment, or a financial recommendation.
