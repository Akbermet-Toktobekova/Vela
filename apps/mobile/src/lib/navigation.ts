import type { Href } from 'expo-router';

// Only local app screens can be resumed after entering connection credentials.
export function connectionDestination(value: string | string[] | undefined): Href {
  if (typeof value !== 'string') return '/personal';
  const screens = ['/', '/personal', '/plan', '/assistant', '/settings', '/snapshot', '/import', '/adjust', '/debts', '/learn', '/observations', '/shared-plan', '/shared-assistant'];
  return screens.includes(value) || /^\/learn\/[a-zA-Z0-9_-]+$/.test(value) ? value as Href : '/personal';
}

export function connectionRedirect(path: string) {
  return {pathname: '/connect' as const, params: {returnTo: path}};
}
