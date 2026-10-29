/** Framework-independent local API client. Keep token in memory, never in bundles or URLs. */
export class VelaApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'Check the form fields and try again.');
    this.name = 'VelaApiError';
    this.status = status;
  }
}

export function createVelaClient({ baseUrl, token, fetchImpl = globalThis.fetch }) {
  const url = new URL(baseUrl);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('Use an HTTP(S) API origin without credentials or a path.');
  }
  if (typeof token !== 'string' || token.length < 24) throw new Error('Enter the local connection token.');
  const base = url.origin;
  async function request(method, path, body, key, signal) {
    const response = await fetchImpl(base + path, {
      method, signal, cache: 'no-store',
      headers: { Authorization: `Bearer ${token}`, ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(key ? { 'Idempotency-Key': key } : {}) },
      ...(body !== undefined ? { body } : {}),
    });
    let value;
    try { value = await response.json(); }
    catch {
      // Preserve the status for frontend error states when a proxy/server sends HTML.
      throw new VelaApiError(response.status, response.ok
        ? 'The server response could not be read. Refresh your data.'
        : 'The server could not complete this request. Try again.');
    }
    if (!response.ok) throw new VelaApiError(response.status, value?.detail);
    return value;
  }
  function command(method, path, payload) {
    // Prepare ONCE per confirmed user action. Retry this object after a lost response.
    // Capturing JSON prevents edited form values from changing an in-flight retry.
    const body = JSON.stringify(payload);
    const key = globalThis.crypto.randomUUID();
    return Object.freeze({ key, send: ({ signal } = {}) => request(method, path, body, key, signal) });
  }
  const id = encodeURIComponent;
  return Object.freeze({
    /** @returns {Promise<import('../apps/mobile/src/lib/generated').FrontendView>} */
    bootstrap: () => request('GET', '/v2/frontend'),
    assistant: () => request('GET', '/v2/assistant/context'),
    personal: () => request('GET', '/v2/personal'),
    planning: () => request('GET', '/v2/planning'),
    profile: body => command('PUT', '/v2/profile', body),
    addAccount: body => command('POST', '/v2/accounts', body),
    replaceBalance: (accountId, body) => command('PUT', `/v2/accounts/${id(accountId)}/balance`, body),
    addIncome: body => command('POST', '/v2/income', body),
    configurePlan: body => command('PUT', '/v2/planning', body),
    adoptLegacy: body => command('POST', '/v2/planning/adopt-legacy', body),
    preview: body => request('POST', '/v2/planning/preview', JSON.stringify(body)),
    reserve: body => command('POST', '/v2/planning/steps', body),
    complete: (stepId, body) => command('POST', `/v2/planning/steps/${id(stepId)}/complete`, body),
    cancel: (stepId, body) => command('POST', `/v2/planning/steps/${id(stepId)}/cancel`, body),
    defer: body => command('POST', '/v2/planning/defer', body),
    resume: body => command('POST', '/v2/planning/resume', body),
    addBill: body => command('POST', '/v2/planning/bills', body),
    payBill: (billId, body) => command('POST', `/v2/planning/bills/${id(billId)}/pay`, body),
    cancelBill: (billId, body) => command('POST', `/v2/planning/bills/${id(billId)}/cancel`, body),
    previewImport: body => request('POST', '/v1/imports/base64', JSON.stringify(body)),
    importPreview: previewId => request('GET', `/v1/imports/${id(previewId)}`),
    applyImport: (previewId, body) => command('POST', `/v2/imports/${id(previewId)}/apply`, body),
    transactions: ({ offset = 0, limit = 50 } = {}) => {
      if (!Number.isInteger(offset) || offset < 0 || !Number.isInteger(limit) || limit < 1 || limit > 200) throw new Error('Invalid history page.');
      return request('GET', `/v1/transactions?offset=${offset}&limit=${limit}`);
    },
    observations: () => request('GET', '/v2/observations'),
    lessons: () => request('GET', '/v1/lessons'),
    lesson: lessonId => request('GET', `/v1/lessons/${id(lessonId)}`),
    lessonProgress: (lessonId, body) => command('POST', `/v1/lessons/${id(lessonId)}/progress`, body),
    exportData: () => request('GET', '/v1/export'),
    eraseData: () => request('DELETE', '/v1/data'),
  });
}
