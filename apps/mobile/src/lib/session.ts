/** Supabase email-OTP sessions. Transport/storage injection keeps provider calls testable. */
export type SessionErrorCode = 'invalid_code' | 'expired_code' | 'rate_limited' | 'unavailable' | 'signed_out';
export class SessionError extends Error {
  constructor(public readonly code: SessionErrorCode, public readonly retryAfterSeconds?: number) {
    super({ invalid_code: 'Check the code and try again.', expired_code: 'That code expired. Request a new code.',
      rate_limited: 'Please wait before trying again.', unavailable: 'Sign-in is temporarily unavailable. Try again.',
      signed_out: 'Sign in again to continue.' }[code]);
    this.name = 'SessionError';
  }
}
export interface RefreshStorage { read(): Promise<string | null>; write(token: string): Promise<void>; clear(): Promise<void> }
export interface SessionConfig { authUrl: string; publicKey: string }
interface Session { accessToken: string; refreshToken: string; expiresAt: number }
type Dependencies = { fetch?: typeof fetch; now?: () => number; storage?: RefreshStorage; timeoutMs?: number };

function anonKey(key: string): boolean {
  if (/^sb_publishable_[A-Za-z0-9_-]+$/.test(key)) return true;
  // Legacy anon JWTs remain public configuration. Never accept service-role/secret keys.
  try {
    const payload = key.split('.')[1];
    if (!payload) return false;
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    let bits = 0, value = 0, decoded = '';
    for (const char of payload.replace(/-/g, '+').replace(/_/g, '/').replace(/=+$/, '')) {
      const index = chars.indexOf(char);
      if (index < 0) return false;
      value = (value << 6) | index; bits += 6;
      if (bits >= 8) { bits -= 8; decoded += String.fromCharCode((value >> bits) & 255); }
    }
    return JSON.parse(decoded).role === 'anon' && key.split('.').length === 3;
  } catch { return false; }
}
export function validateSessionConfig(config: SessionConfig): SessionConfig {
  const url = new URL(config.authUrl);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !/^\/auth\/v1\/?$/.test(url.pathname) || !anonKey(config.publicKey)) {
    throw new Error('Use a trusted HTTPS Supabase Auth URL and public publishable key.');
  }
  return { authUrl: url.href.replace(/\/$/, ''), publicKey: config.publicKey };
}

