'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const { createSourceLoader } = require('./helpers/source_loader');
const source = [
  '// function target() { return "comment decoy"; }',
  '/*',
  'function target() { return "block comment decoy"; }',
  '*/',
  'const text = `',
  'function target() { return "template decoy"; }',
  '// SAMPLE_START',
  '// SAMPLE_END',
  '`;',
  'function outer() {',
  ' function target() { return "nested decoy"; }',
  '}',
  '  async function target\n(\n value = { nested: "}" }\n) {',
  ' const braces = /[{}]/g, escaped = /\\/}/, division = 12 / 3;',
  ' const quoted = "} ; {", single = \'}\\\' {\'; // }',
  ' /* } */ const template = `} ${(() => ({ value: `${value.nested}` }))().value} {`;',
  ' return { template, division, matches: "{}".match(braces), escaped: escaped.test("/}") };',
  '}',
  'const fields\n = [";", { text: `; ${"}"}` }];',
  'function after() { throw Error("must not execute"); }',
  ' // SAMPLE_START — description is allowed',
  'const sectionValue = "kept";',
  ' // SAMPLE_END'
].join('\r\n');
const loader = createSourceLoader(source);
assert.ok(loader.fn('target').startsWith('async function target'));
assert.ok(!loader.fn('target').includes('function after'));
assert.ok(loader.fn('target').includes('/* } */'));
const context = vm.createContext({});
vm.runInContext(`${loader.functions(['target', 'after'])}\nglobalThis.target = target;`, context);
async function run() {
  const result = await context.target();
  assert.equal(result.division, 4);
  assert.equal(result.template, '} } {');
  assert.deepEqual(Array.from(result.matches), ['{', '}']);
  assert.equal(result.escaped, true);
  const sameLine = createSourceLoader('const before=1; function one() { return 1; } function two$() { return 2; }');
  assert.equal(sameLine.fn('one'), 'function one() { return 1; }');
  assert.equal(sameLine.fn('two$'), 'function two$() { return 2; }');
  assert.equal(createSourceLoader('function* values() { yield /}/; }').fn('values'), 'function* values() { yield /}/; }');
  vm.runInContext(loader.declaration('const', 'fields') + '\nglobalThis.fields = fields;', context);
  assert.equal(context.fields[1].text, '; }');
  assert.ok(loader.between('const', 'fields', 'function', 'after').includes('const fields'));
  assert.ok(loader.section('SAMPLE').includes('sectionValue'));
  assert.throws(() => loader.fn('absent'), /found 0/);
  assert.throws(() => loader.fn('bad-name'), /Invalid declaration/);
  assert.throws(() => loader.between('function', 'after', 'function', 'outer'), /Reversed/);
  assert.throws(() => loader.section('ABSENT'), /START\/END/);
  assert.throws(() => createSourceLoader('function broken() {').fn('broken'), /No complete/);
  assert.throws(() => createSourceLoader('function duplicate() {}\nfunction duplicate() {}').fn('duplicate'), /found 2/);
  assert.throws(() => createSourceLoader('// A_END\n// A_START').section('A'), /START\/END/);
  assert.throws(() => createSourceLoader('// A_START\n// A_START\n// A_END').section('A'), /START\/END/);
  assert.throws(() => createSourceLoader('// A_START\nconst unfinished =\n// A_END').section('A'), /START\/END/);
  console.log('PASS: source loader handles multiline declarations, defaults, comments, strings, nested templates, regex/division, decoys and missing/duplicate boundaries without executing source.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
