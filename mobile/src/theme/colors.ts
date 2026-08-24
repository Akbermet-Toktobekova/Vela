export const colors = {
  // Revolut 10 Ultra Background Palette
  background: '#F8F9FB',          // Soft, soothing, eye-friendly off-white canvas
  backgroundPure: '#FFFFFF',      // Pure white for crisp contrast highlights
  surface: '#FFFFFF',             // Card background (floating clean cards)
  surfaceSecondary: '#F1F3F6',    // Subtle secondary container
  surfaceMuted: '#EAECEF',        // Active pill background
  
  // Borders & Dividers
  border: '#ECEEF2',              // Ultra-soft, elegant card border
  borderLight: '#F3F4F7',         // Subtle row divider
  
  // Typography
  text: '#111417',                // Deep luxury charcoal (softer than harsh #000)
  textSecondary: '#646B73',       // Balanced neutral secondary text
  textMuted: '#949BA2',           // Muted captions & timestamps
  
  // Primary Action & Accents
  primary: '#111417',             // Revolut Black Primary
  accentBlue: '#0075EB',          // Revolut Signature Royal Blue
  accentBlueLight: '#E8F2FF',     // Soft Blue Pill BG
  accentGreen: '#00C853',         // Vibrant Positive Financial Green
  accentGreenLight: '#E6F9EE',    // Soft Green Pill BG
  accentPurple: '#7B61FF',        // Revolut Invest/Wants Purple
  accentPurpleLight: '#F3EFFF',   // Soft Purple Pill BG
  accentPink: '#FF3366',          // Revolut VIP Accent Pink
  accentPinkLight: '#FFF0F4',     // Soft Pink Pill BG
  accentOrange: '#FF9500',        // Warning / Avalanche Orange
  accentOrangeLight: '#FFF5E6',   // Soft Orange Pill BG
  
  // Utility
  pillBg: '#EDF0F4',
  danger: '#FF3B30',
  white: '#FFFFFF',
  shadowColor: '#0A101D',
} as const;

export type Colors = typeof colors;
