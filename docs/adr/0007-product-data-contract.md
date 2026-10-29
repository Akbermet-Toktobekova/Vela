# ADR 0007 — Compatible product aggregates and financial authority

Date: 2026-10-29. Status: accepted after independent T50 architecture review; [evidence](../agents/reports/T50-independent.md). Detailed contract: [product-data-v1](../product/data-contract.md). Infrastructure follows accepted [ADR0001](0001-database-and-auth.md); product behaviour follows [PILOT_SPEC](../product/PILOT_SPEC.md).

## Context

Current [State](../../services/api/vela/domain.py), [personal data](../../services/api/vela/personal.py) and [local plan](../../services/api/vela/planning.py) retain legacy JSON alongside a canonical selected EUR account. The [store](../../services/api/vela/store.py) separately persists owner-keyed receipts/previews/runs/publications. T75 [frontend projection](../../services/api/vela/frontend.py) exposes current local facts but is not cloud ownership, a persistent conversation store or a published recommendation identity. Expanding these by silently copying money into every screen/entity would violate no-double-count and migration requirements.

## Decision

Adopt the logical aggregate and authority contract in product-data-v1. Separate confirmed finances, historical analytics, explicit preferences and immutable derived results. Derive owner from verified sessions; validate every child reference within that owner. Keep unknown distinct from zero, amounts as integer minor units plus currency, dates/provenance/confirmation explicit and expected income separate from received events. Statements and observations never cause financial effects.

Keep one canonical account balance and allocation/execution identities. Reservation is intention, completion has explicit effect type, and later statement matching adds evidence rather than replaying money. Preserve versioned facts/calculations and publication IDs so Today/Assistant explain the same decision. Keep no-goal/no-statement paths and voluntary learning.

Retain existing owner aggregate JSON and store tables through the baseline migration, then expand under task-owned versioned migrations; no requirement for one table per logical entity. Preserve `/v1` compatibility and accepted post-adoption guards while `/v2` grows with generated contracts. T75's local projection/capability schema stays distinct from persisted schema and future immutable recommendation versions. T50 adds documentation only.

## Consequences and implementation ownership

The [A–J trace](../product/data-contract.md#a–j-ownership-and-implementation-trace) names every data authority and later task. T31 owns baseline migration, T32 owner isolation, T51/T52 profile/session flow, T33/T34/T53 import lifecycle/reconciliation, T54/T55 scenarios and goals, T56/T57 same-version publication, T58 execution, T59 conversations, T60/T61 reviewed learning/policy, T62 export/delete/restore and T63 end-to-end evidence. Reminder preferences/device state remain T68/T69. Each implementation must publish exact new route schemas before frontend use.

Aggregate JSON reuse avoids premature table proliferation but does not remove transaction/concurrency/ownership obligations. Fields with independent expiry or lease/query requirements may require dedicated records. Existing strict readers can reject expanded JSON: additive schema alone is not proof of binary rollback compatibility. No cloud data acceptance, financial calibration or paid activation follows from this ADR.

## Migration and rollback boundary

Use fresh populated synthetic fixtures to prove old JSON and expanded personal/planning preservation, original histories/receipts/previews/runs/publications and exact money/date/source/link equality. Do not inspect working demo.db. Do not auto-upload or relabel local data as cloud-owned/user-confirmed. Keep existing provenance and legacy current-mode safeguards.

Destructive upgrade/downgrade cycles are limited to disposable fixtures. A populated system rolls back only through a documented compatible schema/application pair and an independently tested preserved copy/export; external files/jobs and deleted-owner safety must be included by T62. This is a design boundary, not a zero-loss restoration claim. See the [preservation acceptance](../product/data-contract.md#migration-preservation-and-rollback-acceptance).

## Decisions deliberately not invented

No new financial weights, percentage rules, certainty/observation thresholds, unsupported debt products, fee assumptions, confidence scores or provider backup promises. Missing financial assumptions remain explicit clarification/blockers and T61 human review. Existing approved Supabase/OTP/Render, 30-day original expiry and no-cloud-upload gate are carried forward rather than reopened.
