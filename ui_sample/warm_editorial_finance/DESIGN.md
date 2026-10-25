---
name: Warm Editorial Finance
colors:
  surface: '#fff8f5'
  surface-dim: '#e6d7cc'
  surface-bright: '#fff8f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fff1e7'
  surface-container: '#fbebdf'
  surface-container-high: '#f5e5da'
  surface-container-highest: '#efe0d4'
  on-surface: '#221a13'
  on-surface-variant: '#4d4540'
  inverse-surface: '#372f27'
  inverse-on-surface: '#feeee2'
  outline: '#7f756f'
  outline-variant: '#d0c4bd'
  surface-tint: '#655d58'
  primary: '#130e0a'
  on-primary: '#ffffff'
  primary-container: '#29231f'
  on-primary-container: '#938984'
  inverse-primary: '#d0c4be'
  secondary: '#9a4527'
  on-secondary: '#ffffff'
  secondary-container: '#fd916d'
  on-secondary-container: '#74290d'
  tertiary: '#140e08'
  on-tertiary: '#ffffff'
  tertiary-container: '#2a231c'
  on-tertiary-container: '#95897f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ece0da'
  primary-fixed-dim: '#d0c4be'
  on-primary-fixed: '#201a17'
  on-primary-fixed-variant: '#4d4541'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59d'
  on-secondary-fixed: '#390c00'
  on-secondary-fixed-variant: '#7b2e12'
  tertiary-fixed: '#eee0d4'
  tertiary-fixed-dim: '#d1c4b9'
  on-tertiary-fixed: '#211a13'
  on-tertiary-fixed-variant: '#4e453d'
  background: '#fff8f5'
  on-background: '#221a13'
  surface-variant: '#efe0d4'
typography:
  display-hero:
    fontFamily: Manrope
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Manrope
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Manrope
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.005em
  headline-sm:
    fontFamily: Manrope
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  body-lg:
    fontFamily: Manrope
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: 0em
  body-md:
    fontFamily: Manrope
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Manrope
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.005em
  label-md:
    fontFamily: Manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  currency-display:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  currency-tabular:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: 0em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style
This design system crafts an atmosphere of quiet dignity, emotional clarity, and non-judgmental support for young adults navigating personal finance for the first time. The visual philosophy firmly rejects the gamified urgency, flashing streak counters, and panic-inducing alert reds typical of traditional consumer fintech. Instead, it draws from warm editorial publishing and mindful self-care tools: spacious, grounded, patient, and deliberate. 

The experience focuses cognitive energy on "one manageable next step" rather than sprawling, anxiety-inducing dashboards. The aesthetic movement is **Warm Editorial Minimalism**: soft paper-like ivory surfaces, rich espresso typography, deliberate tactile micro-borders, and comforting burnt orange accents that encourage action without raising alarm.

## Colors
The color architecture relies on organic, grounded pigments that evoke fine paper, aged book cloth, and quiet study spaces:

- **Canvas & Surfaces:**
  - Base Background: Warm Ivory (`#FAF8F5`). Provides a calm, low-glare reading environment.
  - Surface Raised / Recommendation Cards: Pure White (`#FFFFFF`) or Warm Ivory tinted with high opacity to lift gently off the canvas.
  - Structural Borders & Hairlines: Soft Cream / Decorative Divider (`#E6DED5`). Used for whisper-quiet section delineation.
- **Brand & Actions:**
  - Primary (Deep Brown, `#29231F`): Authoritative, deep, and grounded. Applied to primary CTAs, main headlines, and key balances.
  - Secondary Accent (Burnt Orange, `#9C4628`): Used sparingly for high-value forward actions, selected states, and progressive encouragement.
  - Tertiary / Muted Container (Soft Apricot, `#F6E8DC`): Soft, pillowed containers, badge backgrounds, and secondary touch targets.
- **Guidance & Non-Alarmist Attention:**
  - Attention Surface (`#FFF1D9`) paired with Attention Text (`#7A4E16`): Replaces harsh amber or red warning banners with an inviting, gentle callout tone for items requiring review.
  - Body & Auxiliary (`#6D6259`): Soft Espresso for body copy, timestamps, and secondary balance metadata, ensuring legible contrast without stark, clinical black.

## Typography
Manrope serves as the sole typographic voice, balancing geometric clarity with humanist balance.

- **Tabular Figures (`tnum`):** All numeric data, transaction rows, balances, and dates must explicitly enforce OpenType tabular figures (`font-variant-numeric: tabular-nums`). This eliminates layout shifting when numbers update and preserves precise column alignment.
- **Editorial Hierarchy:** Headlines use a restrained medium-to-semibold weight rather than heavy blacks, ensuring monetary balances feel composed rather than overbearing.
- **Sentence Case:** Capitalization is consistently sentence-case across all headers, action buttons, and badges to preserve a calm, conversational tone.

