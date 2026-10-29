import { useColorScheme } from 'react-native';

// Semantic pilot palette; shared geometry follows docs/design-system.md.
export const light = {
  background: '#F7F9F8', surface: '#FFFFFF', text: '#17251E', muted: '#52635A',
  accent: '#246344', accentText: '#FFFFFF', soft: '#EAF3ED', border: '#D9E2DC',
  attention: '#FFF1D9', attentionText: '#7A4E16', inverse: '#F7F9F8',
  positive: '#236647', negative: '#9C2B2B',
};
export type Palette = typeof light;
export const dark: Palette = {
  background: '#121C17', surface: '#1C2A22', text: '#EDF5EF', muted: '#B1C4B8',
  accent: '#8FD5AC', accentText: '#10271B', soft: '#243D2E', border: '#536B5C',
  attention: '#44351D', attentionText: '#F5D298', inverse: '#121C17',
  positive: '#7CD1A8', negative: '#F09090',
};
export const space = { xs: 4, sm: 8, md: 16, gutter: 16, lg: 16, xl: 24, xxl: 32 };
export const touchTarget = 48;
export const radius = { sm: 8, button: 12, card: 16 };
export const type = { small: 14, body: 16, title: 20, hero: 28, money: 32 };
export function usePalette(): Palette { return useColorScheme() === 'dark' ? dark : light; }
