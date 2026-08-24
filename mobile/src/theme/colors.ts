export const colors = {
  background: '#FFFFFF',
  surface: '#F4F5F7',
  surfaceSecondary: '#FFFFFF',
  border: '#E9EAEF',
  text: '#191C1F',
  textSecondary: '#72777A',
  textMuted: '#9DA2A6',
  primary: '#191C1F',
  accentBlue: '#0075EB',
  accentGreen: '#00C853',
  accentPurple: '#7B61FF',
  accentPink: '#FF3366',
  pillBg: '#F0F2F5',
  danger: '#E53935',
  white: '#FFFFFF',
} as const;

export type Colors = typeof colors;