## Layout & Spacing
Built on a strict 8px spatial grid with an underlying 4px half-step for precise micro-alignment.

- **Mobile Viewport Shell:** Standard canvas margins are set strictly to `20px` (`1.25rem`) to maintain an open, non-constricted frame on mobile displays.
- **Grid Structure:** A single-column vertical flow is the primary paradigm on mobile devices, preventing fragmented multi-column cards and keeping the user focused on sequential, digestible information blocks.
- **Breathing Room:** Major functional clusters (e.g., current focus task vs. past ledger) are separated by `space-xl` (`32px` / `2rem`), allowing cognitive rest between analytical details.

## Elevation & Depth
Depth in this system is conveyed through warm tonal stratification and structural hairline boundaries rather than high-contrast drop shadows.

- **Tonal Layering:** The primary canvas sits at `#FAF8F5`. Elevated recommendation cards and active surface containers utilize pure `#FFFFFF` resting atop the warm canvas, establishing quiet physical hierarchy without casting synthetic grey shadows.
- **Ambient Warm Shadow:** Where visual elevation is strictly necessary for touch affordance (such as modal sheets or floating primary action bars), apply an ultra-diffuse, warm-tinted shadow:
  `box-shadow: 0 8px 24px -4px rgba(41, 35, 31, 0.05), 0 2px 6px -1px rgba(41, 35, 31, 0.03);`
- **Quiet Borders:** Most components maintain structural separation via a subtle 1px border using Decorative Divider (`#E6DED5`), evoking finely ruled paper margins.

## Shapes
The shape system balances modern structural cleanliness with approachable, organic softness.

- **Recommendation & Hero Cards:** Standardized to a generous `24px` radius (`1.5rem`), giving key narrative cards a soft, welcoming, and protective silhouette.
- **Buttons & Interactive Controls:** Primary, secondary, and tertiary buttons strictly use a `14px` corner radius (`0.875rem`), harmonizing with the 24px parent containers without degenerating into full capsule pills.
- **Small Chips & Badges:** Use an `8px` or `12px` radius for small status indicators and category tokens.

## Components

### Buttons
- **Primary CTA:** Background `#29231F`, text `#FAF8F5`, height `52px`, radius `14px`, `label-md` semibold. Active state lowers opacity to `0.92`.
- **Secondary Accent:** Background `#9C4628`, text `#FFFFFF`, height `52px`, radius `14px`. Reserved for single critical progression steps (e.g., "Confirm Budget Strategy").
- **Tertiary / Soft Action:** Background `#F6E8DC`, text `#29231F`, height `44px`, radius `14px`. Ideal for non-demanding optional steps.
- **Ghost:** Transparent background, text `#6D6259`, padding `space-sm` `space-md`.

### Recommendation Card ("One Next Step")
- **Visuals:** Background `#FFFFFF`, 1px border `#E6DED5`, radius `24px`, padding `space-lg` (`24px`).
- **Layout:** Features an optional micro-badge at top, a concise single-line narrative title in `#29231F`, an encouraging 2-line explanation in `#6D6259`, and a single action trigger pinned to the bottom. Never overload with multiple competing CTAs.

### Attention & Guidance Banner
- **Visuals:** Background `#FFF1D9`, border 1px solid rgba(122, 78, 22, 0.15), radius `16px`, padding `space-md`.
- **Typography:** Text in `#7A4E16`, `body-sm` or `label-md`.
- **Philosophy:** Used when an account requires re-linking or spending needs attention. Completely avoids red hazard icons, using gentle informative phrasing instead.

### Chips & Tags
- **Category Filter:** Height `32px`, radius `10px`, background `#FAF8F5`, border 1px solid `#E6DED5`, text `#6D6259`.
- **Selected State:** Background `#29231F`, text `#FAF8F5`, border 1px solid `#29231F`.

### Input Fields
- **Container:** Height `52px`, background `#FFFFFF`, border 1px solid `#E6DED5`, radius `14px`, horizontal padding `16px`.
- **Typography:** Value in `#29231F` (`body-md`), placeholder in `#6D6259` with 60% opacity.
- **Focus State:** 1.5px border in `#29231F`, no outer neon glow.

### Lists & Ledger Items
- **Row:** Height `64px`, border-bottom 1px solid `#E6DED5`.
- **Layout:** Leading soft icon/glyph container (`40x40px`, radius `10px`, background `#F6E8DC`), central merchant title (`headline-sm`) with category below (`body-sm`), trailing currency amount formatted in `currency-tabular`.