export function createSessionClient(input: SessionConfig, dependencies: Dependencies = {}) {
  const config = validateSessionConfig(input);
  const transport = dependencies.fetch ?? ((...args) => fetch(...args));
  const now = dependencies.now ?? Date.now;
  let session: Session | null = null;
  let generation = 0;
  let refreshing: Promise<string> | null = null;
  let storageQueue: Promise<void> = Promise.resolve();
  function stored(work: () => Promise<void>) {
    const result = storageQueue.then(work, work);
    storageQueue = result.catch(() => {});
    return result;
  }
  async function clear(expected: number) {
    if (generation !== expected) return;
    session = null;
    await stored(async () => { if (generation === expected) await dependencies.storage?.clear(); });
  }
  async function provider(path: string, body?: unknown, accessToken?: string): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), dependencies.timeoutMs ?? 15000);
    try {
      const response = await transport(`${config.authUrl}${path}`, {
        method: 'POST', signal: controller.signal, redirect: 'error',
        headers: { apikey: config.publicKey, 'Content-Type': 'application/json',
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const data = response.status === 204 ? null : await response.json().catch(() => null);
      if (!response.ok) {
        const code = data && typeof data === 'object' && 'code' in data ? data.code : null;
        const retry = response.headers.get('Retry-After');
        const seconds = retry && /^\d+$/.test(retry) && Number.isSafeInteger(Number(retry)) ? Number(retry) : undefined;
        throw new SessionError(response.status === 429 ? 'rate_limited' : code === 'otp_expired' ? 'expired_code' :
          response.status >= 500 ? 'unavailable' : 'invalid_code', seconds);
      }
      return data;
    } catch (error) {
      if (error instanceof SessionError) throw error;
      throw new SessionError('unavailable');
    } finally { clearTimeout(timeout); }
  }
  async function accept(data: unknown, expected: number): Promise<string> {
    if (!data || typeof data !== 'object') throw new SessionError('unavailable');
    const value = data as Record<string, unknown>;
    if (typeof value.access_token !== 'string' || !value.access_token || typeof value.refresh_token !== 'string' ||
        !value.refresh_token || value.token_type !== 'bearer' || typeof value.expires_in !== 'number' ||
        !Number.isSafeInteger(value.expires_in) || value.expires_in <= 0 ||
        !Number.isSafeInteger(now() + value.expires_in * 1000)) throw new SessionError('unavailable');
    if (generation !== expected) throw new SessionError('signed_out');
    const next = { accessToken: value.access_token, refreshToken: value.refresh_token, expiresAt: now() + value.expires_in * 1000 };
    await stored(async () => { if (generation === expected) await dependencies.storage?.write(next.refreshToken); });
    if (generation !== expected) throw new SessionError('signed_out');
    session = next;
    return next.accessToken;
  }
  async function refresh(rejectedToken?: string): Promise<string> {
    if (rejectedToken && session && session.accessToken !== rejectedToken) return session.accessToken;
    if (refreshing) return refreshing;
    const expected = generation;
    const token = session?.refreshToken;
    if (!token) throw new SessionError('signed_out');
    const operation = (async () => {
      try { return await accept(await provider('/token?grant_type=refresh_token', { refresh_token: token }), expected); }
      catch (error) { await clear(expected); throw error; }
    })();
    refreshing = operation;
    try { return await operation; } finally { if (refreshing === operation) refreshing = null; }
  }
  return {
    async requestCode(email: string) {
      if (!email.trim() || !email.includes('@')) throw new SessionError('invalid_code');
      await provider('/otp', { email: email.trim(), create_user: true });
    },
    async verifyCode(email: string, code: string) {
      const expected = ++generation;
      session = null;
      refreshing = null;
      await stored(() => dependencies.storage?.clear() ?? Promise.resolve());
      try { await accept(await provider('/verify', { email: email.trim(), token: code.trim(), type: 'email' }), expected); }
      catch (error) { await clear(expected); throw error; }
    },
    async restore() {
      if (!dependencies.storage) return false;
      const expected = ++generation;
      session = null;
      refreshing = null;
      await storageQueue;
      const token = await dependencies.storage.read();
      if (generation !== expected) throw new SessionError('signed_out');
      if (!token) return false;
      session = { accessToken: '', refreshToken: token, expiresAt: 0 };
      await refresh();
      return true;
    },
    async accessToken() {
      if (!session) throw new SessionError('signed_out');
      return session.expiresAt <= now() ? refresh() : session.accessToken;
    },
    refresh,
    async signOut(): Promise<{ remoteSignedOut: boolean }> {
      const accessToken = session?.accessToken;
      const expected = ++generation;
      session = null;
      refreshing = null;
      await clear(expected);
      if (!accessToken) return { remoteSignedOut: false };
      try { await provider('/logout?scope=local', undefined, accessToken); return { remoteSignedOut: true }; }
      catch { return { remoteSignedOut: false }; }
    },
    /** API401 can refresh once; callers reuse their already-serialized command. */
    async fetch(send: (token: string) => Promise<Response>) {
      const expected = generation;
      const access = await this.accessToken();
      let response = await send(access);
      if (generation !== expected) throw new SessionError('signed_out');
      if (response.status === 401) {
        response = await send(await refresh(access));
        if (generation !== expected) throw new SessionError('signed_out');
        if (response.status === 401) { await clear(expected); throw new SessionError('signed_out'); }
      }
      return response;
    },
  };
}
export type SessionClient = ReturnType<typeof createSessionClient>;
