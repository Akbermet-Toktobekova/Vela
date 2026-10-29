const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('../../node_modules/typescript');
function load(file, mocks = {}, extra = {}) {
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports, require: name => {
    if (name in mocks) return mocks[name];
    throw Error('Unexpected import ' + name);
  }, URL, Date, Error, AbortController, setTimeout, clearTimeout, ...extra });
  return module.exports;
}
const { createSessionClient, SessionError, validateSessionConfig } = load('session.ts');
const config = { authUrl: 'https://synthetic.supabase.co/auth/v1', publicKey: 'sb_publishable_synthetic' };
const session = (token = 'access1', refresh = 'refresh1', seconds = 3600) => ({ access_token: token, refresh_token: refresh, token_type: 'bearer', expires_in: seconds });
const response = (data, status = 200, headers) => new Response(status === 204 ? null : JSON.stringify(data), { status, headers });
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
function harness(handler, options = {}) {
  const calls = [];
  const saved = { token: null, writes: [], clears: 0 };
  const storage = { read: async () => saved.token, write: async t => { saved.token = t; saved.writes.push(t); }, clear: async () => { saved.token = null; saved.clears++; } };
  const client = createSessionClient(config, { fetch: async (url, init) => { calls.push({ url, ...init }); return handler(url, init, calls.length); }, storage, ...options });
  return { client, calls, saved };
}
test('trusted public config rejects cleartext, credential URLs and secret/service-role keys', () => {
  for (const patch of [{ authUrl: 'http://synthetic/auth/v1' }, { authUrl: config.authUrl + '?key=secret' }, { authUrl: 'https://user:pass@synthetic/auth/v1' }, { publicKey: 'sb_secret_test' },
    { publicKey: `a.${Buffer.from(JSON.stringify({ role: 'service_role' })).toString('base64url')}.c` }]) assert.throws(() => validateSessionConfig({ ...config, ...patch }));
  assert.equal(validateSessionConfig({ ...config, publicKey: `a.${Buffer.from(JSON.stringify({ role: 'anon' })).toString('base64url')}.c` }).authUrl, config.authUrl);
});
test('OTP request/verification use provider endpoints without leaking response payload or storing access token', async () => {
  const h = harness(url => response(url.endsWith('/otp') ? {} : session()));
  await h.client.requestCode(' user@example.test ');
  await h.client.verifyCode('user@example.test', ' 123456 ');
  assert.equal(h.calls[0].url, config.authUrl + '/otp');
  assert.deepEqual(JSON.parse(h.calls[0].body), { email: 'user@example.test', create_user: true });
  assert.deepEqual(JSON.parse(h.calls[1].body), { email: 'user@example.test', token: '123456', type: 'email' });
  assert.equal(h.calls[1].headers.apikey, config.publicKey);
  assert.equal(h.calls[1].redirect, 'error');
  assert.equal(await h.client.accessToken(), 'access1');
  assert.deepEqual(h.saved.writes, ['refresh1']);
});
test('provider errors map invalid/expired/rate/unavailable without echoing raw details', async () => {
  for (const [status, data, expected] of [[400, { code: 'invalid_credentials', message: 'PRIVATE' }, 'invalid_code'], [403, { code: 'otp_expired' }, 'expired_code'], [429, {}, 'rate_limited'], [503, {}, 'unavailable']]) {
    const h = harness(() => response(data, status, { 'Retry-After': '12' }));
    await assert.rejects(h.client.verifyCode('u@example.test', '123'), error => error.code === expected && !error.message.includes('PRIVATE') && (status !== 429 || error.retryAfterSeconds === 12));
    assert.equal(h.saved.token, null);
  }
  const h = harness(() => { throw Error('PRIVATE network payload'); });
  await assert.rejects(h.client.requestCode('u@example.test'), { code: 'unavailable' });
});
test('expired access tokens share exactly one refresh and persist rotated refresh credential', async () => {
  let clock = 1000;
  const gate = deferred();
  const h = harness(async url => url.endsWith('/verify') ? response(session('old', 'r1', 1)) : (await gate.promise, response(session('fresh', 'r2'))), { now: () => clock });
  await h.client.verifyCode('u@example.test', '123'); clock = 2000;
  const requests = Array.from({ length: 8 }, () => h.client.accessToken());
  await new Promise(r => setImmediate(r));
  assert.equal(h.calls.length, 2);
  assert.equal(h.calls[1].url, config.authUrl + '/token?grant_type=refresh_token');
  assert.deepEqual(JSON.parse(h.calls[1].body), { refresh_token: 'r1' });
  gate.resolve();
  assert.deepEqual(await Promise.all(requests), Array(8).fill('fresh'));
  assert.equal(h.saved.token, 'r2');
});
test('401 refresh retries once, concurrent stale401 reuses already rotated token, 409 never refreshes', async () => {
  const h = harness(url => response(url.endsWith('/verify') ? session('old') : session('new')));
  await h.client.verifyCode('u@example.test', '123');
  const late = deferred(); let call = 0;
  const first = h.client.fetch(async token => { call++; return response({}, token === 'old' ? 401 : 200); });
  const second = h.client.fetch(async token => { if (token === 'old') { await late.promise; return response({}, 401); } return response({}, 200); });
  assert.equal((await first).status, 200); late.resolve(); assert.equal((await second).status, 200);
  assert.equal(h.calls.length, 2);
  assert.equal(call, 2);
  assert.equal((await h.client.fetch(async () => response({}, 409))).status, 409);
  assert.equal(h.calls.length, 2);
});
test('failed refresh and repeated401 clear credentials and require sign-in', async () => {
  for (const failure of ['refresh', '401']) {
    const h = harness(url => response(url.endsWith('/verify') ? session() : failure === 'refresh' ? { code: 'refresh_token_not_found' } : session('new'), url.endsWith('/verify') || failure !== 'refresh' ? 200 : 400));
    await h.client.verifyCode('u@example.test', '123');
    let count = 0;
    await assert.rejects(h.client.fetch(async () => { count++; return response({}, 401); }));
    assert.equal(count, failure === 'refresh' ? 1 : 2);
    assert.equal(h.saved.token, null);
    await assert.rejects(h.client.accessToken(), { code: 'signed_out' });
  }
});
test('native restore uses only refresh credential, web adapter has no persistence', async () => {
  const h = harness(() => response(session('restored', 'rotated')));
  h.saved.token = 'previous-device-refresh';
  assert.equal(await h.client.restore(), true);
  assert.deepEqual(JSON.parse(h.calls[0].body), { refresh_token: 'previous-device-refresh' });
  assert.equal(await h.client.accessToken(), 'restored');
  const web = createSessionClient(config, { fetch: async () => response(session()) });
  assert.equal(await web.restore(), false);
});
test('logout clears locally before remote failure and stale refresh cannot resurrect session', async () => {
  const gate = deferred();
  const h = harness(async url => url.endsWith('/verify') ? response(session()) : url.includes('/logout') ? response({}, 503) : (await gate.promise, response(session('resurrected'))));
  await h.client.verifyCode('u@example.test', '123');
  const refreshing = h.client.refresh();
  const rejection = assert.rejects(refreshing, { code: 'signed_out' });
  assert.equal((await h.client.signOut()).remoteSignedOut, false);
  assert.equal(h.saved.token, null);
  gate.resolve(); await rejection;
  await assert.rejects(h.client.accessToken(), { code: 'signed_out' });
  assert.equal(h.saved.token, null);
  const logout = h.calls.find(c => c.url.includes('/logout'));
  assert.equal(logout.url, config.authUrl + '/logout?scope=local');
  assert.equal(logout.headers.Authorization, 'Bearer access1');
});
test('malformed successful session response fails closed', async () => {
  for (const data of [{}, { ...session(), expires_in: -1 }, { ...session(), token_type: 'other' }]) {
    const h = harness(() => response(data));
    await assert.rejects(h.client.verifyCode('u@example.test', '123'), { code: 'unavailable' });
    await assert.rejects(h.client.accessToken(), { code: 'signed_out' });
  }
});
function apiHarness(os = 'web') {
  const records = [], store = new Map();
  let handler = async () => response({ revision: 0 });
  const fetchMock = async (url, init) => { records.push({ url, ...init }); return handler(url, init); };
  const sessionModule = load('session.ts', {}, { fetch: fetchMock });
  const api = load('api.ts', { './session': sessionModule, 'react-native': { Platform: { OS: os } }, 'expo-secure-store': {
    getItemAsync: async key => store.get(key) ?? null, setItemAsync: async (key, value) => { store.set(key, value); }, deleteItemAsync: async key => { store.delete(key); },
  } }, { fetch: fetchMock, FormData, Blob });
  return { api, records, store, handler: fn => { handler = fn; } };
}
test('API financial401 retry retains exact serialized body/key,409 is surfaced without retry', async () => {
  const h = apiHarness(); let writes = 0;
  h.handler(async (url, init) => url.endsWith('/verify') ? response(session('old')) : url.includes('/token?') ? response(session('new')) : response({ revision: 8 }, ++writes === 1 ? 401 : 200));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  await h.api.verifySignInCode('u@example.test', '123');
  const command = { revision: 7, amount: 4000 };
  assert.equal((await h.api.request('/v2/planning/steps', 'POST', command, 'same-command')).revision, 8);
  const actual = h.records.filter(r => r.url.includes('/v2/'));
  assert.equal(actual.length, 2);
  assert.equal(actual[0].body, actual[1].body);
  assert.equal(actual[0].headers['Idempotency-Key'], 'same-command');
  assert.equal(actual[1].headers['Idempotency-Key'], 'same-command');
  assert.equal(actual[0].headers.Authorization, 'Bearer old');
  assert.equal(actual[1].headers.Authorization, 'Bearer new');
  h.handler(() => response({ detail: 'Refresh changed information.' }, 409));
  await assert.rejects(h.api.request('/v2/planning/steps', 'POST', command, 'same-command'), /Refresh changed information/);
  assert.equal(h.records.filter(r => r.url.includes('/v2/')).length, 3);
});
test('web upload uses current token, retries same FormData and never stores credentials', async () => {
  const h = apiHarness(); let uploads = 0;
  h.handler((url) => url.endsWith('/verify') ? response(session('old')) : url.includes('/token?') ? response(session('new')) : response({ id: 'preview' }, ++uploads === 1 ? 401 : 200));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  await h.api.verifySignInCode('u@example.test', '123');
  await h.api.uploadStatement({ uri: 'blob:synthetic', name: 'synthetic.csv', file: new Blob(['synthetic']) });
  const actual = h.records.filter(r => r.url.endsWith('/v1/imports'));
  assert.equal(actual.length, 2);
  assert.equal(actual[0].body, actual[1].body);
  assert.equal(actual[1].headers.Authorization, 'Bearer new');
  assert.equal(h.store.size, 0);
});
test('native adapter scopes refresh storage to configured deployment and uses base64 upload', async () => {
  const h = apiHarness('android');
  h.handler(url => response(url.endsWith('/verify') || url.includes('/token?') ? session() : { id: 'native-preview' }));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  await h.api.verifySignInCode('u@example.test', '123');
  const stored = JSON.parse(h.store.get('vela-cloud-refresh'));
  assert.equal(stored.refreshToken, 'refresh1'); assert.equal(stored.access_token, undefined);
  await h.api.uploadStatement({ uri: 'unused', name: 'synthetic.csv', base64: 'c3ludGhldGlj' });
  assert.equal(h.records.at(-1).url, 'https://api.example.test/v1/imports/base64');
  assert.equal(h.records.at(-1).headers.Authorization, 'Bearer access1');
  await h.api.disconnect(); assert.equal(h.store.size, 0);
});
test('local connection/restore remain compatible and cloud mode blocks URL credential leaks', async () => {
  const h = apiHarness('android');
  await h.api.connect({ url: 'http://127.0.0.1:55199/', token: ' local-synthetic ' });
  assert.equal(h.records[0].headers.Authorization, 'Bearer local-synthetic');
  assert.equal(await h.api.restoreConnection(), true);
  await h.api.disconnect(); assert.equal(await h.api.restoreConnection(), false);
  await assert.rejects(h.api.configureCloudSession({ ...config, apiUrl: 'http://api.example.test' }));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  await assert.rejects(h.api.request('//evil.example.test/path'));
  await assert.rejects(h.api.request('/\\evil.example.test/path'));
});


