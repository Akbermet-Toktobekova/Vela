/**
 * Vela Financial System Design Tokens
 * Apple-style Light Theme
 */

export const colors = {
  // Base / Surfaces
  background: "#FFFFFF", // Pure White
  surface: "#F8F9FA", // Surface / Cards
  cardBackground: "#F8F9FA",
  surfaceContainerLow: "#F3F4F5",
  surfaceContainer: "#EDEEEF",
  surfaceContainerHigh: "#E7E8E9",
  surfaceBright: "#E7E8E9",

  // Borders & Outlines
  cardBorder: "#C6C6CD", // Outline Variant
  borderVariant: "#C6C6CD",
  outlineVariant: "#C6C6CD",
  outline: "#76777D",

  // Text & Hierarchy
  textPrimary: "#191C1D", // on-surface
  textSecondary: "#45464C", // on-surface-variant
  textMuted: "#76777D", // Muted Text / Outline
  onSurface: "#191C1D",
  onSurfaceVariant: "#45464C",

  // Primary & Secondary Brand Accents
  primary: "#0058BC", // Primary Accent (secondary)
  primaryLight: "#0070EB", // Secondary Container
  secondaryContainer: "#0070EB",
  accent: "#0058BC",
  accentLight: "#0070EB",
  accentWarning: "#F59E0B",
  accentDanger: "#93000A",

  // 50 / 30 / 20 Financial System Tokens
  needsColor: "#53E16F", // Needs (tertiary-fixed-dim)
  needsLight: "rgba(114, 254, 136, 0.2)", // #72FE88 at 20% opacity
  wantsColor: "#FFDAD6", // Wants (error-container)
  wantsText: "#93000A", // Wants Text
  savingsColor: "#0058BC", // Savings Color

  // Love & Emotional Accent
  loveAccent: "#FF2D55", // Apple Love Accent
  loveBg: "rgba(255, 45, 85, 0.1)",
  lovePill: "#0070EB", // secondary-container used for love pill
  lovePillBg: "rgba(0, 112, 235, 0.1)",

  // UI Components (Chat Bubbles, Tab Bar)
  userBubble: "#0058BC",
  agentBubble: "#F3F4F5",
  tabBarBg: "rgba(248, 249, 250, 0.8)", // with backdrop blur
} as const;

export type Colors = typeof colors;
export type ColorKey = keyof Colors;
