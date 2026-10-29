# Vela design system — approved direction, 2026-10-29

English, quiet neutral surfaces, dark text, restrained green accent, Manrope. This document specifies the target; current application compliance requires device evidence.

## Tokens (React Native logical units)
Body 16; supporting 14; screen heading 28; main money 32. Spacing 4/8/12/16/24/32. Buttons minimum height 48, icon hit area 48×48. Button radius 12, card radius 16. Font scaling and wrapping can increase component height; no fixed text containers. Normal text contrast >=4.5:1, large text >=3:1. Light/dark palettes use semantic roles; status also has text/icon. theme.ts is the executable source; update this document with deliberate token changes.

## Components and behaviour
Primary/secondary/text/destructive buttons and accessible icon button; money field with visible currency; account/date/period selectors; labelled field with helper/error; next-step card; dated balance; goal/obligation row; consequence confirmation; empty/loading/error/offline/conflict states; chat/evidence rows.
One dominant action per decision. Primary buttons have normal/pressed/loading/disabled states. Explain unavailability; errors stay next to input and preserve draft. Money keyboards support decimal locale and reject ambiguous precision. Date selection must not require typing ISO syntax. Keyboard never covers action/input. Destructive actions state consequences before confirmation.
Information icon has accessibility label Explain this recommendation, opens Assistant with stored recommendation context. Icon-only controls have labels, focus order, state and generous targets.

## Verification
Small phone, landscape where supported, large text, long amounts/labels, screen reader, both themes, keyboard and back navigation. Test Today, Add income, import failure and contextual explanation. Screenshots show layout, actual task runs prove interaction. Never mark unrun native checks passed.