test('signout during an API request prevents its old-account response from being returned', async () => {
  const gate = deferred();
  const h = harness(url => response(url.endsWith('/logout?scope=local') ? null : session(), url.endsWith('/logout?scope=local') ? 204 : 200));
  await h.client.verifyCode('u@example.test', '123');
  const pending = h.client.fetch(async () => { await gate.promise; return response({ private: 'previous-owner' }); });
  const rejected = assert.rejects(pending, { code: 'signed_out' });
  await h.client.signOut(); gate.resolve(); await rejected;
});
test('trusted provider timeout reports unavailable without raw network error', async () => {
  const client = createSessionClient(config, { timeoutMs: 5, fetch: async (_url, init) => new Promise((_resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(Error('PRIVATE timeout detail')), { once: true });
  }) });
  await assert.rejects(client.requestCode('u@example.test'), error => error.code === 'unavailable' && !error.message.includes('PRIVATE'));
});
test('API503 does not refresh or duplicate command', async () => {
  const h = apiHarness();
  h.handler(url => url.endsWith('/verify') ? response(session()) : response({ detail: 'Temporarily unavailable.' }, 503));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  await h.api.verifySignInCode('u@example.test', '123');
  await assert.rejects(h.api.request('/v2/planning/steps', 'POST', { amount: 4000 }, 'same-command'), /Temporarily unavailable/);
  assert.equal(h.records.length, 2);
});
test('native restore rejects a refresh credential belonging to another deployment', async () => {
  const h = apiHarness('ios');
  h.store.set('vela-cloud-refresh', JSON.stringify({ authUrl: config.authUrl, apiUrl: 'https://other.example.test', refreshToken: 'foreign-refresh' }));
  await h.api.configureCloudSession({ ...config, apiUrl: 'https://api.example.test' });
  assert.equal(await h.api.restoreCloudSession(), false);
  assert.equal(h.records.length, 0);
  assert.equal(h.store.size, 0);
});
