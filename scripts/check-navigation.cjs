// Connection return targets must stay inside explicitly supported local screens.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('../apps/mobile/node_modules/typescript');
const file = path.join(__dirname, '../apps/mobile/src/lib/navigation.ts');
const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
}).outputText;
const moduleValue = {exports: {}};
vm.runInNewContext(code, {exports: moduleValue.exports, module: moduleValue});
const {connectionDestination, connectionRedirect} = moduleValue.exports;
const allowed = ['/', '/personal', '/plan', '/assistant', '/settings', '/snapshot', '/import', '/adjust', '/debts', '/learn', '/learn/buffer-basics'];
for (const target of allowed) assert.equal(connectionDestination(target), target);
const denied = [undefined, [], ['/plan', '/settings'], 'https://example.com', '//example.com', 'javascript:alert(1)', '/\\example.com', '/plan?token=secret', '/plan#fragment', '/learn/../settings', '/learn/%2e%2e', '/connect', '/pilot', '/_sitemap', '/unknown'];
for (const target of denied) assert.equal(connectionDestination(target), '/personal');
assert.equal(connectionRedirect('/plan').pathname, '/connect');
assert.equal(connectionRedirect('/plan').params.returnTo, '/plan');
console.log(`${allowed.length} allowed routes and ${denied.length} unsafe/unsupported targets PASS; redirect preserves requested screen`);
