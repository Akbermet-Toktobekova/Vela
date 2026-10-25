// Offline syntax validation only; does not claim SDK compatibility or type checking.
const fs = require('node:fs');
const path = require('node:path');
const ts = require('../.local/typescript/lib/typescript.js');
let count = 0;
let failed = false;
function walk(directory) {
  for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (/\.tsx?$/.test(file)) {
      const source = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
      for (const diagnostic of source.parseDiagnostics) {
        failed = true;
        console.error(file, ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
      }
      count++;
    }
  }
}
walk(path.join(__dirname, '../apps/mobile/src'));
console.log(`${count} TypeScript source files parsed; ${failed ? 'FAIL' : 'PASS'} (syntax only).`);
process.exitCode = failed ? 1 : 0;
