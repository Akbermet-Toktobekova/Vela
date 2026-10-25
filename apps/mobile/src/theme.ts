import { useColorScheme } from 'react-native';

// Warm editorial palette, tightened for mobile density.
export const light = {
  background: '#FAF8F5', surface: '#FFFFFF', text: '#29231F', muted: '#6D6259',
  accent: '#9C4628', accentText: '#FFFFFF', soft: '#F6E8DC', border: '#E6DED5',
  attention: '#FFF1D9', attentionText: '#7A4E16', inverse: '#FAF8F5',
  positive: '#236647', negative: '#9C2B2B',
};
export type Palette = typeof light;
export const dark: Palette = {
  background: '#201A17', surface: '#2D2520', text: '#FAF0E8', muted: '#CCBBB0',
  accent: '#E8A086', accentText: '#29150E', soft: '#443027', border: '#625046',
  attention: '#44351D', attentionText: '#F5D298', inverse: '#201A17',
  positive: '#7CD1A8', negative: '#F09090',
};
export const space = { xs: 4, sm: 6, md: 12, gutter: 16, lg: 16, xl: 24, xxl: 32 };
export const radius = { sm: 8, button: 12, card: 16 };
export const type = { small: 12, body: 14, title: 17, hero: 22, money: 28 };
export function usePalette(): Palette { return useColorScheme() === 'dark' ? dark : light; }
