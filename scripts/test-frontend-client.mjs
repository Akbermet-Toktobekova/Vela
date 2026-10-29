import assert from 'node:assert/strict';
import { createVelaClient, VelaApiError } from '../contracts/frontend-client.mjs';

const calls = [];
let fail = false;
const client = createVelaClient({ baseUrl: 'http://127.0.0.1:54321', token: 'synthetic-client-token-0001', fetchImpl: async (url, options) => {
  calls.push({ url, ...options });
  if (fail) { fail = false; throw new TypeError('Synthetic lost response'); }
  return { ok: true, json: async () => ({ revision: 3 }) };
} });
const payload = { revision: 2, id: 'step-40', amount: 4000 };
const action = client.reserve(payload);
payload.amount = 9999;
fail = true;
await assert.rejects(action.send(), TypeError);
await action.send();
assert.equal(calls[0].headers['Idempotency-Key'], calls[1].headers['Idempotency-Key']);
assert.equal(calls[0].body, calls[1].body);
assert.equal(JSON.parse(calls[0].body).amount, 4000);
assert.equal(calls[0].url, 'http://127.0.0.1:54321/v2/planning/steps');
assert.equal(calls[0].headers.Authorization, 'Bearer synthetic-client-token-0001');
assert.notEqual(client.reserve({ revision: 3, id: 'next', amount: 100 }).key, action.key);
await client.bootstrap();
assert.equal(calls.at(-1).method, 'GET');
assert.equal(calls.at(-1).headers['Idempotency-Key'], undefined);
await client.preview({ amount: 4000 });
assert.equal(calls.at(-1).headers['Idempotency-Key'], undefined);
await client.complete('step/with space', { revision: 3 }).send();
assert.ok(calls.at(-1).url.endsWith('/steps/step%2Fwith%20space/complete'));
assert.throws(() => client.transactions({ offset: -1 }));
assert.throws(() => createVelaClient({ baseUrl: 'https://user:secret@example.org', token: 'synthetic-client-token-0001' }));
const stale = createVelaClient({ baseUrl: 'http://127.0.0.1:54321', token: 'synthetic-client-token-0001', fetchImpl: async () => ({ ok: false, status: 409, json: async () => ({ detail: 'Refresh and review.' }) }) });
await assert.rejects(stale.resume({ revision: 0 }).send(), error => error instanceof VelaApiError && error.status === 409 && error.message === 'Refresh and review.');
const unreadable = createVelaClient({ baseUrl: 'http://127.0.0.1:54321', token: 'synthetic-client-token-0001', fetchImpl: async () => ({ ok: false, status: 503, json: async () => { throw new SyntaxError('HTML response'); } }) });
await assert.rejects(unreadable.bootstrap(), error => error instanceof VelaApiError && error.status === 503 && !error.message.includes('HTML'));
console.log('Frontend client: retry identity, immutable payload, paths, preview, auth, conflict and non-JSON error checks PASS.');
