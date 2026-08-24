export const colors = {
  // Revolut 10 Signature Gradient Palette
  gradientTop: '#1E68FF',         // Royal cobalt blue
  gradientMid: '#3984FF',         // Vibrant sky electric blue
  gradientBottom: '#6BA4FF',      // Luminous silk blue
  
  // Card & Sheet Surfaces (Frosted Glass / Silk Cards)
  sheetBg: '#FFFFFF',             // Clean white bottom sheet / cards
  sheetGlass: 'rgba(255, 255, 255, 0.88)', // Frosted glass card
  cardBg: '#FFFFFF',
  cardMuted: '#F4F6F9',
  pillGlass: 'rgba(255, 255, 255, 0.22)',  // Frosted white glass pill on blue
  pillGlassText: '#FFFFFF',
  
  // Typography
  textOnGradient: '#FFFFFF',
  textOnGradientMuted: 'rgba(255, 255, 255, 0.85)',
  text: '#111417',                // Deep dark text on white sheets
  textSecondary: '#646B73',       // Subdued gray
  textMuted: '#949BA2',
  
  // Action Buttons
  btnPrimary: '#111417',          // Solid black CTA button
  btnPrimaryText: '#FFFFFF',
  btnGlass: 'rgba(255, 255, 255, 0.24)',
  btnGlassText: '#FFFFFF',
  
  // Accents
  accentBlue: '#0075EB',
  accentGreen: '#00C853',
  accentPurple: '#7B61FF',
  accentPink: '#FF3366',
  accentOrange: '#FF9500',
  
  // Borders
  border: '#ECEEF2',
  borderGlass: 'rgba(255, 255, 255, 0.28)',
  
  white: '#FFFFFF',
  shadowColor: '#002B75',
} as const;

export type Colors = typeof colors;
