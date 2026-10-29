---
name: uxpeak
description: Design, implement and review Vela mobile screens, components, navigation and financial UX. Use for Vela UI changes and usability checks; follow the approved pilot journeys and shared design system.
---

# uxpeak

Read docs/product/PILOT_SPEC.md for affected behaviour and docs/design-system.md for components/tokens. Read only relevant sections; do not reload the whole backlog for a component edit.

1. State the person's task, entry, successful exit and records changed. Check the backlog scope.
2. Reuse components/ui.tsx and theme.ts before adding screen-local styles. One primary decision at a time; reveal supporting detail on request.
3. Specify loading, empty, failure, offline, stale and conflict states where applicable. Preserve input and never fake server success.
4. Show source/date/currency for money. Unknown is not zero. Statement analytics cannot mutate balances. Acceptance is not execution. What-if stays read-only.
5. Information icon opens Assistant for the specific stored recommendation/version. Never require the person to retype context.
6. Check target size, contrast, scaling, screen reader labels, keyboard, long text, back navigation and destructive confirmation against the design system.
7. Run affected checks. Report actual device/browser/build used and clearly list unrun checks. A mockup is not integrated acceptance.

Deliver: purpose, entry/exit, exact English copy/actions, states, data effects, accessibility, verification and limitations. Do not invent financial thresholds, change product scope, add dependencies outside the task or authorize deployments.

For interaction proof read references/acceptance.md. Token values live in the design system, not here.
