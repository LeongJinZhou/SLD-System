'use strict';
// Run from the repository root: node tests/helpers/check_formatted_source.js
// Feed a reformatted app to each suite via stdin/read mocks; never write web files.
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');
const { createSourceLoader } = require('./source_loader');
let source = fs.readFileSync('web/app.js', 'utf8');
const loader = createSourceLoader(source);
let formatted = 0;
const names = new Set([...source.matchAll(/\bfunction\s+([A-Za-z_$][\w$]*)\s*\(/g)].map(match => match[1]));
for (const name of names) {
  let declaration;
  try { declaration = loader.fn(name); }
  catch (error) {
    // Nested named callbacks are not independently loadable top-level functions.
    if (/found 0$/.test(error.message)) continue;
    throw error;
  }
  source = source.replace(declaration, declaration.replace(/function\s+([A-Za-z_$][\w$]*)\s*\(/, 'function\n  $1\n('));
  formatted++;
}
source = source.replace(/\b(const|let) (clubEditVersion|reportEditableFields|recoveryClubFields|recoveryProposalFields)=/g, '$1\n $2\n =');
const bootstrap = `
  const fs=require('node:fs'),path=require('node:path');
  const read=fs.readFileSync,app=path.resolve('web/app.js'),source=read(0,'utf8');
  fs.readFileSync=function(file,...args){
    if(typeof file==='string'&&path.resolve(file)===app)
      return args[0]==='utf8'?source:Buffer.from(source);
    return read.call(this,file,...args);
  };
  require(path.resolve(process.argv[1]));
`;
const suites = fs.readdirSync('tests').filter(file => /^test_.*\.js$/.test(file));
let failed = 0;
for (const file of suites) {
  const result = spawnSync(process.execPath, ['-e', bootstrap, 'tests/' + file], { encoding: 'utf8', input: source, timeout: 30000 });
  console.log(`${file}: exit ${result.status}`);
  if (result.status !== 0) {
    failed++;
    console.error(result.error?.message || '', result.stdout || '', result.stderr || '');
  }
}
console.log(`IN-MEMORY FORMATTED FUNCTIONS ${formatted}; SUITES ${suites.length}; FAILED ${failed}; NO FILE WRITES`);
process.exitCode = failed ? 1 : 0;
